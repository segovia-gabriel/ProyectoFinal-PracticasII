"""
Acceso a datos de historial_precios_menu. Cada cambio de precio crea una fila
nueva (fecha_inicio = hoy, fecha_fin = NULL) y cierra la anterior poniendo su
fecha_fin al dia anterior. El precio vigente es el que arranco y todavia no
cerro. Nunca se editan filas viejas: asi el historial queda intacto.
"""

from datetime import timedelta

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def obtener_vigente(item_id):
    # Precio del dia: fecha_inicio <= hoy y (fecha_fin NULL o fecha_fin >= hoy).
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, precio_lista, precio_especial, medio_pago_especial, "
            "fecha_inicio, fecha_fin FROM historial_precios_menu "
            "WHERE menu_item_id = %s AND fecha_inicio <= CURDATE() "
            "AND (fecha_fin IS NULL OR fecha_fin >= CURDATE()) "
            "ORDER BY fecha_inicio DESC LIMIT 1",
            (item_id,),
        )
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def listar_historial(item_id):
    # Todo el historial ordenado del mas viejo al mas nuevo, para calcular la
    # variacion porcentual entre cambios en Python.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, precio_lista, precio_especial, medio_pago_especial, "
            "fecha_inicio, fecha_fin FROM historial_precios_menu "
            "WHERE menu_item_id = %s ORDER BY fecha_inicio ASC",
            (item_id,),
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar(item_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM historial_precios_menu WHERE menu_item_id = %s", (item_id,))
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def crear_precio(item_id, precio_lista, precio_especial, medio_pago_especial,
                 fecha_inicio, fecha_fin=None):
    # Cierra el precio abierto y crea el nuevo, todo en la misma transaccion para
    # que no quede el item con dos precios abiertos o con ninguno. fecha_fin puede
    # venir con una fecha (vigencia acotada) o None (vigente indefinidamente).
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        # cerrar el precio vigente (fecha_fin NULL) al dia anterior al nuevo
        fecha_cierre = fecha_inicio - timedelta(days=1)
        cursor.execute(
            "UPDATE historial_precios_menu SET fecha_fin = %s "
            "WHERE menu_item_id = %s AND fecha_fin IS NULL",
            (fecha_cierre, item_id),
        )
        cursor.execute(
            "INSERT INTO historial_precios_menu "
            "(menu_item_id, precio_lista, precio_especial, medio_pago_especial, fecha_inicio, fecha_fin) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (item_id, precio_lista, precio_especial, medio_pago_especial, fecha_inicio, fecha_fin),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def eliminar_por_item(item_id):
    # Se usa al borrar un item de menu: primero hay que sacar su historial de
    # precios por la clave foranea.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM historial_precios_menu WHERE menu_item_id = %s", (item_id,))
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
