import logging
from pythonjsonlogger import jsonlogger

def log(mensaje,nivel="info"):
    logger = logging.getLogger(__name__)

    fileHandler= logging.FileHandler("error\\app.log")

    formatoJson = jsonlogger.JsonFormatter(
        "%(name)s %(asctime)s %(levelname)s %(filename)s %(lineno)s %(message)s", 
        rename_fields= {"levelname":"severity","asctime": "timestamp"},
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
    fileHandler.setFormatter(formatoJson)
    logger.addHandler(fileHandler)
    logger.setLevel(logging.DEBUG)

    # niveles={
    #     'debug':debug,
    #     'info':info,
    #     'warning':warning,
    #     'error':error,
    #     'critical':critical 
    # }

    if nivel=="info":
        logger.info(mensaje)
    elif nivel=="debug":
        logger.debug(mensaje)
    elif nivel == "warning":
        logger.warning(mensaje)
    elif nivel == "error":
        logger.error(mensaje)
    elif nivel == "critical":
        logger.critical(mensaje)
    else:
        logger.debug("Nivel no definido")

