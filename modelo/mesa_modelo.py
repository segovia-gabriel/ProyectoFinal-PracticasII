"""
Acceso a datos de mesas. El codigo (letra de piso + numero) lo arma el
controlador y se guarda ya listo. El listado trae el nombre del grupo con un JOIN
para mostrarlo sin que la vista tenga que resolverlo.
"""

from mysql.connector import Error

from modelo.conexion import abrir_conexion
from utilidades.logger import registrar


def listar(filtro_codigo=None):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        sql = (
            "SELECT m.id, m.numero_mesa, m.numero_sillas, m.piso, m.codigo, "
            "m.grupo_mesa_id, g.nombre AS grupo_nombre "
            "FROM mesas m JOIN grupos_mesa g ON g.id = m.grupo_mesa_id"
        )
        parametros = ()
        if filtro_codigo:
            sql += " WHERE m.codigo LIKE %s"
            parametros = (f"%{filtro_codigo}%",)
        sql += " ORDER BY m.piso, m.numero_mesa"
        cursor.execute(sql, parametros)
        return cursor.fetchall()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def obtener_por_id(mesa_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, numero_mesa, numero_sillas, piso, codigo, grupo_mesa_id "
            "FROM mesas WHERE id = %s",
            (mesa_id,),
        )
        return cursor.fetchone()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def existe_numero(numero_mesa, piso, excluir_id=None):
    # El numero de mesa solo tiene que ser unico dentro del mismo piso.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        if excluir_id is None:
            cursor.execute(
                "SELECT COUNT(*) FROM mesas WHERE numero_mesa = %s AND piso = %s",
                (numero_mesa, piso),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM mesas WHERE numero_mesa = %s AND piso = %s AND id <> %s",
                (numero_mesa, piso, excluir_id),
            )
        return cursor.fetchone()[0] > 0
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def maximo_numero():
    # El numero_mesa mas alto cargado, para sugerir el siguiente en el alta. Si
    # todavia no hay mesas, MAX devuelve NULL y lo paso a 0.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT MAX(numero_mesa) FROM mesas")
        maximo = cursor.fetchone()[0]
        return maximo if maximo is not None else 0
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def contar_reservas(mesa_id):
    # Para avisar antes de borrar una mesa que tiene reservas colgadas.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM reservas WHERE mesa_id = %s", (mesa_id,))
        return cursor.fetchone()[0]
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def crear(numero_mesa, numero_sillas, piso, codigo, grupo_mesa_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO mesas (numero_mesa, numero_sillas, piso, codigo, grupo_mesa_id) "
            "VALUES (%s, %s, %s, %s, %s)",
            (numero_mesa, numero_sillas, piso, codigo, grupo_mesa_id),
        )
        conexion.commit()
        return cursor.lastrowid
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def modificar(mesa_id, numero_mesa, numero_sillas, piso, codigo, grupo_mesa_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE mesas SET numero_mesa = %s, numero_sillas = %s, piso = %s, "
            "codigo = %s, grupo_mesa_id = %s WHERE id = %s",
            (numero_mesa, numero_sillas, piso, codigo, grupo_mesa_id, mesa_id),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def eliminar(mesa_id):
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM mesas WHERE id = %s", (mesa_id,))
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
