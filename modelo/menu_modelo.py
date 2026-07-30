from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def listar(filtro_nombre=None):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = (
            "SELECT i.id, i.nombre, i.descripcion, i.imagen_path, i.grupo_menu_id, "
            "g.nombre AS grupo_nombre "
            "FROM menu_items i JOIN grupos_menu g ON g.id = i.grupo_menu_id"
        )
        parametros = ()
        if filtro_nombre:
            sql += " WHERE i.nombre LIKE %s"
            parametros = (f"%{filtro_nombre}%",)
        sql += " ORDER BY g.nombre, i.nombre"
        cursor.execute(sql, parametros)
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_por_id(item_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre, descripcion, imagen_path, grupo_menu_id "
            "FROM menu_items WHERE id = %s",
            (item_id,),
        )
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar_consumos(item_id):
    # Para no borrar un item que ya se consumio alguna vez (esta en consumo_detalle).
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM consumo_detalle WHERE menu_item_id = %s", (item_id,))
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def crear(nombre, descripcion, imagen_path, grupo_menu_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO menu_items (nombre, descripcion, imagen_path, grupo_menu_id) "
            "VALUES (%s, %s, %s, %s)",
            (nombre, descripcion, imagen_path, grupo_menu_id),
        )
        conexion.commit()
        return cursor.lastrowid
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def modificar(item_id, nombre, descripcion, imagen_path, grupo_menu_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE menu_items SET nombre = %s, descripcion = %s, imagen_path = %s, "
            "grupo_menu_id = %s WHERE id = %s",
            (nombre, descripcion, imagen_path, grupo_menu_id, item_id),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def eliminar(item_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM menu_items WHERE id = %s", (item_id,))
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
