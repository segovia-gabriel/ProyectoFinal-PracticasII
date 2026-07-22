"""
Sesion del usuario logueado. Adaptado del UserSession de sistema_ejemplo.
Es un singleton: haya la instancia que haya, siempre es la misma, asi cualquier
modulo puede preguntar quien esta logueado sin pasar el usuario por parametro.
Guardamos el id ademas del nombre porque historial_acciones referencia usuario_id.
"""


class Sesion:
    _instancia = None

    def __new__(cls):
        # __new__ (no __init__) para que la segunda vez que alguien haga Sesion()
        # devuelva la instancia ya creada en vez de pisar los datos.
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia.usuario_id = None
            cls._instancia.nombre_usuario = None
        return cls._instancia

    def iniciar(self, usuario_id, nombre_usuario):
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario

    def cerrar(self):
        self.usuario_id = None
        self.nombre_usuario = None

    def hay_sesion(self):
        return self.usuario_id is not None
