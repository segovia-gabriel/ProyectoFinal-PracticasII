"""
Acceso a datos de consumos y su detalle. Un consumo por reserva (la columna
reserva_id es UNIQUE). Al crear el consumo se guardan los precios ya resueltos
(snapshot en precio_unitario_aplicado) para que el historial de ventas no cambie
si despues se modifica el precio del item.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def listar():
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT co.id, co.fecha, co.medio_pago, co.precio_total, "
            "c.nombre AS cliente_nombre, c.apellido AS cliente_apellido, "
            "m.codigo AS mesa_codigo, r.fecha AS reserva_fecha "
            "FROM consumos co "
            "JOIN reservas r ON r.id = co.reserva_id "
            "JOIN clientes c ON c.id = r.cliente_id "
            "JOIN mesas m ON m.id = r.mesa_id "
            "ORDER BY co.fecha DESC"
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def reservas_sin_consumo():
    # Reservas que todavia no tienen un consumo cargado (para el combo de alta).
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT r.id, r.fecha, c.nombre, c.apellido, m.codigo AS mesa_codigo "
            "FROM reservas r "
            "JOIN clientes c ON c.id = r.cliente_id "
            "JOIN mesas m ON m.id = r.mesa_id "
            "LEFT JOIN consumos co ON co.reserva_id = r.id "
            "WHERE co.id IS NULL "
            "ORDER BY r.fecha DESC"
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_detalle(consumo_id):
    # Items de un consumo, con el nombre del item, para la vista de detalle.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT mi.nombre, cd.cantidad, cd.precio_unitario_aplicado "
            "FROM consumo_detalle cd JOIN menu_items mi ON mi.id = cd.menu_item_id "
            "WHERE cd.consumo_id = %s",
            (consumo_id,),
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def crear_consumo(reserva_id, medio_pago, precio_total, detalles):
    # Inserta el consumo y sus detalles en una sola transaccion. 'detalles' es
    # una lista de tuplas (menu_item_id, cantidad, precio_unitario_aplicado)
    # con el precio ya resuelto por el controlador.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO consumos (reserva_id, medio_pago, precio_total) VALUES (%s, %s, %s)",
            (reserva_id, medio_pago, precio_total),
        )
        consumo_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO consumo_detalle (consumo_id, menu_item_id, cantidad, precio_unitario_aplicado) "
            "VALUES (%s, %s, %s, %s)",
            [(consumo_id, item_id, cantidad, precio) for (item_id, cantidad, precio) in detalles],
        )
        conexion.commit()
        return consumo_id
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
