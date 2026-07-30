"""
Acceso a datos de la tabla usuarios. Cada funcion hace una sola cosa en SQL y
devuelve datos pelados (dict/tupla/None), nunca widgets.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def obtener_por_nombre(nombre_usuario):
    # Devuelve el usuario (id + hash) para chequear el login, o None si no existe.
    # Pido solo las columnas que necesito, nada de SELECT *.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre_usuario, contrasena_hash FROM usuarios WHERE nombre_usuario = %s",
            (nombre_usuario,),
        )
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def actualizar_ultimo_acceso(usuario_id):
    # Lo llamo despues de un login OK para dejar anotado cuando entro.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE usuarios SET fecha_ultimo_acceso = NOW() WHERE id = %s",
            (usuario_id,),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def listar(filtro_nombre=None):
    # Devuelve los usuarios para el listado. Nunca trae la contrasena_hash porque
    # no se muestra en pantalla. Si viene filtro_nombre, filtra por coincidencia.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = ("SELECT id, nombre_usuario, fecha_creacion, fecha_modificacion, "
               "fecha_ultimo_acceso FROM usuarios")
        parametros = ()
        if filtro_nombre:
            sql += " WHERE nombre_usuario LIKE %s"
            parametros = (f"%{filtro_nombre}%",)
        sql += " ORDER BY nombre_usuario"
        cursor.execute(sql, parametros)
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_por_id(usuario_id):
    # Para precargar el formulario cuando edito. Sin la contrasena, que no se vuelve a mostrar.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre_usuario FROM usuarios WHERE id = %s", (usuario_id,)
        )
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def existe_nombre(nombre_usuario, excluir_id=None):
    # Chequea que el nombre no este repetido antes de guardar. Al editar excluyo
    # el propio id, asi no choca consigo mismo.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        if excluir_id is None:
            cursor.execute(
                "SELECT COUNT(*) FROM usuarios WHERE nombre_usuario = %s",
                (nombre_usuario,),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM usuarios WHERE nombre_usuario = %s AND id <> %s",
                (nombre_usuario, excluir_id),
            )
        return cursor.fetchone()[0] > 0
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar():
    # Lo uso para no dejar borrar el ultimo usuario, sino nos quedariamos sin acceso.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def crear(nombre_usuario, contrasena_hash):
    # Inserta un usuario nuevo. El hash ya viene calculado del controlador, el
    # modelo nunca ve la contrasena en texto plano. Devuelve el id nuevo.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nombre_usuario, contrasena_hash) VALUES (%s, %s)",
            (nombre_usuario, contrasena_hash),
        )
        conexion.commit()
        return cursor.lastrowid
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def modificar(usuario_id, nombre_usuario, contrasena_hash=None):
    # Actualiza el nombre y, solo si mandaron una contrasena nueva, tambien el
    # hash. Si contrasena_hash es None dejo la que ya tenia, no la piso con un
    # vacio. La fecha_modificacion se pone al momento del cambio.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        if contrasena_hash is None:
            cursor.execute(
                "UPDATE usuarios SET nombre_usuario = %s, fecha_modificacion = NOW() "
                "WHERE id = %s",
                (nombre_usuario, usuario_id),
            )
        else:
            cursor.execute(
                "UPDATE usuarios SET nombre_usuario = %s, contrasena_hash = %s, "
                "fecha_modificacion = NOW() WHERE id = %s",
                (nombre_usuario, contrasena_hash, usuario_id),
            )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def eliminar(usuario_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
