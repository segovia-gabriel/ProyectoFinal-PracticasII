"""
Acceso a datos de historial_acciones (auditoria).
registrar_accion() es la funcion comun que llaman todos los modulos (login,
usuarios, clientes, reservas...) cuando hacen un alta/baja/modificacion, asi no
repito el mismo INSERT en cada uno.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def registrar_accion(usuario_id, descripcion):
    # Guarda una linea de auditoria. La fecha_hora la pone la base con su DEFAULT
    # CURRENT_TIMESTAMP, asi que no la mando desde Python.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO historial_acciones (usuario_id, accion) VALUES (%s, %s)",
            (usuario_id, descripcion),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def listar_con_filtros(usuario_id=None, fecha_desde=None, fecha_hasta=None):
    # Listado de auditoria (solo lectura) con filtros opcionales. Hace JOIN con
    # usuarios para mostrar quien hizo cada accion. El WHERE lo armo sumando
    # condiciones solo para los filtros que vinieron con valor.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = (
            "SELECT h.id, u.nombre_usuario, h.accion, h.fecha_hora "
            "FROM historial_acciones h "
            "JOIN usuarios u ON u.id = h.usuario_id"
        )
        condiciones = []
        parametros = []
        if usuario_id is not None:
            condiciones.append("h.usuario_id = %s")
            parametros.append(usuario_id)
        if fecha_desde is not None:
            condiciones.append("h.fecha_hora >= %s")
            parametros.append(fecha_desde)
        if fecha_hasta is not None:
            # sumo un dia y uso < para que entre el dia 'hasta' completo
            condiciones.append("h.fecha_hora < %s")
            parametros.append(fecha_hasta)
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        sql += " ORDER BY h.fecha_hora DESC"
        cursor.execute(sql, tuple(parametros))
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
