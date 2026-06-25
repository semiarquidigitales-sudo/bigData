"""
main.py
=======
Punto de entrada del Pipeline ETL — Entregable 1.

Ejecutar con:
    python main.py

El pipeline corre completamente solo. Genera outputs en output/
y registra eventos en logs/pipeline.log.
"""

import logging
import json
import sys
import os
from pathlib import Path

from src.etl.cargador      import DataLoader
from src.etl.limpiador     import DataCleaner
from src.utils.performance import PipelineTimer


def configurar_logging() -> None:
    """Configura logging hacia archivo y consola."""
    Path('logs').mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  %(name)-28s  %(levelname)-8s  %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler('logs/pipeline.log', encoding='utf-8', mode='a'),
            logging.StreamHandler(sys.stdout),
        ]
    )


def ejecutar_pipeline(
    ruta_datos: str     = 'datos/crudos/ventas_colombia_2022_2024.csv',
    carpeta_salida: str = 'output/',
) -> dict:
    """
    Ejecuta el pipeline ETL completo de forma autónoma.

    Args:
        ruta_datos (str):     Ruta al dataset crudo.
        carpeta_salida (str): Carpeta de outputs.

    Returns:
        dict con métricas de ejecución.
    """
    logger = logging.getLogger('pipeline.main')
    Path(carpeta_salida).mkdir(parents=True, exist_ok=True)

    logger.info('='*60)
    logger.info('PIPELINE ETL — ENTREGABLE 1 — INICIANDO')
    logger.info('='*60)

    timer   = PipelineTimer('entregable_1')
    reporte = {'exitoso': False, 'errores': []}
    timer.iniciar()

    # PASO 1: CARGAR
    logger.info('─── PASO 1: CARGA ───')
    loader   = DataLoader(ruta_datos, nombre_proyecto='mi_proyecto')
    df_crudo = loader.cargar()

    if df_crudo is None:
        logger.error('PIPELINE DETENIDO — no se pudo cargar el dataset')
        reporte['errores'].append('Carga fallida')
        return reporte

    timer.marcar('carga_datos', n_registros=len(df_crudo))

    # PASO 2: DIAGNOSTICAR
    logger.info('─── PASO 2: DIAGNÓSTICO ───')
    metricas = loader.diagnosticar(df_crudo)
    reporte['metricas_calidad'] = metricas
    timer.marcar('diagnostico')

    print('\n📊 VISTA PREVIA (5 filas):')
    print(df_crudo.head().to_string())
    print('\n📋 TIPOS DE DATO:')
    print(df_crudo.dtypes.to_string())

    # PASO 3: LIMPIAR
    logger.info('─── PASO 3: LIMPIEZA ───')
    cleaner             = DataCleaner(nombre_proyecto='mi_proyecto')
    df_limpio, rep_limp = cleaner.limpiar(
        df_crudo, estrategia_nulos='mediana', optimizar_ram=True)
    reporte['metricas_limpieza'] = rep_limp
    timer.marcar('limpieza', n_registros=len(df_limpio))
    cleaner.validar(df_limpio)

    # PASO 4: GUARDAR
    logger.info('─── PASO 4: GUARDAR ───')
    ruta_csv = os.path.join(carpeta_salida, 'dataset_limpio.csv')
    df_limpio.to_csv(ruta_csv, index=False)
    logger.info(f'CSV guardado: {ruta_csv}')

    try:
        ruta_parquet = os.path.join(carpeta_salida, 'dataset_limpio.parquet')
        df_limpio.to_parquet(ruta_parquet, index=False)
        logger.info(f'Parquet guardado: {ruta_parquet}')
    except Exception as e:
        logger.warning(f'Parquet no disponible: {e}')

    timer.marcar('guardar')

    # PASO 5: REPORTE
    met_render = timer.reporte()
    reporte['exitoso']              = True
    reporte['metricas_rendimiento'] = met_render

    ruta_json = os.path.join(carpeta_salida, 'reporte_ejecucion.json')
    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False, default=str)

    print('\n' + '='*60)
    print('✅ PIPELINE ETL COMPLETADO')
    print('='*60)
    print(f'  Filas entrada:    {rep_limp["filas_entrada"]:,}')
    print(f'  Filas limpias:    {rep_limp["filas_salida"]:,}')
    print(f'  Nulos resueltos:  {rep_limp["nulos_resueltos"]:,}')
    print(f'  RAM reducida:     {rep_limp["pct_reduccion_ram"]}%')
    print(f'  Latencia total:   {met_render.get("total_seg", "?")}s')
    print(f'  Outputs en:       {carpeta_salida}')
    print(f'  Log en:           logs/pipeline.log')
    print('='*60)
    logger.info('PIPELINE COMPLETADO EXITOSAMENTE')
    return reporte


if __name__ == '__main__':
    configurar_logging()
    resultado = ejecutar_pipeline(
        # ── CAMBIA ESTA RUTA AL ARCHIVO REAL QUE DESCARGASTE ──────
        ruta_datos     = 'datos/crudos/ventas_colombia_2022_2024.csv',
        carpeta_salida = 'output/',
    )
    sys.exit(0 if resultado['exitoso'] else 1)