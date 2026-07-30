
from configparser import ConfigParser
from pathlib import Path

from mysql.connector import MySQLConnection

RUTA_CONFIG = Path(__file__).resolve().parent.parent / "config.ini"


def config_db(seccion="mysql"):
    parser = ConfigParser()
    parser.read(RUTA_CONFIG)

    if not parser.has_section(seccion):
        raise Exception(f"No se encontro la seccion [{seccion}] en {RUTA_CONFIG.name}")

    datos = dict(parser.items(seccion))
    # El puerto viene como texto del .ini y MySQLConnection lo necesita entero.
    if "port" in datos:
        datos["port"] = int(datos["port"])
    return datos


def abrir_conexion():
    # Devuelvo la conexion y no un cursor, asi cada funcion del modelo decide
    # como leer los resultados y la cierra en su propio try/finally.
    return MySQLConnection(**config_db())
