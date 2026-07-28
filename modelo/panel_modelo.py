"""
Consultas del panel principal (solo lectura). Son los numeros y listas que se
muestran apenas se inicia sesion, para que la pantalla de inicio sirva de resumen
del dia en vez de estar vacia. No duplica las de estadisticas_modelo: aca van las
que miran "hoy" y "este mes", alla las que arman los informes por periodo.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def contar_reservas_hoy():
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM reservas WHERE fecha = CURDATE()")
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar_reservas_futuras():
    # Estrictamente posteriores a hoy: las de hoy se cuentan aparte.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM reservas WHERE fecha > CURDATE()")
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def reservas_de_hoy():
    # Agenda del dia, ordenada por hora, para la tabla del panel.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT r.id, r.hora_inicio, r.hora_fin, r.estado_asistencia, "
            "c.nombre AS cliente_nombre, c.apellido AS cliente_apellido, "
            "m.codigo AS mesa_codigo "
            "FROM reservas r "
            "JOIN clientes c ON c.id = r.cliente_id "
            "JOIN mesas m ON m.id = r.mesa_id "
            "WHERE r.fecha = CURDATE() "
            "ORDER BY r.hora_inicio"
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def ingresos_del_mes():
    # COALESCE para que devuelva 0 y no None cuando todavia no hubo consumos.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(precio_total), 0) FROM consumos "
            "WHERE estado = 'cerrada' "
            "AND YEAR(fecha) = YEAR(CURDATE()) AND MONTH(fecha) = MONTH(CURDATE())"
        )
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def total_clientes():
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM clientes")
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def precios_por_vencer(dias):
    # Items cuyo precio vigente vence dentro de los proximos 'dias' dias. Es el
    # mismo aviso de renovacion que muestra el modulo Menu, pero adelantado al
    # panel para que se vea al entrar sin tener que buscar item por item.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT mi.id AS item_id, mi.nombre AS item, h.fecha_fin, "
            "DATEDIFF(h.fecha_fin, CURDATE()) AS dias "
            "FROM historial_precios_menu h "
            "JOIN menu_items mi ON mi.id = h.menu_item_id "
            "WHERE h.fecha_fin IS NOT NULL "
            "AND h.fecha_inicio <= CURDATE() AND h.fecha_fin >= CURDATE() "
            "AND DATEDIFF(h.fecha_fin, CURDATE()) <= %s "
            "ORDER BY h.fecha_fin",
            (dias,),
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def reservas_cumplidas_sin_consumo():
    # Reservas ya cumplidas (el cliente asistio o llego tarde) a las que todavia
    # no se les cargo el consumo: es trabajo pendiente para el usuario. Es la
    # misma condicion que usa el combo de Nuevo consumo, incluidas las de hoy,
    # para que lo que el panel marca como pendiente sea exactamente lo que se
    # puede cargar.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT r.id, r.fecha, c.nombre AS cliente_nombre, c.apellido AS cliente_apellido, "
            "m.codigo AS mesa_codigo "
            "FROM reservas r "
            "JOIN clientes c ON c.id = r.cliente_id "
            "JOIN mesas m ON m.id = r.mesa_id "
            "LEFT JOIN consumos co ON co.reserva_id = r.id "
            "WHERE co.id IS NULL AND r.fecha <= CURDATE() "
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
