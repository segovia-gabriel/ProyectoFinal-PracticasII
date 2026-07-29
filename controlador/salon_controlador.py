"""
Controlador del plano del salon. Traduce cada mesa a un estado visual segun lo
que este pasando en el horario elegido, y arma los textos que muestra la vista.
Es solo lectura: las acciones sobre la reserva (asistencia, consumo) las
resuelven ReservasControlador y ConsumoControlador, que ya existian.
"""

from datetime import date

from mysql.connector import Error

from modelo import salon_modelo
from utilidades import formato

# Estados posibles de una mesa en el plano. El orden es el del circuito real:
# libre -> reservada -> ocupada -> cerrada. 'falto' es la via muerta.
LIBRE = "libre"
RESERVADA = "reservada"
OCUPADA = "ocupada"
CERRADA = "cerrada"
FALTO = "falto"

ETIQUETAS = {
    LIBRE: "Libre",
    RESERVADA: "Reservada",
    OCUPADA: "Mesa abierta",
    CERRADA: "Cuenta cerrada",
    FALTO: "No se presento",
}


class SalonControlador:

    def estado_del_salon(self, hora):
        # Devuelve las mesas agrupadas por piso, cada una ya con su estado y sus
        # textos listos para dibujar. La fecha es siempre hoy: el plano muestra
        # como esta el salon, no sirve para consultar dias pasados.
        try:
            filas = salon_modelo.mesas_en(date.today(), hora)
        except Error:
            return False, "No se pudo cargar el estado del salon."

        pisos = {}
        for fila in filas:
            pisos.setdefault(fila["piso"], []).append(self._armar_mesa(fila))
        return True, pisos

    def _armar_mesa(self, fila):
        mesa = {
            "id": fila["id"],
            "codigo": fila["codigo"],
            "sillas": fila["numero_sillas"],
            "grupo": fila["grupo_nombre"],
            "grupo_valor": float(fila["grupo_valor"]),
            "reserva_id": fila["reserva_id"],
            "consumo_id": fila["consumo_id"],
            "consumo_estado": fila["consumo_estado"],
            "estado_reserva": fila["estado_asistencia"],
        }

        if fila["reserva_id"] is None:
            mesa["estado"] = LIBRE
            mesa["cliente"] = ""
            mesa["horario"] = ""
            mesa["detalle"] = "Sin reserva en este horario."
            return mesa

        mesa["cliente"] = f"{fila['cliente_apellido']}, {fila['cliente_nombre']}"
        mesa["horario"] = (f"{formato.hora(fila['hora_inicio'])} - "
                           f"{formato.hora(fila['hora_fin'])}")

        if fila["estado_asistencia"] == "falto":
            mesa["estado"] = FALTO
            mesa["detalle"] = "El cliente no se presento."
        elif fila["consumo_id"] is not None and fila["consumo_estado"] == "cerrada":
            mesa["estado"] = CERRADA
            mesa["detalle"] = (f"Cuenta cerrada: {formato.moneda(fila['precio_total'])} en "
                               f"{formato.medio_pago(fila['medio_pago']).lower()}.")
        elif fila["estado_asistencia"] in ("asistio", "tardanza"):
            # Mesa abierta: el cliente esta y la cuenta esta en curso. Si ya tiene
            # un consumo abierto, se muestra el total que lleva.
            mesa["estado"] = OCUPADA
            if fila["consumo_id"] is not None:
                mesa["detalle"] = (f"Mesa abierta. Lleva {formato.moneda(fila['precio_total'])}. "
                                   "Se pueden agregar items o cerrar la cuenta.")
            else:
                mesa["detalle"] = "El cliente esta en la mesa. Carga el consumo."
        else:
            mesa["estado"] = RESERVADA
            mesa["detalle"] = "Reservada, todavia no llego el cliente."

        return mesa

    def resumen(self, pisos):
        # Conteo por estado para la linea de resumen de arriba del plano.
        conteo = {}
        for mesas in pisos.values():
            for mesa in mesas:
                conteo[mesa["estado"]] = conteo.get(mesa["estado"], 0) + 1
        partes = []
        for clave in (LIBRE, RESERVADA, OCUPADA, CERRADA, FALTO):
            if conteo.get(clave):
                partes.append(f"{ETIQUETAS[clave]}: {conteo[clave]}")
        return "   |   ".join(partes) if partes else "No hay mesas cargadas."

    def nombre_piso(self, piso):
        if piso == 0:
            return "Planta baja"
        if piso == 1:
            return "Primer piso"
        return f"Piso {piso}"

    def horarios_sugeridos(self):
        # Horas en las que hoy hay reservas, para los accesos rapidos.
        try:
            return True, salon_modelo.horarios_del_dia(date.today())
        except Error:
            return False, "No se pudieron cargar los horarios del dia."
