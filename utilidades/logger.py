"""
Logging a archivo. Basado en la idea de sistema_ejemplo/util/logger.py, pero
usando solo el modulo 'logging' estandar (sin dependencias extra a las de
requirements.txt) para que corra igual en la Mac de Gabriel y el Windows de
Mijail sin instalar nada mas.
"""

import logging
from pathlib import Path

# logs/ vive en la raiz del proyecto; se calcula desde este archivo para que
# funcione sin importar desde donde se ejecute la app (regla dura: pathlib).
RUTA_LOG = Path(__file__).resolve().parent.parent / "logs" / "app.log"

_logger = logging.getLogger("restaurante")


def _configurar():
    # Si el logger ya tiene handler no agregamos otro: sin esto, cada llamada
    # sumaria un FileHandler nuevo y la misma linea se guardaria repetida.
    if _logger.handlers:
        return

    RUTA_LOG.parent.mkdir(exist_ok=True)  # crea logs/ si no existe todavia
    manejador = logging.FileHandler(RUTA_LOG, encoding="utf-8")
    formato = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    manejador.setFormatter(formato)
    _logger.addHandler(manejador)
    _logger.setLevel(logging.DEBUG)


def registrar(mensaje, nivel="info"):
    # Punto unico de logging de la app: registrar(error, "error").
    _configurar()
    getattr(_logger, nivel, _logger.debug)(mensaje)
