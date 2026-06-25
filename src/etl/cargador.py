"""
src/etl/cargador.py
===================
Responsabilidad única: leer datos desde CSV, JSON o Parquet
y retornar un DataFrame. No limpia, no transforma, no grafica.
"""

import os
import time
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Carga datos desde cualquier formato soportado.

    Detecta el formato por la extensión del archivo y registra
    todos los eventos con logging profesional.

    Formats: .csv, .json, .parquet

    Example:
        >>> loader = DataLoader('datos/crudos/dataset.csv')
        >>> df = loader.cargar()
        >>> metricas = loader.diagnosticar(df)
    """

    FORMATOS_SOPORTADOS = {'csv', 'json', 'parquet'}

    def __init__(self, ruta_archivo: str, nombre_proyecto: str = 'proyecto') -> None:
        """
        Inicializa el DataLoader.

        Args:
            ruta_archivo (str):    Ruta al archivo de datos.
            nombre_proyecto (str): Nombre para etiquetar los logs.

        Raises:
            ValueError: Si la extensión no está soportada.
        """
        self.ruta_archivo    = ruta_archivo
        self.nombre_proyecto = nombre_proyecto
        self.extension = os.path.splitext(ruta_archivo)[1].lstrip('.').lower()

        if self.extension not in self.FORMATOS_SOPORTADOS:
            raise ValueError(
                f'Formato no soportado: .{self.extension}. '
                f'Válidos: {self.FORMATOS_SOPORTADOS}'
            )
        logger.info(f'DataLoader listo | {ruta_archivo} | .{self.extension}')

    def cargar(self) -> pd.DataFrame | None:
        """
        Carga el archivo según su extensión.

        Returns:
            pd.DataFrame o None si hay error.
        """
        if not os.path.exists(self.ruta_archivo):
            logger.error(f'Archivo no encontrado: {self.ruta_archivo}')
            return None

        metodos = {
            'csv':     self._cargar_csv,
            'json':    self._cargar_json,
            'parquet': self._cargar_parquet,
        }
        return metodos[self.extension]()

    def _cargar_csv(self) -> pd.DataFrame | None:
        """Carga CSV con soporte para encodings alternativos."""
        try:
            t0 = time.time()
            df = pd.read_csv(self.ruta_archivo, low_memory=False)
            logger.info(f'{len(df):,} filas CSV en {time.time()-t0:.2f}s')
            return df
        except UnicodeDecodeError:
            logger.warning('UTF-8 falló, reintentando con latin-1...')
            try:
                df = pd.read_csv(self.ruta_archivo, low_memory=False, encoding='latin-1')
                logger.info(f'{len(df):,} filas (latin-1)')
                return df
            except Exception as e:
                logger.error(f'No se pudo leer: {e}')
                return None
        except pd.errors.EmptyDataError:
            logger.error('CSV vacío')
            return None
        except Exception as e:
            logger.error(f'Error CSV: {e}')
            return None

    def _cargar_json(self) -> pd.DataFrame | None:
        """Carga JSON."""
        try:
            t0 = time.time()
            df = pd.read_json(self.ruta_archivo)
            logger.info(f'{len(df):,} filas JSON en {time.time()-t0:.2f}s')
            return df
        except ValueError as e:
            logger.error(f'JSON malformado: {e}')
            return None
        except Exception as e:
            logger.error(f'Error JSON: {e}')
            return None

    def _cargar_parquet(self) -> pd.DataFrame | None:
        """Carga Parquet — columnar, 5-10x más rápido que CSV."""
        try:
            t0 = time.time()
            df = pd.read_parquet(self.ruta_archivo)
            mb = df.memory_usage(deep=True).sum() / 1024**2
            logger.info(f'{len(df):,} filas | {mb:.1f} MB RAM | {time.time()-t0:.3f}s')
            return df
        except Exception as e:
            logger.error(f'Error Parquet: {e}')
            return None

    def diagnosticar(self, df: pd.DataFrame) -> dict:
        """
        Audita el DataFrame: dimensiones, tipos, nulos, duplicados.

        Args:
            df: DataFrame a auditar.

        Returns:
            dict con filas, columnas, nulos_total, pct_nulos,
                 duplicados, cumple_minimo.
        """
        filas, cols = df.shape
        nulos       = int(df.isnull().sum().sum())
        dup         = int(df.duplicated().sum())
        pct         = round(nulos / (filas * cols) * 100, 2)

        logger.info(
            f'AUDITORÍA: {filas:,} filas x {cols} cols | '
            f'nulos: {nulos:,} ({pct}%) | dup: {dup:,}'
        )

        if filas < 100_000:
            logger.warning(f'{filas:,} filas — mínimo: 100.000')

        for col, n in df.isnull().sum().items():
            if n > 0:
                p = round(n / filas * 100, 1)
                nivel = 'CRÍTICO' if p > 20 else ('MODERADO' if p > 5 else 'LEVE')
                logger.warning(f'  [{nivel}] {col}: {n:,} ({p}%)')

        return {
            'filas':          filas,
            'columnas':       cols,
            'nulos_total':    nulos,
            'pct_nulos':      pct,
            'duplicados':     dup,
            'cumple_minimo':  filas >= 100_000,
        }