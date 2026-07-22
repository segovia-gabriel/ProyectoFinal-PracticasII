import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.uic import loadUi
from database.conexion import Database
from error.logger import log
from views.session import UserSession

class EliminarUsuario(QMainWindow):
    def __init__(self):
        super(EliminarUsuario, self).__init__()
        loadUi("ui\\eliminarUsuario.ui", self)

        # Llenar el comboBox con los usuarios desde la base de datos
        self.cargar_usuarios()
        self.btnAceptar_eliminar.clicked.connect(self.eliminar_usuario)
        self.btnCancelar_eliminar.clicked.connect(self.close)
        self.accion="Elimino un Usuario"

    def cargar_usuarios(self):
        """Carga los usuarios en el comboBox desde la base de datos."""
        try:
            database = Database()
            usuarios = database.obtener_usuarios()  # Obtener todos los usuarios

            # Limpiar el comboBox
            self.comboBoxUsuario_eliminar.clear()

            # Añadir los usuarios al comboBox
            for usuario in usuarios:
                id_usuario = usuario[0]  
                nombre_usuario = usuario[1] 
                self.comboBoxUsuario_eliminar.addItem(nombre_usuario, (id_usuario, nombre_usuario))

        except Exception as e:
            log(e, "error")
            QMessageBox.critical(self, 'Error', 'No se pudo cargar la lista de usuarios.')

    def eliminar_usuario(self):
        """Elimina el usuario seleccionado en el comboBox."""
        # Obtener el ID y el nombre del usuario seleccionado
        data = self.comboBoxUsuario_eliminar.currentData()

        if data:
            user_id, user_name = data

            reply = QMessageBox.question(self, 'Confirmar eliminación',
                                            f"¿Estás seguro de que deseas eliminar al usuario: {user_name}?",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                try:
                    database = Database()
                    sesion= UserSession()
                    id_user = sesion.get_user_id()
                    database.eliminar_usuario(user_id)  # Eliminar el usuario de la base de datos
                    QMessageBox.information(self, 'Éxito', f'El usuario "{user_name}" ha sido eliminado correctamente.')
                    database.registrar_historial_usuario(id_user,self.accion)
                    
                    #Cerrar
                    self.close()

                except Exception as e:
                    log(e, "error")
                    QMessageBox.critical(self, 'Error', 'No se pudo eliminar el usuario.')
        else:
            QMessageBox.warning(self, 'Advertencia', 'No se ha seleccionado ningún usuario para eliminar.')

def main():
    app = QApplication(sys.argv)
    ventana = EliminarUsuario()
    ventana.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
