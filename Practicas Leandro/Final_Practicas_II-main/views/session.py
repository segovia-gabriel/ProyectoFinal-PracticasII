class UserSession:
    _instance = None  # Variable de clase para almacenar la única instancia de la clase (Singleton).

    def __new__(cls):
        # Si no se ha creado una instancia, se crea una nueva.
        if cls._instance is None:
            cls._instance = super(UserSession, cls).__new__(cls)  # Llama al método __new__ de la superclase para crear la instancia.
            # Inicializa los atributos
            cls._instance.user_id = None  # Nuevo atributo para almacenar el ID del usuario
            cls._instance.username = None   
            cls._instance.grupo = None  
        return cls._instance  

    def set_user(self, user_id, username, grupo):
        # Método para establecer el ID, nombre de usuario y grupo en la sesión.
        self.user_id = user_id  # Almacena el ID del usuario
        self.username = username  
        self.grupo = grupo

    def get_user_id(self):
        # Método para obtener el ID del usuario
        return self.user_id

    def clear_user(self):
        # Método para limpiar los datos del usuario, simulando un cierre de sesión.
        self.user_id = None  # Limpia el ID del usuario
        self.username = None  
        self.grupo = None  

    def is_logged_in(self):
        # Método para verificar si un usuario está logueado.
        return self.username is not None  # Retorna True si 'username' no es None (usuario logueado), de lo contrario False.
