import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from datetime import datetime
from database.conexion import Database  
from error.logger import log
from PyQt5.uic import loadUi  
from views.password import generar_password
from views.session import UserSession
class ModificarUsuario(QMainWindow):
    def __init__(self, parent=None):
        super(ModificarUsuario, self).__init__(parent)
        loadUi("ui\\modificarUsuario.ui", self)

        # Inicializar base de datos
        self.db = Database()

        # Conectar el botón de guardar a la función para agregar usuario
        self.btnCancelar_Modificar.clicked.connect(self.close)
        self.btnAceptar_Modificar.clicked.connect(self.modificar_usuario)
        self.accion="Modifico un Usuario"

        # Configurar el valor por defecto del comboBox
        self.comboBoxUsuario.setCurrentText("Administrador")

        # Conectar eventos
        self.comboBoxUsuario_2.currentIndexChanged.connect(self.cargar_datos_usuario)

        # Cargar usuarios en el combo box
        self.load_users()

    def load_users(self):
        """Carga la lista de usuarios en el combo box."""
        try:
            usuarios = self.db.obtener_usuarios()
            for usuario in usuarios:
                self.comboBoxUsuario_2.addItem(f"{usuario[1]} - {usuario[3]}", usuario[0]) 
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Error al cargar usuarios: {str(e)}")

    def cargar_datos_usuario(self):
        """Carga los datos del usuario seleccionado en los campos."""
        user_id = self.comboBoxUsuario_2.currentData()  # Obtener el ID del usuario seleccionado

        if user_id:
            try:
                usuario = self.db.obtener_usuario_por_id(user_id)  # Método obtener_usuario en tu database.py

                if usuario:
                    self.lineEdit_Nombre.setText(usuario[1])  # Nombre de usuario
                    self.lineEdit_Contrasenia.setText(usuario[2])  # Contraseña
                    rol = usuario[3]
                    if rol == 'Administrador':
                        self.comboBoxUsuario.setCurrentIndex(0)
                    elif rol == 'Empleado':
                        self.comboBoxUsuario.setCurrentIndex(1)

            except Exception as e:
                QMessageBox.critical(self, 'Error', f"Error al cargar datos del usuario: {str(e)}")

    def modificar_usuario(self):
        """Modifica los datos del usuario seleccionado."""
        user_id = self.comboBoxUsuario_2.currentData()
        nuevo_nombre = self.lineEdit_Nombre.text()
        nueva_contrasena = self.lineEdit_Contrasenia.text()
        nuevo_rol = self.comboBoxUsuario.currentText()
        fecha_modificacion = datetime.now()
        

        if not nuevo_nombre or not nueva_contrasena or not nuevo_rol:
            QMessageBox.warning(self, 'Advertencia', 'Todos los campos son obligatorios.')
            return

        try:
            contrasenia_encriptada=generar_password(nueva_contrasena)
            sesion= UserSession()
            id_user = sesion.get_user_id()
            self.db.modificar_usuario(user_id, nuevo_nombre, contrasenia_encriptada, nuevo_rol, fecha_modificacion)
            QMessageBox.information(self, 'Éxito', 'Usuario modificado correctamente.')
            self.db.registrar_historial_usuario(id_user,self.accion)
            self.close()
        except Exception as e:
            log(e, "error")
            QMessageBox.critical(self, 'Error', f"Error al modificar usuario: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModificarUsuario()
    window.show()
    sys.exit(app.exec_())
