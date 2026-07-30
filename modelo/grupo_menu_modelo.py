"""
Acceso a datos de grupos_menu (Bebidas, Picadas, Pastas...). Solo tienen un nombre.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def listar(filtro_nombre=None):
    # El filtro por nombre lo usa la pantalla de grupos; los combos la llaman sin
    # filtro para traer todos.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = "SELECT id, nombre FROM grupos_menu"
        parametros = ()
        if filtro_nombre:
            sql += " WHERE nombre LIKE %s"
            parametros = (f"%{filtro_nombre}%",)
        sql += " ORDER BY nombre"
        cursor.execute(sql, parametros)
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
        cursor.execute("SELECT id, nombre FROM grupos_menu WHERE id = %s", (grupo_id,))
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
            cursor.execute("SELECT COUNT(*) FROM grupos_menu WHERE nombre = %s", (nombre,))
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM grupos_menu WHERE nombre = %s AND id <> %s",
                (nombre, excluir_id),
            )
        return cursor.fetchone()[0] > 0
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar_items(grupo_id):
    # Para no borrar un grupo que todavia tiene items de menu colgados.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM menu_items WHERE grupo_menu_id = %s", (grupo_id,))
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def crear(nombre):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO grupos_menu (nombre) VALUES (%s)", (nombre,))
        conexion.commit()
        return cursor.lastrowid
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def modificar(grupo_id, nombre):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("UPDATE grupos_menu SET nombre = %s WHERE id = %s", (nombre, grupo_id))
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
        cursor.execute("DELETE FROM grupos_menu WHERE id = %s", (grupo_id,))
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
