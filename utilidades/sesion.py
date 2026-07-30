"""
Sesion del usuario logueado, hecha como singleton: cualquier modulo puede
preguntar quien esta adentro sin andar pasando el usuario por parametro. Guardo el
id ademas del nombre porque historial_acciones apunta a usuario_id.
"""


class Sesion:
    _instancia = None

    def __new__(cls):
        # Uso __new__ y no __init__ para que un segundo Sesion() te devuelva la
        # instancia que ya existe en vez de pisar los datos.
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
