"""
Controlador de Consumo. Resuelve el precio de cada item segun el medio de pago
(precio especial si el medio coincide, si no el de lista), arma el detalle con
esos precios como snapshot y calcula el total. Un consumo por reserva.
"""

from decimal import Decimal

from mysql.connector import Error

from modelo import consumo_modelo, menu_modelo, precio_menu_modelo
from modelo.historial_modelo import registrar_accion
from utilidades.sesion import Sesion


class ConsumoControlador:

    def listar(self):
        try:
            return True, consumo_modelo.listar()
        except Error:
            return False, "No se pudieron cargar los consumos."

    def obtener_detalle(self, consumo_id):
        try:
            return True, consumo_modelo.obtener_detalle(consumo_id)
        except Error:
            return False, "No se pudo cargar el detalle del consumo."

    def listar_reservas_combo(self):
        # Solo reservas sin consumo (la regla es un consumo por reserva).
        try:
            reservas = consumo_modelo.reservas_sin_consumo()
            opciones = []
            for r in reservas:
                texto = f"{r['apellido']}, {r['nombre']} — {r['mesa_codigo']} — {r['fecha'].strftime('%d/%m/%Y')}"
                opciones.append((r["id"], texto))
            return True, opciones
        except Error:
            return False, "No se pudieron cargar las reservas."

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

    def guardar_consumo(self, reserva_id, medio_pago, items):
        # items: lista de (item_id, cantidad). Se resuelve el precio de cada uno,
        # se arma el detalle (snapshot) y se calcula el total.
        if reserva_id is None:
            return False, "Seleccioná una reserva."
        if medio_pago not in ("efectivo", "transferencia"):
            return False, "Seleccioná el medio de pago."
        if not items:
            return False, "Agregá al menos un ítem al consumo."

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

            consumo_modelo.crear_consumo(reserva_id, medio_pago, total, detalles)
            registrar_accion(Sesion().usuario_id, f"Cargó consumo de la reserva #{reserva_id}")
            return True, "Consumo cargado correctamente."
        except Error:
            return False, "No se pudo guardar el consumo."
