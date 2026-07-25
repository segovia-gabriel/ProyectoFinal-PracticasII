"""
Acceso a datos de reservas. El listado trae nombre del cliente y codigo de mesa
con JOINs. El precio (precio_mesa_aplicado) llega ya calculado por el controlador
y se guarda como snapshot: no se recalcula aunque despues cambie el valor del grupo.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def listar(filtro_nombre=None, fecha_desde=None, fecha_hasta=None):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = (
            "SELECT r.id, r.cliente_id, r.mesa_id, r.fecha, r.hora_inicio, r.hora_fin, "
            "r.duracion_tipo, r.precio_mesa_aplicado, r.estado_asistencia, "
            "c.nombre AS cliente_nombre, c.apellido AS cliente_apellido, m.codigo AS mesa_codigo "
            "FROM reservas r "
            "JOIN clientes c ON c.id = r.cliente_id "
            "JOIN mesas m ON m.id = r.mesa_id"
        )
        condiciones = []
        parametros = []
        if filtro_nombre:
            condiciones.append("(c.nombre LIKE %s OR c.apellido LIKE %s)")
            parametros += [f"%{filtro_nombre}%", f"%{filtro_nombre}%"]
        if fecha_desde is not None:
            condiciones.append("r.fecha >= %s")
            parametros.append(fecha_desde)
        if fecha_hasta is not None:
            condiciones.append("r.fecha <= %s")
            parametros.append(fecha_hasta)
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        # De la mas proxima a la mas lejana: la pantalla arranca mostrando la
        # semana en curso, asi que arriba queda lo que esta por pasar.
        sql += " ORDER BY r.fecha ASC, r.hora_inicio ASC"
        cursor.execute(sql, tuple(parametros))
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_por_id(reserva_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, cliente_id, mesa_id, fecha, hora_inicio, hora_fin, "
            "duracion_tipo, precio_mesa_aplicado, estado_asistencia "
            "FROM reservas WHERE id = %s",
            (reserva_id,),
        )
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def hay_superposicion(mesa_id, fecha, hora_inicio, hora_fin, excluir_id=None):
    # Dos reservas se pisan si comparten mesa y dia y sus horarios se cruzan:
    # (inicio_existente < fin_nuevo) AND (fin_existente > inicio_nuevo).
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        sql = (
            "SELECT COUNT(*) FROM reservas WHERE mesa_id = %s AND fecha = %s "
            "AND hora_inicio < %s AND hora_fin > %s"
        )
        parametros = [mesa_id, fecha, hora_fin, hora_inicio]
        if excluir_id is not None:
            sql += " AND id <> %s"
            parametros.append(excluir_id)
        cursor.execute(sql, tuple(parametros))
        return cursor.fetchone()[0] > 0
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def crear(cliente_id, mesa_id, fecha, hora_inicio, hora_fin, duracion_tipo, precio_mesa_aplicado):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO reservas (cliente_id, mesa_id, fecha, hora_inicio, hora_fin, "
            "duracion_tipo, precio_mesa_aplicado) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (cliente_id, mesa_id, fecha, hora_inicio, hora_fin, duracion_tipo, precio_mesa_aplicado),
        )
        conexion.commit()
        return cursor.lastrowid
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def modificar(reserva_id, cliente_id, mesa_id, fecha, hora_inicio, hora_fin,
              duracion_tipo, precio_mesa_aplicado, estado_asistencia):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE reservas SET cliente_id = %s, mesa_id = %s, fecha = %s, "
            "hora_inicio = %s, hora_fin = %s, duracion_tipo = %s, "
            "precio_mesa_aplicado = %s, estado_asistencia = %s WHERE id = %s",
            (cliente_id, mesa_id, fecha, hora_inicio, hora_fin, duracion_tipo,
             precio_mesa_aplicado, estado_asistencia, reserva_id),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def actualizar_estado(reserva_id, estado_asistencia):
    # El estado de asistencia se puede cambiar siempre, incluso en reservas
    # pasadas (para marcar retroactivamente si asistio o falto).
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE reservas SET estado_asistencia = %s WHERE id = %s",
            (estado_asistencia, reserva_id),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_para_consumo(reserva_id):
    # Datos de una reserva puntual para mostrarla en el combo de Consumo cuando
    # el dialogo se abre ya apuntando a ella (desde el salon o el panel).
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT r.id, r.fecha, c.nombre, c.apellido, m.codigo AS mesa_codigo "
            "FROM reservas r "
            "JOIN clientes c ON c.id = r.cliente_id "
            "JOIN mesas m ON m.id = r.mesa_id "
            "WHERE r.id = %s",
            (reserva_id,),
        )
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar_consumos(reserva_id):
    # Para no borrar una reserva que ya tiene un consumo cargado.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM consumos WHERE reserva_id = %s", (reserva_id,))
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def eliminar(reserva_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
