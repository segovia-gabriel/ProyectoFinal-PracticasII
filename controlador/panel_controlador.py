"""
Controlador del panel principal. Junta en una sola llamada los numeros y listas
del resumen del dia, ya formateados para mostrar, asi la vista no arma textos ni
sabe de SQL. Es solo lectura: el panel no modifica nada.
"""

from datetime import date

from mysql.connector import Error

from modelo import panel_modelo
from utilidades import formato

# Mismo umbral que usa el modulo Menu para avisar la renovacion de precios: lo
# pide el enunciado (avisar 10 dias antes del vencimiento).
DIAS_AVISO_RENOVACION = 10


class PanelControlador:

    def resumen(self):
        # Un solo metodo para toda la pantalla: si falla la base, el panel avisa
        # una vez en lugar de mostrar seis errores distintos.
        try:
            datos = {
                "reservas_hoy": panel_modelo.contar_reservas_hoy(),
                "reservas_manana": panel_modelo.contar_reservas_manana(),
                "reservas_futuras": panel_modelo.contar_reservas_futuras(),
                "agenda": self._agenda_de_hoy(),
                "avisos": self._avisos(),
            }
        except Error:
            return False, "No se pudo cargar el resumen del día."
        return True, datos

    def _agenda_de_hoy(self):
        # Cada fila queda lista para volcarse en la tabla, sin conversiones en la
        # vista. Se incluye el id y el estado crudo porque haciendo doble clic
        # sobre la fila se cambia la asistencia.
        filas = []
        for reserva in panel_modelo.reservas_de_hoy():
            filas.append({
                "id": reserva["id"],
                "horario": f"{formato.hora(reserva['hora_inicio'])} - {formato.hora(reserva['hora_fin'])}",
                "cliente": f"{reserva['cliente_apellido']}, {reserva['cliente_nombre']}",
                "mesa": reserva["mesa_codigo"],
                "estado_clave": reserva["estado_asistencia"],
                "estado": formato.estado_asistencia(reserva["estado_asistencia"]),
            })
        return filas

    def _avisos(self):
        # Dos tipos de pendiente en una sola lista. Cada uno lleva su tipo y el
        # id del registro para que el panel sepa que pantalla abrir cuando se le
        # hace doble clic.
        avisos = []

        for fila in panel_modelo.precios_por_vencer(DIAS_AVISO_RENOVACION):
            dias = int(fila["dias"])
            if dias == 0:
                cuando = "vence hoy"
            elif dias == 1:
                cuando = "vence mañana"
            else:
                cuando = f"vence en {dias} días"
            avisos.append({
                "tipo": "precio",
                "id": fila["item_id"],
                "texto": f"Precio de «{fila['item']}» {cuando} ({fila['fecha_fin'].strftime('%d/%m/%Y')}).",
            })

        for fila in panel_modelo.reservas_cumplidas_sin_consumo():
            # Texto corto a proposito: son varios y tienen que entrar en dos
            # lineas dentro del panel, sin que Qt los corte con puntos suspensivos.
            avisos.append({
                "tipo": "consumo",
                "id": fila["id"],
                "texto": (f"Falta el consumo del {fila['fecha'].strftime('%d/%m')} — "
                          f"{fila['cliente_apellido']}, {fila['cliente_nombre']} "
                          f"(mesa {fila['mesa_codigo']})."),
            })

        return avisos

    def saludo(self, nombre_usuario):
        # Saludo segun la hora, para que el panel se sienta parte del turno de trabajo.
        from datetime import datetime

        hora_actual = datetime.now().hour
        if hora_actual < 13:
            momento = "Buen día"
        elif hora_actual < 20:
            momento = "Buenas tardes"
        else:
            momento = "Buenas noches"
        return f"{momento}, {nombre_usuario}"

    def fecha_larga(self):
        # "Miércoles 22 de julio de 2026" -- se arma a mano porque strftime
        # depende del idioma del sistema operativo y en Windows sale en ingles.
        hoy = date.today()
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return (f"{dias[hoy.weekday()]} {hoy.day} de "
                f"{formato.nombre_mes(hoy.month).lower()} de {hoy.year}")
