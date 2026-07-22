import sys
import bcrypt
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox
from main_window import MainWindow
from util.session import UserSession
from python_mysql_config import config_db
from mysql.connector import MySQLConnection, Error
from util.logger import log


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi('ui/login.ui', self)
            self.pushButton.clicked.connect(self.login)
        except FileNotFoundError as error:
            log(error, "error")
            QMessageBox.critical(self, 'Error', 'El programa no pudo encontrar la pantalla de login. Consulte con el administrador.')
            sys.exit(1)

    def login(self):
        email = self.lineEdit_email.text()
        contrasena = self.lineEdit_contrasena.text()

        # INICIO: primera vez, luego borrar
        nombre= "juan"

        # Almacena la sesión
        session = UserSession()
        session.set_user(nombre, email)

        self.hide()
        self.main_window = MainWindow(nombre, email)
        self.main_window.show()
        #FIN: primera vez, luego borrar

        try:
            db_config = config_db()
            db = MySQLConnection(**db_config)
            cursor = db.cursor()
            cursor.execute("SELECT nombre, password FROM usuarios WHERE email = %s", (email,))
            resultado = cursor.fetchone()
        except Error as error:
            log(error, "error")
            QMessageBox.warning(self, 'Error', 'No se pudo finalizar el proceso debido a un error con la base de datos.')
        finally:
            if db is not None and db.is_connected():
                cursor.close()
                db.close()

        if resultado:
            nombre, contrasena_encriptada = resultado
            if bcrypt.checkpw(contrasena.encode('utf-8'), contrasena_encriptada.encode('utf-8')):
                # Almacena la sesión
                session = UserSession()
                session.set_user(nombre, email)

                self.hide()
                self.main_window = MainWindow(nombre, email)
                self.main_window.show()
            else:
                QMessageBox.warning(self, 'Error', 'Contraseña incorrecta.')
        else:
            QMessageBox.warning(self, 'Error', 'Email no encontrado.')
