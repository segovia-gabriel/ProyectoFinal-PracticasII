class UserSession:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserSession, cls).__new__(cls)
            cls._instance.username = None
            cls._instance.email = None
        return cls._instance

    def set_user(self, username, email):
        self.username = username
        self.email = email

    def clear_user(self):
        self.username = None
        self.email = None

    def is_logged_in(self):
        return self.username is not None
