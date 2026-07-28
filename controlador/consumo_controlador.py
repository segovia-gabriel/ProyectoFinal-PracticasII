"""
Controlador de Consumo. Maneja la cuenta de la mesa bajo el concepto de mesa
abierta / cerrada: mientras esta abierta se le agregan o editan items, y al
cerrarla la cuenta pasa al historial de ventas. Resuelve el precio de cada item
segun el medio de pago (especial si el medio coincide, si no el de lista), arma
el detalle con esos precios como snapshot y calcula el total. Un consumo por
reserva.
"""

from datetime import date
from decimal import Decimal

from mysql.connector import Error

from modelo import consumo_modelo, menu_modelo, precio_menu_modelo, reserva_modelo
from modelo.historial_modelo import registrar_accion
from utilidades.sesion import Sesion


class ConsumoControlador:

    def listar(self, filtro_nombre=None, fecha_desde=None, fecha_hasta=None):
        try:
            return True, consumo_modelo.listar(filtro_nombre, fecha_desde, fecha_hasta)
        except Error:
            return False, "No se pudieron cargar los consumos."

    def obtener_detalle(self, consumo_id):
        try:
            return True, consumo_modelo.obtener_detalle(consumo_id)
        except Error:
            return False, "No se pudo cargar el detalle del consumo."

    def preparar_edicion(self, reserva_id):
        # Trae el consumo de una reserva (si existe) con sus items, para precargar
        # el dialogo. Devuelve (True, None) si la mesa todavia no tiene consumo
        # (es una carga nueva).
        try:
            consumo = consumo_modelo.obtener_por_reserva(reserva_id)
            if consumo is None:
                return True, None
            detalle = consumo_modelo.obtener_detalle(consumo["id"])
        except Error:
            return False, "No se pudo cargar el consumo de la mesa."
        items = [{"item_id": d["menu_item_id"], "nombre": d["nombre"], "cantidad": d["cantidad"]}
                 for d in detalle]
        return True, {"medio_pago": consumo["medio_pago"], "estado": consumo["estado"], "items": items}

    def _texto_reserva(self, r):
        return f"{r['apellido']}, {r['nombre']} — {r['mesa_codigo']} — {r['fecha'].strftime('%d/%m/%Y')}"

    def listar_reservas_combo(self):
        # Solo reservas sin consumo (la regla es un consumo por reserva).
        try:
            reservas = consumo_modelo.reservas_sin_consumo()
            return True, [(r["id"], self._texto_reserva(r)) for r in reservas]
        except Error:
            return False, "No se pudieron cargar las reservas."

    def texto_reserva(self, reserva_id):
        # Texto de UNA reserva puntual, para cuando el dialogo se abre ya fijado
        # a ella (desde el salon o desde un pendiente del panel).
        try:
            r = reserva_modelo.obtener_para_consumo(reserva_id)
        except Error:
            return False, "No se pudo cargar la reserva."
        if r is None:
            return False, "La reserva ya no existe."
        return True, self._texto_reserva(r)

    def listar_items_combo(self):
        try:
            items = menu_modelo.listar()
            return True, [(i["id"], i["nombre"]) for i in items]
        except Error:
            return False, "No se pudieron cargar los ítems."

    def precio_item(self, item_id, medio_pago):
        # Precio vigente resuelto segun el medio de pago. Devuelve Decimal o None
        # si el item no tiene precio cargado todavia.
        vigente = precio_menu_modelo.obtener_vigente(item_id)
        if vigente is None:
            return None
        # si hay precio especial y el medio de pago coincide, se usa ese
        if (vigente["precio_especial"] is not None
                and vigente["medio_pago_especial"] == medio_pago):
            return vigente["precio_especial"]
        return vigente["precio_lista"]

    def guardar_consumo(self, reserva_id, medio_pago, items, cerrar=False):
        # items: lista de (item_id, cantidad). Se resuelve el precio de cada uno,
        # se arma el detalle (snapshot) y se calcula el total. Si la mesa todavia
        # no tiene consumo se crea (abierta), y si ya lo tiene abierto se
        # reemplaza el detalle. Con cerrar=True ademas se consolida la cuenta.
        if reserva_id is None:
            return False, "Seleccioná una reserva."
        if medio_pago not in ("efectivo", "transferencia"):
            return False, "Seleccioná el medio de pago."
        if not items:
            return False, "Agregá al menos un ítem al consumo."

        # Se revalida la reserva aca y no solo al armar el combo: el consumo es
        # de "las personas que asistieron", asi que la reserva tiene que haber
        # ocurrido y el cliente tiene que haber estado.
        try:
            reserva = reserva_modelo.obtener_por_id(reserva_id)
        except Error:
            return False, "No se pudo verificar la reserva."
        if reserva is None:
            return False, "La reserva ya no existe."
        if reserva["fecha"] > date.today():
            return False, "Esa reserva todavía no ocurrió: no se le puede cargar el consumo."
        if reserva["estado_asistencia"] not in ("asistio", "tardanza"):
            return False, ("Primero marcá la asistencia del cliente en Reservas "
                           "(solo se cobra a quien asistió).")

        # Si ya hay un consumo cerrado, la cuenta esta consolidada y no se toca.
        try:
            existente = consumo_modelo.obtener_por_reserva(reserva_id)
        except Error:
            return False, "No se pudo verificar el consumo."
        if existente is not None and existente["estado"] == "cerrada":
            return False, "Esa mesa ya tiene la cuenta cerrada; no se puede modificar."

        try:
            detalles = []
            total = Decimal("0")
            for item_id, cantidad in items:
                if cantidad <= 0:
                    return False, "Las cantidades deben ser mayores a cero."
                precio = self.precio_item(item_id, medio_pago)
                if precio is None:
                    return False, "Hay un ítem sin precio cargado; cargale un precio primero."
                detalles.append((item_id, cantidad, precio))
                total += precio * cantidad

            if existente is None:
                # Primera carga: nace abierta, o directamente cerrada si se cierra.
                consumo_modelo.crear_consumo(
                    reserva_id, medio_pago, total, detalles,
                    "cerrada" if cerrar else "abierta")
            else:
                # Mesa ya abierta: se reemplaza el detalle con lo que hay ahora.
                consumo_modelo.reemplazar_detalle(existente["id"], medio_pago, total, detalles)
                if cerrar:
                    consumo_modelo.cerrar(existente["id"])

            if cerrar:
                registrar_accion(Sesion().usuario_id, f"Cerró la cuenta de la reserva #{reserva_id}")
                return True, "Mesa cerrada. La cuenta pasó al historial de ventas."
            registrar_accion(Sesion().usuario_id, f"Guardó el consumo abierto de la reserva #{reserva_id}")
            return True, "Consumo guardado. La mesa sigue abierta."
        except Error:
            return False, "No se pudo guardar el consumo."
