"""
Controlador de Clientes. Valida los datos, aplica la regla de baja (no se puede
eliminar un cliente con reservas actuales o futuras), llama al modelo y registra
en el historial. Tambien expone las reservas del cliente para la vista de detalle.
"""

from datetime import date

from mysql.connector import Error

from modelo import cliente_modelo
from modelo.historial_modelo import registrar_accion
from utilidades import validaciones
from utilidades.sesion import Sesion


class ClientesControlador:

    def listar(self, filtro_nombre=None, filtro_dni=None, fecha_desde=None, fecha_hasta=None):
        try:
            return True, cliente_modelo.listar(filtro_nombre, filtro_dni, fecha_desde, fecha_hasta)
        except Error:
            return False, "No se pudieron cargar los clientes."

    def obtener(self, cliente_id):
        try:
            return True, cliente_modelo.obtener_por_id(cliente_id)
        except Error:
            return False, "No se pudo obtener el cliente."

    def listar_reservas(self, cliente_id):
        try:
            return True, cliente_modelo.listar_reservas(cliente_id)
        except Error:
            return False, "No se pudieron cargar las reservas del cliente."

    def guardar(self, cliente_id, nombre, apellido, dni, fecha_nacimiento, direccion, telefono):
        nombre = nombre.strip()
        apellido = apellido.strip()
        dni = dni.strip()
        direccion = direccion.strip()
        telefono = telefono.strip()

        # Nombre y apellido: obligatorios y sin numeros.
        for valor, etiqueta in ((nombre, "Nombre"), (apellido, "Apellido")):
            valido, mensaje = validaciones.validar_nombre_persona(valor, etiqueta)
            if not valido:
                return False, mensaje

        valido, mensaje = validaciones.validar_dni(dni)
        if not valido:
            return False, mensaje

        # Ningun dato del cliente es opcional: direccion y telefono obligatorios.
        valido, mensaje = validaciones.validar_direccion(direccion)
        if not valido:
            return False, mensaje

        valido, mensaje = validaciones.validar_telefono(telefono)
        if not valido:
            return False, mensaje

        # La fecha de nacimiento no puede ser futura.
        if fecha_nacimiento > date.today():
            return False, "La fecha de nacimiento no puede ser una fecha futura."

        try:
            if cliente_modelo.existe_dni(dni, excluir_id=cliente_id):
                return False, "Ya existe un cliente con ese DNI."
        except Error:
            return False, "No se pudo verificar el DNI."

        try:
            if cliente_id is None:
                cliente_modelo.crear(nombre, apellido, dni, fecha_nacimiento, direccion, telefono)
                registrar_accion(Sesion().usuario_id, f"Creó cliente: {apellido}, {nombre}")
                return True, "Cliente creado correctamente."
            else:
                cliente_modelo.modificar(cliente_id, nombre, apellido, dni,
                                         fecha_nacimiento, direccion, telefono)
                registrar_accion(Sesion().usuario_id, f"Modificó cliente: {apellido}, {nombre}")
                return True, "Cliente modificado correctamente."
        except Error:
            return False, "No se pudo guardar el cliente."

    def eliminar(self, cliente_id):
        try:
            # Regla de negocio de la consigna: no borrar si tiene reservas de hoy
            # en adelante.
            if cliente_modelo.contar_reservas_futuras(cliente_id) > 0:
                return False, ("No se puede eliminar el cliente porque tiene reservas "
                               "actuales o futuras.")
            # Integridad: aunque solo tenga reservas pasadas, la clave foranea
            # impide borrarlo; se avisa claro en vez de dejar reventar el DELETE.
            if cliente_modelo.contar_reservas_totales(cliente_id) > 0:
                return False, ("No se puede eliminar el cliente porque tiene reservas "
                               "registradas en su historial.")
            cliente = cliente_modelo.obtener_por_id(cliente_id)
            if cliente is None:
                return False, "El cliente ya no existe."
            cliente_modelo.eliminar(cliente_id)
            registrar_accion(
                Sesion().usuario_id,
                f"Eliminó cliente: {cliente['apellido']}, {cliente['nombre']}",
            )
            return True, "Cliente eliminado correctamente."
        except Error:
            return False, "No se pudo eliminar el cliente."
