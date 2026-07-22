"""
Acceso a datos de grupos_mesa (Simple, VIP, Terraza...). El 'valor' es el precio
base de 2 horas; el de 3 horas se calcula, no se guarda otro valor.
Una funcion = una operacion SQL.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def listar():
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, valor FROM grupos_mesa ORDER BY nombre")
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_por_id(grupo_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, valor FROM grupos_mesa WHERE id = %s", (grupo_id,))
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def existe_nombre(nombre, excluir_id=None):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        if excluir_id is None:
            cursor.execute("SELECT COUNT(*) FROM grupos_mesa WHERE nombre = %s", (nombre,))
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM grupos_mesa WHERE nombre = %s AND id <> %s",
                (nombre, excluir_id),
            )
        return cursor.fetchone()[0] > 0
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar_mesas(grupo_id):
    # Se usa para no permitir borrar un grupo que todavia tiene mesas asignadas.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM mesas WHERE grupo_mesa_id = %s", (grupo_id,))
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def crear(nombre, valor):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO grupos_mesa (nombre, valor) VALUES (%s, %s)", (nombre, valor)
        )
        conexion.commit()
        return cursor.lastrowid
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def modificar(grupo_id, nombre, valor):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE grupos_mesa SET nombre = %s, valor = %s WHERE id = %s",
            (nombre, valor, grupo_id),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def eliminar(grupo_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM grupos_mesa WHERE id = %s", (grupo_id,))
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
