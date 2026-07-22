import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.uic import loadUi
from database.conexion import Database
from error.logger import log
from views.session import UserSession

class EliminarPelicula(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('ui\\eliminarPelicula.ui', self)  
        
        self.db = Database()
        self.cargar_peliculas()
        self.btnAceptar_eliminar.clicked.connect(self.eliminar_pelicula)
        self.btnCancelar_eliminar.clicked.connect(self.close)
        self.accion="Elimino una Pelicula"

    def cargar_peliculas(self):
        """Carga las películas desde la base de datos en el QComboBox."""
        try:
            peliculas = self.db.obtener_peliculas()  # Asegúrate de llamar correctamente al método
            self.comboBoxPelicula_eliminar.clear()  # Limpiar el QComboBox antes de cargar nuevamente
            for pelicula in peliculas:
                self.comboBoxPelicula_eliminar.addItem(pelicula[1], pelicula[0])  # (nombre, id)
        except Exception as e:
            log(e, "error")
            QMessageBox.warning(self, 'Error', f"Error al cargar películas: {e}")


    def eliminar_pelicula(self):
        """Elimina la película seleccionada de la base de datos."""
        pelicula_id = self.comboBoxPelicula_eliminar.currentData()  # Obtiene el ID de la película seleccionada
        pelicula_nombre = self.comboBoxPelicula_eliminar.currentText()  # Obtiene el nombre de la película seleccionada
        
        if pelicula_id:
            # Pregunta al usuario si está seguro
            respuesta = QMessageBox.question(
                self,
                'Confirmar eliminación',
                f"¿Estás seguro de que deseas eliminar la película '{pelicula_nombre}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            # Si el usuario confirma la eliminación
            if respuesta == QMessageBox.Yes:
                try:
                    sesion= UserSession()
                    id_user = sesion.get_user_id()
                    self.db.eliminar_pelicula(pelicula_id)
                    self.db.eliminar_generos_pelicula(pelicula_id)
                    QMessageBox.information(self, 'Éxito', 'La película ha sido eliminada exitosamente.')
                    self.db.registrar_historial_usuario(id_user,self.accion)
                    self.close()
                except Exception as e:
                    log(e, "error")
                    QMessageBox.warning(self, 'Error', f"Error al eliminar película: {e}")
            else:
                # Si el usuario cancela la operación
                QMessageBox.information(self, 'Cancelado', 'La eliminación ha sido cancelada.')
        else:
            QMessageBox.warning(self, 'Advertencia', 'Por favor, selecciona una película.')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EliminarPelicula()
    window.show()
    sys.exit(app.exec_())
