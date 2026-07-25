"""
Controlador de Mesas y Grupos de mesa. Genera el codigo de la mesa (letra del
piso + numero), valida, llama a los modelos y registra en el historial.
El codigo se arma aca (no lo escribe el usuario) para que sea consistente.
"""

from mysql.connector import Error

from modelo import grupo_mesa_modelo, mesa_modelo
from modelo.historial_modelo import registrar_accion
from utilidades.sesion import Sesion


def _codigo_mesa(piso, numero_mesa):
    # piso 0 -> A, 1 -> B, 2 -> C... combinado con el numero de mesa (ej: A5).
    letra = chr(ord("A") + piso)
    return f"{letra}{numero_mesa}"


class MesasControlador:

    # ---------------- Mesas ----------------

    def listar_mesas(self, filtro_codigo=None):
        try:
            return True, mesa_modelo.listar(filtro_codigo)
        except Error:
            return False, "No se pudieron cargar las mesas."

    def obtener_mesa(self, mesa_id):
        try:
            return True, mesa_modelo.obtener_por_id(mesa_id)
        except Error:
            return False, "No se pudo obtener la mesa."

    def listar_grupos_combo(self):
        # Para el combo de grupo en el formulario de mesa.
        try:
            grupos = grupo_mesa_modelo.listar()
            return True, [(g["id"], g["nombre"]) for g in grupos]
        except Error:
            return False, "No se pudieron cargar los grupos."

    def guardar_mesa(self, mesa_id, numero_mesa, numero_sillas, piso, grupo_mesa_id):
        if numero_mesa <= 0:
            return False, "El número de mesa debe ser mayor a cero."
        if numero_sillas <= 0:
            return False, "El número de sillas debe ser mayor a cero."
        if grupo_mesa_id is None:
            return False, "Seleccioná un grupo de mesa."

        try:
            if mesa_modelo.existe_numero(numero_mesa, excluir_id=mesa_id):
                return False, "Ya existe una mesa con ese número."
        except Error:
            return False, "No se pudo verificar el número de mesa."

        codigo = _codigo_mesa(piso, numero_mesa)
        try:
            if mesa_id is None:
                mesa_modelo.crear(numero_mesa, numero_sillas, piso, codigo, grupo_mesa_id)
                registrar_accion(Sesion().usuario_id, f"Creó mesa: {codigo}")
                return True, "Mesa creada correctamente."
            else:
                mesa_modelo.modificar(mesa_id, numero_mesa, numero_sillas, piso, codigo, grupo_mesa_id)
                registrar_accion(Sesion().usuario_id, f"Modificó mesa: {codigo}")
                return True, "Mesa modificada correctamente."
        except Error:
            return False, "No se pudo guardar la mesa."

    def eliminar_mesa(self, mesa_id):
        try:
            if mesa_modelo.contar_reservas(mesa_id) > 0:
                return False, "No se puede eliminar la mesa porque tiene reservas asociadas."
            mesa = mesa_modelo.obtener_por_id(mesa_id)
            if mesa is None:
                return False, "La mesa ya no existe."
            mesa_modelo.eliminar(mesa_id)
            registrar_accion(Sesion().usuario_id, f"Eliminó mesa: {mesa['codigo']}")
            return True, "Mesa eliminada correctamente."
        except Error:
            return False, "No se pudo eliminar la mesa."

    # ---------------- Grupos de mesa ----------------

    def listar_grupos(self, filtro_nombre=None):
        try:
            return True, grupo_mesa_modelo.listar(filtro_nombre)
        except Error:
            return False, "No se pudieron cargar los grupos."

    def obtener_grupo(self, grupo_id):
        try:
            return True, grupo_mesa_modelo.obtener_por_id(grupo_id)
        except Error:
            return False, "No se pudo obtener el grupo."

    def guardar_grupo(self, grupo_id, nombre, valor):
        nombre = nombre.strip()
        if not nombre:
            return False, "El nombre del grupo no puede estar vacío."
        if valor <= 0:
            return False, "El valor del grupo debe ser mayor a cero."

        try:
            if grupo_mesa_modelo.existe_nombre(nombre, excluir_id=grupo_id):
                return False, "Ya existe un grupo con ese nombre."
        except Error:
            return False, "No se pudo verificar el nombre del grupo."

        try:
            if grupo_id is None:
                grupo_mesa_modelo.crear(nombre, valor)
                registrar_accion(Sesion().usuario_id, f"Creó grupo de mesa: {nombre}")
                return True, "Grupo creado correctamente."
            else:
                grupo_mesa_modelo.modificar(grupo_id, nombre, valor)
                registrar_accion(Sesion().usuario_id, f"Modificó grupo de mesa: {nombre}")
                return True, "Grupo modificado correctamente."
        except Error:
            return False, "No se pudo guardar el grupo."

    def eliminar_grupo(self, grupo_id):
        try:
            if grupo_mesa_modelo.contar_mesas(grupo_id) > 0:
                return False, "No se puede eliminar el grupo porque tiene mesas asignadas."
            grupo = grupo_mesa_modelo.obtener_por_id(grupo_id)
            if grupo is None:
                return False, "El grupo ya no existe."
            grupo_mesa_modelo.eliminar(grupo_id)
            registrar_accion(Sesion().usuario_id, f"Eliminó grupo de mesa: {grupo['nombre']}")
            return True, "Grupo eliminado correctamente."
        except Error:
            return False, "No se pudo eliminar el grupo."
