"""
Controlador del login. No conoce widgets: recibe usuario y contrasena como
texto, valida, consulta el modelo, y devuelve (exito, mensaje) para que la
vista muestre el resultado. Si el login es correcto, deja la sesion iniciada
y registra la accion en el historial antes de volver.
"""

from mysql.connector import Error

from modelo import usuario_modelo
from modelo.historial_modelo import registrar_accion
from utilidades.seguridad import verificar_contrasena
from utilidades.sesion import Sesion


class LoginControlador:

    def intentar_ingresar(self, nombre_usuario, contrasena):
        # Validacion basica antes de tocar la base.
        if not nombre_usuario or not contrasena:
            return False, "Completá usuario y contraseña."

        try:
            usuario = usuario_modelo.obtener_por_nombre(nombre_usuario)
        except Error:
            # El modelo ya logueo el detalle; a la vista solo un mensaje claro.
            return False, "No se pudo conectar con la base de datos."

        # Mismo mensaje si el usuario no existe o si la contrasena esta mal,
        # para no revelar cual de los dos fallo (buena practica de seguridad).
        if usuario is None or not verificar_contrasena(contrasena, usuario["contrasena_hash"]):
            return False, "Usuario o contraseña incorrectos."

        # Login correcto: dejamos constancia y abrimos la sesion global.
        try:
            usuario_modelo.actualizar_ultimo_acceso(usuario["id"])
            registrar_accion(usuario["id"], "Inicio de sesión")
        except Error:
            # Que falle la auditoria no deberia impedir entrar; ya quedo logueado.
            pass

        Sesion().iniciar(usuario["id"], usuario["nombre_usuario"])
        return True, ""
