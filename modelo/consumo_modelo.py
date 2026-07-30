"""
Acceso a datos de consumos y su detalle. Un consumo por reserva (reserva_id es
UNIQUE). Arranca 'abierta' (la mesa esta en curso y le podes agregar o editar
items) y pasa a 'cerrada' cuando se cierra la cuenta. Los precios los guardo ya
resueltos (una foto en precio_unitario_aplicado) para que el historial de ventas
no se mueva si despues cambio el precio del item.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def listar(filtro_nombre=None, fecha_desde=None, fecha_hasta=None):
    # Filtros del listado: por nombre (del cliente o el codigo de mesa) y por el
    # rango de fechas del consumo.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = (
            "SELECT co.id, co.reserva_id, co.fecha, co.medio_pago, co.precio_total, co.estado, "
            "c.nombre AS cliente_nombre, c.apellido AS cliente_apellido, "
            "m.codigo AS mesa_codigo, r.fecha AS reserva_fecha "
            "FROM consumos co "
            "JOIN reservas r ON r.id = co.reserva_id "
            "JOIN clientes c ON c.id = r.cliente_id "
            "JOIN mesas m ON m.id = r.mesa_id "
            "WHERE 1 = 1"
        )
        parametros = []
        if filtro_nombre:
            sql += " AND (c.nombre LIKE %s OR c.apellido LIKE %s OR m.codigo LIKE %s)"
            patron = f"%{filtro_nombre}%"
            parametros += [patron, patron, patron]
        if fecha_desde:
            sql += " AND DATE(co.fecha) >= %s"
            parametros.append(fecha_desde)
        if fecha_hasta:
            sql += " AND DATE(co.fecha) <= %s"
            parametros.append(fecha_hasta)
        sql += " ORDER BY co.fecha DESC"
        cursor.execute(sql, tuple(parametros))
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def reservas_sin_consumo():
    # Reservas a las que todavia les puedo cargar el consumo: solo consume el
    # cliente que asistio, asi que entran las que ya pasaron y donde estuvo
    # (asistio o llego tarde). Quedan afuera las futuras, las de hoy que siguen en
    # espera y las que el cliente falto.
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
            "AND r.fecha <= CURDATE() "
            "AND r.consumo_vencido = 0 "
            "AND r.estado_asistencia IN ('asistio', 'tardanza') "
            "ORDER BY r.fecha DESC"
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_por_reserva(reserva_id):
    # Devuelve el consumo de una reserva (con su estado) o None si no tiene. Me
    # sirve para saber si la mesa ya esta abierta y para precargar el dialogo cuando edito.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, reserva_id, medio_pago, precio_total, estado "
            "FROM consumos WHERE reserva_id = %s",
            (reserva_id,),
        )
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_detalle(consumo_id):
    # Los items de un consumo, con el nombre de cada uno, para la vista de detalle.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT cd.menu_item_id, mi.nombre, cd.cantidad, cd.precio_unitario_aplicado "
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


def crear_consumo(reserva_id, medio_pago, precio_total, detalles, estado="abierta"):
    # Mete el consumo y sus detalles en una sola transaccion. 'detalles' viene como
    # lista de tuplas (menu_item_id, cantidad, precio_unitario_aplicado) con el
    # precio ya resuelto por el controlador. Por defecto la mesa nace 'abierta'.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO consumos (reserva_id, medio_pago, precio_total, estado) "
            "VALUES (%s, %s, %s, %s)",
            (reserva_id, medio_pago, precio_total, estado),
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


def reemplazar_detalle(consumo_id, medio_pago, precio_total, detalles):
    # Reemplaza los items de un consumo abierto: borro los detalles viejos, cargo
    # los nuevos y actualizo el medio de pago y el total. Todo en una transaccion
    # para que la cuenta nunca quede a medias.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM consumo_detalle WHERE consumo_id = %s", (consumo_id,))
        cursor.executemany(
            "INSERT INTO consumo_detalle (consumo_id, menu_item_id, cantidad, precio_unitario_aplicado) "
            "VALUES (%s, %s, %s, %s)",
            [(consumo_id, item_id, cantidad, precio) for (item_id, cantidad, precio) in detalles],
        )
        cursor.execute(
            "UPDATE consumos SET medio_pago = %s, precio_total = %s WHERE id = %s",
            (medio_pago, precio_total, consumo_id),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def cerrar(consumo_id):
    # Cierra la cuenta: la mesa pasa a 'cerrada' y recien ahi cuenta como venta.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("UPDATE consumos SET estado = 'cerrada' WHERE id = %s", (consumo_id,))
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def cerrar_abiertas_con_items(fecha_limite):
    # Cierra las mesas que quedaron abiertas y tienen consumo cargado (total > 0)
    # hasta 'fecha_limite' inclusive: pasan a 'cerrada' y recien ahi cuentan como
    # venta. Devuelve cuantas cerro.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE consumos SET estado = 'cerrada' "
            "WHERE estado = 'abierta' AND precio_total > 0 AND DATE(fecha) <= %s",
            (fecha_limite,),
        )
        conexion.commit()
        return cursor.rowcount
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def eliminar_abiertas_vacias(fecha_limite):
    # Descarta las mesas abiertas sin nada cargado (total 0): se abrieron por error
    # y no son una venta. Borro primero el detalle (por la clave foranea) y despues
    # el consumo. Devuelve cuantos consumos borro.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "DELETE cd FROM consumo_detalle cd "
            "JOIN consumos co ON co.id = cd.consumo_id "
            "WHERE co.estado = 'abierta' AND co.precio_total = 0 AND DATE(co.fecha) <= %s",
            (fecha_limite,),
        )
        cursor.execute(
            "DELETE FROM consumos "
            "WHERE estado = 'abierta' AND precio_total = 0 AND DATE(fecha) <= %s",
            (fecha_limite,),
        )
        conexion.commit()
        return cursor.rowcount
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
