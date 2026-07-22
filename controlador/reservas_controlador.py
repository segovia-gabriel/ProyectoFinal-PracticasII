"""
Controlador de Reservas. Calcula la hora de fin y el precio (2h = 100% del valor
del grupo de la mesa, 3h = 125%), valida superposicion de horarios, y hace
cumplir la regla de que las reservas pasadas no se modifican ni se eliminan
(el estado de asistencia si se puede cambiar siempre). El precio se guarda como
snapshot al crear la reserva.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from mysql.connector import Error

from modelo import cliente_modelo, grupo_mesa_modelo, mesa_modelo, reserva_modelo
from modelo.historial_modelo import registrar_accion
from utilidades.sesion import Sesion

ESTADOS = ("en_espera", "asistio", "tardanza", "falto")


def _horas_de(duracion_tipo):
    return 2 if duracion_tipo == "2h" else 3


class ReservasControlador:

    def listar(self, filtro_nombre=None, fecha_desde=None, fecha_hasta=None):
        try:
            return True, reserva_modelo.listar(filtro_nombre, fecha_desde, fecha_hasta)
        except Error:
            return False, "No se pudieron cargar las reservas."

    def obtener(self, reserva_id):
        try:
            return True, reserva_modelo.obtener_por_id(reserva_id)
        except Error:
            return False, "No se pudo obtener la reserva."

    def listar_clientes_combo(self):
        try:
            clientes = cliente_modelo.listar()
            return True, [(c["id"], f"{c['apellido']}, {c['nombre']}") for c in clientes]
        except Error:
            return False, "No se pudieron cargar los clientes."

    def listar_mesas_combo(self):
        try:
            mesas = mesa_modelo.listar()
            return True, [(m["id"], f"{m['codigo']} — {m['grupo_nombre']}") for m in mesas]
        except Error:
            return False, "No se pudieron cargar las mesas."

    def es_pasada(self, reserva):
        # Una reserva es pasada si su fecha ya quedo atras respecto de hoy.
        return reserva["fecha"] < date.today()

    def calcular_precio(self, mesa_id, duracion_tipo):
        # Precio segun el valor del grupo de la mesa y la duracion. Devuelve
        # Decimal para no perder centavos. None si no se pudo resolver la mesa.
        mesa = mesa_modelo.obtener_por_id(mesa_id)
        if mesa is None:
            return None
        grupo = grupo_mesa_modelo.obtener_por_id(mesa["grupo_mesa_id"])
        if grupo is None:
            return None
        valor = grupo["valor"]  # Decimal
        if duracion_tipo == "3h":
            return valor * Decimal("1.25")
        return valor

    def _hora_fin(self, hora_inicio, duracion_tipo):
        # hora_inicio es un time; se le suman 2 o 3 horas. Se usa una fecha
        # cualquiera solo para poder sumar con timedelta.
        fin = datetime.combine(date.today(), hora_inicio) + timedelta(hours=_horas_de(duracion_tipo))
        return fin.time()

    def guardar(self, reserva_id, cliente_id, mesa_id, fecha, hora_inicio, duracion_tipo, estado):
        if cliente_id is None:
            return False, "Seleccioná un cliente."
        if mesa_id is None:
            return False, "Seleccioná una mesa."

        # No crear ni mover una reserva al pasado.
        if reserva_id is None and fecha < date.today():
            return False, "No se puede crear una reserva en una fecha pasada."

        # Al editar, si la reserva original es pasada, no se toca (regla dura).
        if reserva_id is not None:
            try:
                original = reserva_modelo.obtener_por_id(reserva_id)
            except Error:
                return False, "No se pudo verificar la reserva."
            if original is None:
                return False, "La reserva ya no existe."
            if self.es_pasada(original):
                return False, "No se puede modificar una reserva pasada (solo su estado de asistencia)."

        # El horario no puede cruzar la medianoche (la mesa se libera ese dia).
        horas = _horas_de(duracion_tipo)
        if hora_inicio.hour + horas > 24:
            return False, "El horario elegido se pasa de la medianoche."
        hora_fin = self._hora_fin(hora_inicio, duracion_tipo)

        try:
            if reserva_modelo.hay_superposicion(mesa_id, fecha, hora_inicio, hora_fin, excluir_id=reserva_id):
                return False, "La mesa ya tiene otra reserva que se cruza con ese horario."
            precio = self.calcular_precio(mesa_id, duracion_tipo)
            if precio is None:
                return False, "No se pudo calcular el precio de la mesa."
        except Error:
            return False, "No se pudo validar la reserva."

        try:
            if reserva_id is None:
                reserva_modelo.crear(cliente_id, mesa_id, fecha, hora_inicio, hora_fin,
                                     duracion_tipo, precio)
                registrar_accion(Sesion().usuario_id, f"Creó reserva para mesa {mesa_id} el {fecha}")
                return True, "Reserva creada correctamente."
            else:
                reserva_modelo.modificar(reserva_id, cliente_id, mesa_id, fecha, hora_inicio,
                                        hora_fin, duracion_tipo, precio, estado)
                registrar_accion(Sesion().usuario_id, f"Modificó reserva #{reserva_id}")
                return True, "Reserva modificada correctamente."
        except Error:
            return False, "No se pudo guardar la reserva."

    def cambiar_estado(self, reserva_id, estado):
        # Permitido siempre, incluso en reservas pasadas.
        if estado not in ESTADOS:
            return False, "Estado de asistencia inválido."
        try:
            reserva_modelo.actualizar_estado(reserva_id, estado)
            registrar_accion(Sesion().usuario_id, f"Cambió estado de reserva #{reserva_id} a {estado}")
            return True, "Estado actualizado correctamente."
        except Error:
            return False, "No se pudo actualizar el estado."

    def eliminar(self, reserva_id):
        try:
            reserva = reserva_modelo.obtener_por_id(reserva_id)
            if reserva is None:
                return False, "La reserva ya no existe."
            if self.es_pasada(reserva):
                return False, "No se puede eliminar una reserva pasada."
            if reserva_modelo.contar_consumos(reserva_id) > 0:
                return False, "No se puede eliminar la reserva porque tiene un consumo cargado."
            reserva_modelo.eliminar(reserva_id)
            registrar_accion(Sesion().usuario_id, f"Eliminó reserva #{reserva_id}")
            return True, "Reserva eliminada correctamente."
        except Error:
            return False, "No se pudo eliminar la reserva."
