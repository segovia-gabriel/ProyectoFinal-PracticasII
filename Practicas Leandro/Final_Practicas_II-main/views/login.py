import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from views.principalAdmin import MainWindow  
from views.principalUser import MainWindowUser
from PyQt5.QtCore import Qt
from error.logger import log  
from PyQt5.uic import loadUi 
from views.session import UserSession  
from database.conexion import Database
from views.password import verifica_password  # Importar la función para verificar la contraseña

class ClaseLogin(QMainWindow):   
    def __init__(self, parent=None):
        super(ClaseLogin, self).__init__(parent)
        try:
            # Cargar el diseño de la interfaz de usuario
            loadUi("ui\\login.ui", self)
            self.setup()
            self.sesion="Inicio Sesion"

            # Eliminar la barra de título de la ventana y ajustar la opacidad
            self.setWindowFlags(Qt.FramelessWindowHint) 
            self.setWindowOpacity(1.0)  # Opacidad completa (1.0 es totalmente opaco)

        except FileNotFoundError as error:
            log(error, "error")  # Registrar el error en el log
            QMessageBox.critical(self, 'Error', 'El programa no pudo encontrar la pantalla de login. Consulte con el administrador.')
            sys.exit(1)  # Cerrar la aplicación si hay un error crítico

    def setup(self):
        # Conectar el botón de aceptar con el método para procesar el login
        self.btn_aceptar.clicked.connect(self.aceptar_clicked)
        self.btn_cancelar.clicked.connect(self.close)

    def aceptar_clicked(self):
        """ Maneja el proceso de login """
        user = self.lineEdit_Usuario.text()
        password = self.lineEdit_Contrasenia.text()

        # Conexión y validación con la base de datos
        db = Database()
        try:
            # Obtener el usuario y la contraseña encriptada desde la base de datos
            resultado = db.obtener_usuario(user)
            print(resultado)
            
            if resultado:
                id_user = resultado[0]
                contrasena_encriptada = resultado[2]  # Hash + sal almacenada
                grupo = resultado[3]

                # Verificar la contraseña ingresada contra la encriptada
                if verifica_password(password, contrasena_encriptada):

                    print(grupo)
                    if grupo == "Administrador":
                        # Crea la sesión del usuario
                        session = UserSession()
                        session.set_user(id_user,user, grupo)
                        db.actualizar_ultimo_acceso(id_user)
                        db.registrar_historial_usuario(id_user,self.sesion)

                        self.hide()
                        self.main_window = MainWindow()
                        self.main_window.show() 
                    else:
                        # Si es un usuario normal, redirige a la ventana correspondiente
                        session = UserSession()
                        session.set_user(user, grupo)
                        db.actualizar_ultimo_acceso(id_user)
                        db.registrar_historial_usuario(id_user,self.sesion)

                        self.hide()
                        self.main_window = MainWindowUser()
                        self.main_window.show()
                else:
                    QMessageBox.warning(self, 'Error', 'Contraseña incorrecta.')
            else:
                QMessageBox.warning(self, 'Error', 'Datos incorrectos.')
                
        except Exception as e:
            log(e, "error")
            QMessageBox.critical(self, 'Error', f'Ocurrió un error: {str(e)}')

def main():
    # Iniciar la aplicación
    app = QApplication(sys.argv)
    ventana = ClaseLogin()  # Crear la ventana de login
    ventana.show()  # Mostrar la ventana de login
    app.exec()  # Iniciar el loop de eventos

if __name__ == "__main__":
    main()
