"""
Controlador del Historial de acciones. Es un modulo de solo lectura: arma los
filtros (usuario, rango de fechas) y devuelve las filas a la vista. No registra
acciones ni permite editar (el historial no se toca).
"""

from datetime import timedelta

from mysql.connector import Error

from modelo import historial_modelo, usuario_modelo


class HistorialControlador:

    def listar_usuarios(self):
        # Para llenar el combo de filtro por usuario. Devuelve [(id, nombre), ...].
        try:
            usuarios = usuario_modelo.listar()
            return True, [(u["id"], u["nombre_usuario"]) for u in usuarios]
        except Error:
            return False, "No se pudieron cargar los usuarios."

    def listar(self, usuario_id=None, fecha_desde=None, fecha_hasta=None):
        # usuario_id None => todos los usuarios. Las fechas llegan como date de
        # los QDateEdit; a 'hasta' le sumamos un dia para incluir ese dia completo
        # (el modelo compara con < fecha_hasta).
        if fecha_hasta is not None:
            fecha_hasta = fecha_hasta + timedelta(days=1)
        try:
            filas = historial_modelo.listar_con_filtros(usuario_id, fecha_desde, fecha_hasta)
            return True, filas
        except Error:
            return False, "No se pudo cargar el historial."
