"""
Script de verificacion de entorno - Practicas II
No es parte del sistema final, es solo para confirmar que Python, las
librerias y la conexion a MySQL funcionan antes de empezar a programar.

Se corre una vez por maquina (Mac y Windows), despues de:
1. Instalar Python y crear el entorno virtual.
2. pip install -r requirements.txt
3. Copiar config.ini.example a config.ini y completar la password real.
4. Ejecutar analisis/schema.sql en MySQL Workbench.

Uso: python verificar_entorno.py
"""

import sys
from configparser import ConfigParser
from pathlib import Path

# --- Paso 1: version de Python ---
print(f"Python: {sys.version.split()[0]}")
if sys.version_info < (3, 8):
    print("ATENCION: se necesita Python 3.8 o superior.")

# --- Paso 2: que las librerias esten instaladas ---
try:
    import PyQt5.QtCore
    print(f"PyQt5: OK (Qt {PyQt5.QtCore.QT_VERSION_STR})")
except ImportError:
    print("FALTA: PyQt5. Correr: pip install -r requirements.txt")
    sys.exit(1)

try:
    import mysql.connector
    print(f"mysql-connector-python: OK ({mysql.connector.__version__})")
except ImportError:
    print("FALTA: mysql-connector-python. Correr: pip install -r requirements.txt")
    sys.exit(1)

try:
    import bcrypt
    print("bcrypt: OK")
except ImportError:
    print("FALTA: bcrypt. Correr: pip install -r requirements.txt")
    sys.exit(1)

# --- Paso 3: leer config.ini ---
ruta_config = Path(__file__).resolve().parent / "config.ini"
if not ruta_config.exists():
    print(f"FALTA: {ruta_config.name}. Copiar config.ini.example a config.ini y completar la password.")
    sys.exit(1)

parser = ConfigParser()
parser.read(ruta_config)
if not parser.has_section("mysql"):
    print("config.ini no tiene la seccion [mysql]. Revisar contra config.ini.example.")
    sys.exit(1)

db_config = dict(parser.items("mysql"))

# --- Paso 4: conectar a MySQL y chequear que schema.sql ya se ejecuto ---
try:
    conexion = mysql.connector.connect(
        host=db_config["host"],
        port=int(db_config["port"]),
        database=db_config["database"],
        user=db_config["user"],
        password=db_config["password"],
    )
    cursor = conexion.cursor()

    tablas_esperadas = [
        "usuarios", "historial_acciones", "clientes", "grupos_mesa", "mesas",
        "grupos_menu", "menu_items", "historial_precios_menu", "reservas",
        "consumos", "consumo_detalle",
    ]

    print(f"\nConexion a MySQL OK -> base '{db_config['database']}'")
    print("-" * 50)
    for tabla in tablas_esperadas:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            cantidad = cursor.fetchone()[0]
            print(f"  {tabla:<25} {cantidad} filas")
        except mysql.connector.Error:
            print(f"  {tabla:<25} NO EXISTE (falta correr analisis/schema.sql)")

    cursor.close()
    conexion.close()
    print("-" * 50)
    print("Entorno verificado correctamente.")

except mysql.connector.Error as error:
    print(f"\nERROR de conexion a MySQL: {error}")
    print("Revisar que MySQL este corriendo y que host/user/password/port en config.ini sean correctos.")
    sys.exit(1)
