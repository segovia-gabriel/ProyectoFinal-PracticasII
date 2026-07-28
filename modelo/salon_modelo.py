"""
Consulta del plano del salon: todas las mesas con la reserva que las ocupa en
un momento dado. Es solo lectura; las acciones (marcar asistencia, cargar
consumo) las hacen los modulos que ya existen.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def mesas_en(fecha, hora):
    # Devuelve TODAS las mesas (LEFT JOIN) y, si en ese dia y hora hay una
    # reserva que las ocupa, sus datos. Como no se permiten reservas
    # superpuestas en la misma mesa, a lo sumo puede coincidir una.
    # El rango es [hora_inicio, hora_fin): a la hora de fin la mesa ya se libera.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT m.id, m.numero_mesa, m.numero_sillas, m.piso, m.codigo, "
            "g.nombre AS grupo_nombre, g.valor AS grupo_valor, "
            "r.id AS reserva_id, r.hora_inicio, r.hora_fin, r.duracion_tipo, "
            "r.estado_asistencia, r.precio_mesa_aplicado, "
            "c.nombre AS cliente_nombre, c.apellido AS cliente_apellido, "
            "co.id AS consumo_id, co.precio_total, co.medio_pago, co.estado AS consumo_estado "
            "FROM mesas m "
            "JOIN grupos_mesa g ON g.id = m.grupo_mesa_id "
            "LEFT JOIN reservas r ON r.mesa_id = m.id AND r.fecha = %s "
            "  AND r.hora_inicio <= %s AND r.hora_fin > %s "
            "LEFT JOIN clientes c ON c.id = r.cliente_id "
            "LEFT JOIN consumos co ON co.reserva_id = r.id "
            "ORDER BY m.piso, m.numero_mesa",
            (fecha, hora, hora),
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def horarios_del_dia(fecha):
    # Horas de inicio distintas del dia, para ofrecer accesos rapidos en el
    # selector en vez de obligar a adivinar a que hora hay movimiento.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT DISTINCT hora_inicio FROM reservas WHERE fecha = %s ORDER BY hora_inicio",
            (fecha,),
        )
        return [fila[0] for fila in cursor.fetchall()]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
