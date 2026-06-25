"""
src/utils/performance.py
========================
Monitor de latencia para el pipeline — Entregable 1.

Responsabilidad: medir el tiempo de cada paso e identificar
el cuello de botella.
"""

import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PipelineTimer:
    """
    Cronómetro para pipelines de datos.

    Mide el tiempo de cada paso, calcula throughput (filas/segundo)
    e identifica el cuello de botella automáticamente.

    Example:
        >>> timer = PipelineTimer('mi_pipeline')
        >>> timer.iniciar()
        >>> # ... operación costosa ...
        >>> timer.marcar('carga', n_registros=len(df))
        >>> timer.reporte()
    """

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        self.inicio = None
        self.marcas = {}
        self.ultimo = None

    def iniciar(self) -> None:
        """Inicia el cronómetro."""
        self.inicio = datetime.now()
        self.ultimo = time.perf_counter()
        logger.info(f'[{self.nombre}] Iniciado: {self.inicio.strftime("%H:%M:%S")}')

    def marcar(self, nombre_paso: str, n_registros: int = 0) -> float:
        """
        Registra el tiempo del paso que terminó.

        Args:
            nombre_paso (str): Etiqueta del paso.
            n_registros (int): Filas procesadas (para throughput).

        Returns:
            float: Duración en segundos.
        """
        ahora = time.perf_counter()
        dur   = ahora - self.ultimo
        tp    = int(n_registros / dur) if dur > 0 else 0
        self.marcas[nombre_paso] = {
            'duracion':    round(dur, 4),
            'n_registros': n_registros,
            'throughput':  tp,
        }
        self.ultimo = ahora
        logger.info(f'  [{nombre_paso}]: {dur:.3f}s | {tp:,} filas/s')
        return dur

    def reporte(self) -> dict:
        """
        Imprime el reporte de latencia con barras visuales.

        Returns:
            dict con pasos, total_seg, cuello_botella.
        """
        if not self.marcas:
            return {}

        total  = sum(m['duracion'] for m in self.marcas.values())
        cuello = max(self.marcas, key=lambda k: self.marcas[k]['duracion'])

        print(f'\n{"="*55}')
        print(f'REPORTE DE LATENCIA — {self.nombre}')
        print(f'{"="*55}')
        for paso, d in self.marcas.items():
            pct  = d['duracion'] / total * 100
            bar  = '█' * int(pct / 4)
            flag = ' ← CUELLO' if paso == cuello else ''
            print(f'  {paso:<22} {bar:<25} {d["duracion"]:.3f}s ({pct:.0f}%){flag}')
        print(f'{"─"*55}')
        print(f'  TOTAL: {total:.3f}s')
        fin = datetime.now()
        print(f'  Inicio: {self.inicio.strftime("%H:%M:%S")} | Fin: {fin.strftime("%H:%M:%S")}')
        print(f'{"="*55}\n')

        logger.info(f'[{self.nombre}] Total: {total:.3f}s | Cuello: {cuello}')
        return {'pasos': self.marcas, 'total_seg': round(total, 3), 'cuello_botella': cuello}