"""
src/etl/limpiador.py
====================
Responsabilidad única: limpiar un DataFrame crudo y optimizar
sus tipos de dato para reducir el uso de RAM.
"""

import time
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def optimizar_memoria(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Reduce RAM eligiendo tipos de dato más pequeños.

    Estrategias:
      - int64/int32 → int8/int16/int32 según el rango real.
      - float64     → float32.
      - object con < 50% únicos → category.

    Args:
        df (pd.DataFrame): DataFrame a optimizar.
        verbose (bool):    Si True, registra el resultado.

    Returns:
        pd.DataFrame: Copia optimizada.
    """
    df_opt    = df.copy()
    mb_antes  = df_opt.memory_usage(deep=True).sum() / 1024**2

    for col in df_opt.columns:
        tipo = df_opt[col].dtype
        if tipo in ['int64', 'int32']:
            cmin, cmax = df_opt[col].min(), df_opt[col].max()
            if   cmin >= -128   and cmax <= 127:   df_opt[col] = df_opt[col].astype('int8')
            elif cmin >= -32768 and cmax <= 32767:  df_opt[col] = df_opt[col].astype('int16')
            elif tipo == 'int64':                   df_opt[col] = df_opt[col].astype('int32')
        elif tipo == 'float64':
            df_opt[col] = df_opt[col].astype('float32')
        elif tipo == 'object':
            if df_opt[col].nunique() / len(df_opt) < 0.50:
                df_opt[col] = df_opt[col].astype('category')

    mb_despues = df_opt.memory_usage(deep=True).sum() / 1024**2
    reduccion  = (1 - mb_despues / mb_antes) * 100
    if verbose:
        logger.info(f'RAM: {mb_antes:.1f} MB → {mb_despues:.1f} MB (−{reduccion:.0f}%)')
    return df_opt


class DataCleaner:
    """
    Limpia y optimiza un DataFrame crudo.

    Tres pasos: eliminar duplicados, imputar nulos, castear tipos.

    Example:
        >>> cleaner = DataCleaner()
        >>> df_limpio, reporte = cleaner.limpiar(df_crudo)
        >>> print(reporte['pct_reduccion_ram'])
    """

    def __init__(self, nombre_proyecto: str = 'proyecto') -> None:
        self.nombre_proyecto = nombre_proyecto
        self.logger = logging.getLogger(f'{nombre_proyecto}.cleaner')
        self.logger.info('DataCleaner inicializado')

    def limpiar(
        self,
        df: pd.DataFrame,
        estrategia_nulos: str = 'mediana',
        optimizar_ram: bool   = True,
    ) -> tuple:
        """
        Limpia el DataFrame en tres pasos.

        Args:
            df (pd.DataFrame):      DataFrame crudo.
            estrategia_nulos (str): 'mediana', 'media' o 'eliminar'.
            optimizar_ram (bool):   Si True, aplica casteo de tipos.

        Returns:
            tuple: (df_limpio, reporte_metricas)
        """
        self.logger.info('=== LIMPIEZA INICIADA ===')
        t0          = time.time()
        df_out      = df.copy()
        filas_ini   = len(df_out)
        n_resueltos = 0

        # PASO 1: Eliminar duplicados exactos
        n_dup  = df_out.duplicated().sum()
        df_out = df_out.drop_duplicates()
        self.logger.info(f'Paso 1 — Duplicados: {n_dup:,} eliminados')

        # PASO 2: Imputar nulos según el tipo de columna
        for col in df_out.columns:
            n_nulos = df_out[col].isna().sum()
            if n_nulos == 0:
                continue

            es_numerica = pd.api.types.is_numeric_dtype(df_out[col].dtype)

            if not es_numerica:
                # Categórico: valor neutral que no sesga el análisis
                df_out[col] = df_out[col].fillna('Sin Datos')
                self.logger.info(f'  {col}: {n_nulos:,} nulos → "Sin Datos"')

            elif estrategia_nulos == 'eliminar':
                df_out = df_out.dropna(subset=[col])
                self.logger.info(f'  {col}: filas con nulos eliminadas')

            elif estrategia_nulos == 'media':
                v = df_out[col].mean()
                df_out[col] = df_out[col].fillna(v)
                self.logger.info(f'  {col}: {n_nulos:,} nulos → media {v:.2f}')

            else:  # mediana — más robusta a outliers (default)
                v = df_out[col].median()
                df_out[col] = df_out[col].fillna(v)
                self.logger.info(f'  {col}: {n_nulos:,} nulos → mediana {v:.2f}')

            n_resueltos += n_nulos

        self.logger.info(f'Paso 2 — Nulos resueltos: {n_resueltos:,}')

        # PASO 3: Optimizar tipos de dato
        mb_antes = df_out.memory_usage(deep=True).sum() / 1024**2
        if optimizar_ram:
            df_out = optimizar_memoria(df_out, verbose=True)
        mb_despues = df_out.memory_usage(deep=True).sum() / 1024**2

        duracion = time.time() - t0
        reporte  = {
            'filas_entrada':     filas_ini,
            'filas_salida':      len(df_out),
            'filas_eliminadas':  filas_ini - len(df_out),
            'nulos_resueltos':   n_resueltos,
            'ram_antes_mb':      round(mb_antes, 2),
            'ram_despues_mb':    round(mb_despues, 2),
            'pct_reduccion_ram': round((1 - mb_despues / mb_antes) * 100, 1),
            'latencia_seg':      round(duracion, 3),
        }

        self.logger.info(
            f'=== LIMPIEZA COMPLETADA: {len(df_out):,} filas | '
            f'RAM −{reporte["pct_reduccion_ram"]}% | {duracion:.3f}s ==='
        )
        return df_out, reporte

    def validar(self, df: pd.DataFrame) -> bool:
        """Verifica que no hay nulos ni duplicados."""
        nulos = df.isna().sum().sum()
        dup   = df.duplicated().sum()
        ok    = (nulos == 0) and (dup == 0)
        msg   = '✅ limpio' if ok else f'⚠️  nulos={nulos} dup={dup}'
        (self.logger.info if ok else self.logger.warning)(f'Validación: {msg}')
        return ok