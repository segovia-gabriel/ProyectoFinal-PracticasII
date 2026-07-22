"""
Controlador de Usuarios. Valida, aplica las reglas de negocio (unicidad del
nombre, criterio de contrasena, no borrar el ultimo usuario ni el propio),
llama al modelo y registra cada alta/baja/modificacion en el historial.
No conoce widgets: devuelve (exito, mensaje) o (exito, datos) a la vista.
"""

from mysql.connector import Error

from modelo import usuario_modelo
from modelo.historial_modelo import registrar_accion
from utilidades import validaciones
from utilidades.seguridad import hashear_contrasena
from utilidades.sesion import Sesion


class UsuariosControlador:

    def listar(self, filtro_nombre=None):
        # Devuelve (True, lista_de_usuarios) o (False, mensaje) si falla la base.
        try:
            return True, usuario_modelo.listar(filtro_nombre)
        except Error:
            return False, "No se pudieron cargar los usuarios."

    def obtener(self, usuario_id):
        # Para precargar el formulario al editar.
        try:
            return True, usuario_modelo.obtener_por_id(usuario_id)
        except Error:
            return False, "No se pudo obtener el usuario."

    def guardar(self, usuario_id, nombre_usuario, contrasena, contrasena_repetida):
        # usuario_id None => alta; con id => edicion.
        nombre_usuario = nombre_usuario.strip()

        valido, mensaje = validaciones.validar_nombre_usuario(nombre_usuario)
        if not valido:
            return False, mensaje

        try:
            if usuario_modelo.existe_nombre(nombre_usuario, excluir_id=usuario_id):
                return False, "Ya existe un usuario con ese nombre."
        except Error:
            return False, "No se pudo verificar el nombre de usuario."

        # En alta la contrasena es obligatoria; en edicion, dejarla vacia
        # significa "no cambiar la contrasena".
        es_alta = usuario_id is None
        cambia_contrasena = es_alta or contrasena != ""

        hash_contrasena = None
        if cambia_contrasena:
            valido, mensaje = validaciones.validar_contrasena(contrasena)
            if not valido:
                return False, mensaje
            if contrasena != contrasena_repetida:
                return False, "Las contraseñas no coinciden."
            hash_contrasena = hashear_contrasena(contrasena)

        try:
            if es_alta:
                usuario_modelo.crear(nombre_usuario, hash_contrasena)
                registrar_accion(Sesion().usuario_id, f"Creó usuario: {nombre_usuario}")
                return True, "Usuario creado correctamente."
            else:
                usuario_modelo.modificar(usuario_id, nombre_usuario, hash_contrasena)
                registrar_accion(Sesion().usuario_id, f"Modificó usuario: {nombre_usuario}")
                return True, "Usuario modificado correctamente."
        except Error:
            return False, "No se pudo guardar el usuario en la base de datos."

    def eliminar(self, usuario_id):
        # Regla: no puede borrarse a si mismo (perderia la sesion activa)...
        if usuario_id == Sesion().usuario_id:
            return False, "No podés eliminar tu propio usuario mientras estás logueado."

        try:
            # ...ni el ultimo usuario del sistema (nadie podria volver a entrar).
            if usuario_modelo.contar() <= 1:
                return False, "No se puede eliminar el único usuario del sistema."

            usuario = usuario_modelo.obtener_por_id(usuario_id)
            if usuario is None:
                return False, "El usuario ya no existe."

            usuario_modelo.eliminar(usuario_id)
            registrar_accion(Sesion().usuario_id, f"Eliminó usuario: {usuario['nombre_usuario']}")
            return True, "Usuario eliminado correctamente."
        except Error:
            return False, "No se pudo eliminar el usuario."
