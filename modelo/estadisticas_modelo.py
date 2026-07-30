

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


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


def top_clientes(limite=5):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT c.nombre, c.apellido, COUNT(*) AS cantidad "
            "FROM reservas r JOIN clientes c ON c.id = r.cliente_id "
            "GROUP BY r.cliente_id ORDER BY cantidad DESC LIMIT %s",
            (limite,),
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def reservas_actuales_y_futuras():
    # Las devuelvo separadas (actuales = las de hoy, futuras = de manana en
    # adelante); la pantalla muestra las dos y el total.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT "
            "SUM(CASE WHEN fecha = CURDATE() THEN 1 ELSE 0 END) AS actuales, "
            "SUM(CASE WHEN fecha > CURDATE() THEN 1 ELSE 0 END) AS futuras "
            "FROM reservas"
        )
        fila = cursor.fetchone()
        # SUM devuelve NULL si la tabla esta vacia, asi que lo paso a 0.
        return {
            "actuales": int(fila["actuales"] or 0),
            "futuras": int(fila["futuras"] or 0),
        }
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def reservas_por_mes():
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT YEAR(fecha) AS anio, MONTH(fecha) AS mes, COUNT(*) AS cantidad "
            "FROM reservas GROUP BY YEAR(fecha), MONTH(fecha) "
            "ORDER BY anio, mes"
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def ingresos_por_dia_semana(anio, mes):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT DAYNAME(c.fecha) AS dia, SUM(c.precio_total) AS ingreso "
            "FROM consumos c "
            "WHERE c.estado = 'cerrada' AND YEAR(c.fecha) = %s AND MONTH(c.fecha) = %s "
            "GROUP BY dia",
            (anio, mes),
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def items_por_dia_semana(anio, mes):
    # La cantidad consumida de cada item por dia de la semana; el top 5 de cada dia
    # lo arma el controlador en Python.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT DAYNAME(c.fecha) AS dia, mi.nombre AS item, SUM(cd.cantidad) AS total "
            "FROM consumo_detalle cd "
            "JOIN consumos c ON c.id = cd.consumo_id "
            "JOIN menu_items mi ON mi.id = cd.menu_item_id "
            "WHERE c.estado = 'cerrada' AND YEAR(c.fecha) = %s AND MONTH(c.fecha) = %s "
            "GROUP BY dia, mi.id ORDER BY dia, total DESC",
            (anio, mes),
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
