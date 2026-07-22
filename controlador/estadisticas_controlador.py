"""
Controlador de Estadisticas. Junta las consultas del modelo y las deja listas
para mostrar en tablas: pasa los dias de la semana a espanol, ordena, y arma el
top 5 de items por dia. Es solo lectura.
"""

from mysql.connector import Error

from modelo import estadisticas_modelo
from utilidades import formato


class EstadisticasControlador:

    def clientes(self):
        try:
            total = estadisticas_modelo.total_clientes()
            top = estadisticas_modelo.top_clientes(5)
            return True, {"total": total, "top": top}
        except Error:
            return False, "No se pudieron cargar las estadísticas de clientes."

    def reservas(self):
        try:
            futuras = estadisticas_modelo.reservas_futuras()
            por_mes = estadisticas_modelo.reservas_por_mes()
            # agregamos el nombre del mes en espanol para mostrarlo
            for fila in por_mes:
                fila["mes_nombre"] = formato.nombre_mes(fila["mes"])
            return True, {"futuras": futuras, "por_mes": por_mes}
        except Error:
            return False, "No se pudieron cargar las estadísticas de reservas."

    def consumo(self, anio, mes):
        try:
            ingresos = estadisticas_modelo.ingresos_por_dia_semana(anio, mes)
            items = estadisticas_modelo.items_por_dia_semana(anio, mes)
        except Error:
            return False, "No se pudieron cargar las estadísticas de consumo."

        # Ingresos: dia a espanol y ordenados de Lunes a Domingo.
        ingresos_es = [(formato.dia_semana(f["dia"]), float(f["ingreso"])) for f in ingresos]
        ingresos_es.sort(key=lambda x: formato.ORDEN_DIAS.index(x[0]) if x[0] in formato.ORDEN_DIAS else 99)

        # Top 5 items por dia: la consulta ya viene ordenada por total desc dentro
        # de cada dia; agrupamos y nos quedamos con los primeros 5 de cada uno.
        por_dia = {}
        for fila in items:
            dia = formato.dia_semana(fila["dia"])
            por_dia.setdefault(dia, []).append((fila["item"], int(fila["total"])))

        top_items = []
        for dia in formato.ORDEN_DIAS:
            for nombre, total in por_dia.get(dia, [])[:5]:
                top_items.append((dia, nombre, total))

        return True, {"ingresos": ingresos_es, "top_items": top_items}
