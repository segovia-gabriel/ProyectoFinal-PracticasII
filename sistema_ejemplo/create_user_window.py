import re
import bcrypt
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox
from python_mysql_config import config_db
from mysql.connector import MySQLConnection


class CreateUserWindow(QWidget):
    def __init__(self, user_list_window):
        super().__init__()
        self.user_list_window = user_list_window
        uic.loadUi('ui/create_user.ui', self)
        self.pushButton_guardar.clicked.connect(self.guardar_usuario)
        self.pushButton_cancelar.clicked.connect(self.cancelar)

    def validar_email(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email)

    def validar_contrasena(self, password):
        return (len(password) >= 8 and len(password) <= 100 and
                any(c.isdigit() for c in password) and
                any(c.isupper() for c in password))

    def guardar_usuario(self):
        nombre = self.lineEdit_nombre.text()
        email = self.lineEdit_email.text()
        password = self.lineEdit_password.text()
        rol = self.comboBox_rol.currentText().lower()

        # Limpia los mensajes de error
        self.label_error_nombre.setText("")
        self.label_error_email.setText("")
        self.label_error_password.setText("")
        self.label_error_rol.setText("")

        # Validación
        if not (5 <= len(nombre) <= 50):
            self.label_error_nombre.setText("El nombre debe tener entre 5 y 50 caracteres.")
        elif not self.validar_email(email) or not (10 <= len(email) <= 100):
            self.label_error_email.setText("Email inválido o no cumple con las reglas.")
        elif not self.validar_contrasena(password):
            self.label_error_password.setText("La contraseña debe tener al menos 8 caracteres, un número y una letra mayúscula.")
        elif rol not in ["admin", "moderador"]:
            self.label_error_rol.setText("Debes seleccionar un rol válido.")
        else:
            # Guardar el usuario en la base de datos
            db_config = config_db()
            db = MySQLConnection(**db_config)
            cursor = db.cursor()
            password_encriptada = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)",
                           (nombre, email, password_encriptada.decode('utf-8'), rol))
            db.commit()
            db.close()

            QMessageBox.information(self, 'Éxito', 'Usuario creado exitosamente.')
            self.user_list_window.cargar_usuarios()  # Actualiza la lista de usuarios
            self.hide()  # Cierra el formulario de creación

    def cancelar(self):
        self.hide()
