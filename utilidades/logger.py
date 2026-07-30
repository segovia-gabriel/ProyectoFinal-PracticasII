import logging
from pathlib import Path

RUTA_LOG = Path(__file__).resolve().parent.parent / "logs" / "app.log"

_logger = logging.getLogger("restaurante")


def _configurar():
    # Sin este corte, cada llamada engancharia un FileHandler nuevo y me
    # terminaria guardando las lineas duplicadas.
    if _logger.handlers:
        return

    RUTA_LOG.parent.mkdir(exist_ok=True)
    manejador = logging.FileHandler(RUTA_LOG, encoding="utf-8")
    formato = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    manejador.setFormatter(formato)
    _logger.addHandler(manejador)
    _logger.setLevel(logging.DEBUG)


def registrar(mensaje, nivel="info"):
    # El unico punto de logging de la app: registrar(error, "error").
    _configurar()
    getattr(_logger, nivel, _logger.debug)(mensaje)
