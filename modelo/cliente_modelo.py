
from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def listar(filtro_nombre=None, filtro_dni=None, fecha_desde=None, fecha_hasta=None):
    # Filtros del listado: nombre, DNI (con eso identifico al cliente) y rango de
    # fecha de registro.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = ("SELECT id, nombre, apellido, dni, fecha_nacimiento, direccion, "
               "telefono, fecha_registro FROM clientes")
        condiciones = []
        parametros = []
        if filtro_nombre:
            # busca en nombre o apellido, asi el filtro sirve de algo
            condiciones.append("(nombre LIKE %s OR apellido LIKE %s)")
            parametros += [f"%{filtro_nombre}%", f"%{filtro_nombre}%"]
        if filtro_dni:
            condiciones.append("dni LIKE %s")
            parametros.append(f"%{filtro_dni}%")
        if fecha_desde:
            condiciones.append("fecha_registro >= %s")
            parametros.append(fecha_desde)
        if fecha_hasta:
            condiciones.append("fecha_registro <= %s")
            parametros.append(fecha_hasta)
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        sql += " ORDER BY apellido, nombre"
        cursor.execute(sql, tuple(parametros))
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_por_id(cliente_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre, apellido, dni, fecha_nacimiento, direccion, telefono "
            "FROM clientes WHERE id = %s",
            (cliente_id,),
        )
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def existe_dni(dni, excluir_id=None):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        if excluir_id is None:
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE dni = %s", (dni,))
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM clientes WHERE dni = %s AND id <> %s",
                (dni, excluir_id),
            )
        return cursor.fetchone()[0] > 0
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar_reservas_futuras(cliente_id):
    # Reservas de hoy para adelante: si tiene aunque sea una, no puedo borrar el cliente.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM reservas WHERE cliente_id = %s AND fecha >= CURDATE()",
            (cliente_id,),
        )
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar_reservas_totales(cliente_id):
    # Cualquier reserva, tambien las pasadas: aunque la regla de negocio mire solo
    # las futuras, la clave foranea no te deja borrar un cliente con reservas en el
    # historial, asi que lo chequeo antes para tirar un mensaje claro.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM reservas WHERE cliente_id = %s", (cliente_id,))
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def listar_reservas(cliente_id):
    # Para la vista de detalle del cliente: sus reservas con el codigo de mesa y el estado.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT r.fecha, r.hora_inicio, r.hora_fin, m.codigo AS mesa, "
            "r.estado_asistencia "
            "FROM reservas r JOIN mesas m ON m.id = r.mesa_id "
            "WHERE r.cliente_id = %s ORDER BY r.fecha DESC, r.hora_inicio DESC",
            (cliente_id,),
        )
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def crear(nombre, apellido, dni, fecha_nacimiento, direccion, telefono):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO clientes (nombre, apellido, dni, fecha_nacimiento, direccion, telefono) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (nombre, apellido, dni, fecha_nacimiento, direccion, telefono),
        )
        conexion.commit()
        return cursor.lastrowid
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def modificar(cliente_id, nombre, apellido, dni, fecha_nacimiento, direccion, telefono):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE clientes SET nombre = %s, apellido = %s, dni = %s, "
            "fecha_nacimiento = %s, direccion = %s, telefono = %s WHERE id = %s",
            (nombre, apellido, dni, fecha_nacimiento, direccion, telefono, cliente_id),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def eliminar(cliente_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
