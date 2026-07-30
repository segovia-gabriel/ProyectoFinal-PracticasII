"""
Cierre de mesas del restaurante. Al cerrar el dia (con el boton) o al abrir el
sistema (barrido de lo que quedo de dias anteriores) se cierran las mesas
abiertas: las que tienen consumo cargado pasan a 'cerrada', las vacias se
descartan y las reservas que quedaron sin consumo se marcan como vencidas.
Coordina consumo + reservas, por eso vive en su propio controlador.
"""

from datetime import date, timedelta

from mysql.connector import Error

from modelo import consumo_modelo, reserva_modelo
from modelo.historial_modelo import registrar_accion
from utilidades.sesion import Sesion


class CierreControlador:

    def cerrar_dia(self):
        # Cierre manual desde el panel: incluye el dia de hoy.
        return self._cerrar_hasta(date.today(), "Cerro el dia")

    def barrido_inicial(self):
        # Al iniciar sesion: cierra solo lo que quedo de dias ANTERIORES, por si
        # ayer no lo cerraron a mano. No toca las mesas abiertas de hoy.
        limite = date.today() - timedelta(days=1)
        return self._cerrar_hasta(limite, "Cierre automatico de mesas de dias anteriores")

    def _cerrar_hasta(self, fecha_limite, descripcion):
        try:
            cerradas = consumo_modelo.cerrar_abiertas_con_items(fecha_limite)
            descartadas = consumo_modelo.eliminar_abiertas_vacias(fecha_limite)
            vencidas = reserva_modelo.vencer_consumos_pendientes(fecha_limite)
        except Error:
            return False, "No se pudo completar el cierre de mesas."

        # Solo anoto en el historial si de verdad hubo algo que cerrar, asi no
        # ensucio el log con un cierre vacio cada vez que abren el sistema.
        if cerradas + descartadas + vencidas > 0:
            registrar_accion(
                Sesion().usuario_id,
                f"{descripcion}: {cerradas} mesas cerradas, "
                f"{descartadas} vacias descartadas, {vencidas} sin consumo vencidas.",
            )
        return True, {"cerradas": cerradas, "descartadas": descartadas, "vencidas": vencidas}
