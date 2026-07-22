"""
Acceso a la base MySQL. Adaptado de sistema_ejemplo/python_mysql_config.py.
Centraliza la lectura de config.ini y la apertura de la conexion para que
ningun otro archivo tenga que saber donde estan las credenciales.
"""

from configparser import ConfigParser
from pathlib import Path

from mysql.connector import MySQLConnection

# Ruta absoluta al config.ini de la raiz del proyecto, sin depender del
# directorio desde el que se ejecute (regla dura: siempre pathlib, nunca "/").
RUTA_CONFIG = Path(__file__).resolve().parent.parent / "config.ini"


def config_db(seccion="mysql"):
    # Lee las credenciales de MySQL desde config.ini y las devuelve como dict
    # listo para pasarle a MySQLConnection(**config).
    parser = ConfigParser()
    parser.read(RUTA_CONFIG)

    if not parser.has_section(seccion):
        raise Exception(f"No se encontro la seccion [{seccion}] en {RUTA_CONFIG.name}")

    datos = dict(parser.items(seccion))
    # el puerto viene como texto del .ini y MySQLConnection lo necesita entero
    if "port" in datos:
        datos["port"] = int(datos["port"])
    return datos


def abrir_conexion():
    # Punto unico de conexion: cada funcion del modelo la abre, la usa y la
    # cierra en su propio try/finally. Devolver la conexion (no un cursor)
    # deja que el modelo decida como leer los resultados.
    return MySQLConnection(**config_db())
