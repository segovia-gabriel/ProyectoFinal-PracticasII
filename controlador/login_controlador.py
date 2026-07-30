

from mysql.connector import Error

from modelo import usuario_modelo
from modelo.historial_modelo import registrar_accion
from utilidades.seguridad import verificar_contrasena
from utilidades.sesion import Sesion


class LoginControlador:

    def intentar_ingresar(self, nombre_usuario, contrasena):
        # Un chequeo basico antes de tocar la base.
        if not nombre_usuario or not contrasena:
            return False, "Completa usuario y contrasena."

        try:
            usuario = usuario_modelo.obtener_por_nombre(nombre_usuario)
        except Error:
            # El modelo ya logueo el detalle, a la vista le doy solo un mensaje claro.
            return False, "No se pudo conectar con la base de datos."

        # Mismo mensaje si el usuario no existe o si la contrasena esta mal, asi
        # no revelo cual de los dos fallo (buena practica de seguridad).
        if usuario is None or not verificar_contrasena(contrasena, usuario["contrasena_hash"]):
            return False, "Usuario o contrasena incorrectos."

        # Login OK: dejo constancia y abro la sesion global.
        try:
            usuario_modelo.actualizar_ultimo_acceso(usuario["id"])
            registrar_accion(usuario["id"], "Inicio de sesion")
        except Error:
            # Que falle la auditoria no tiene que trabar el ingreso, ya esta logueado.
            pass

        Sesion().iniciar(usuario["id"], usuario["nombre_usuario"])
        return True, ""
