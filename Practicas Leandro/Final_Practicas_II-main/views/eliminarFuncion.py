import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
from database.conexion import Database
from error.logger import log
from views.session import UserSession

class EliminarFuncion(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui\\eliminarFuncion.ui", self)  
        self.accion="Elimino una Funcion"
        self.db = Database()
        
        # Llenar el QComboBox al iniciar
        self.llenar_comboBox()

        # Conectar los botones a sus funciones
        self.btnAceptar_eliminar.clicked.connect(self.eliminar_funcion)
        self.btnCancelar_eliminar.clicked.connect(self.close)

    def llenar_comboBox(self):
        """Llena el comboBox con funciones desde la base de datos."""
        funciones = self.db.obtener_funciones()
        self.comboBoxEliminar_Funcion.clear()
        for funcion in funciones:
            # Suponiendo que la tupla 'funcion' tiene el formato: (IdFunciones, IdPelicula, Fecha_hora, IdSala, Precio)
            descripcion = f"Función: {funcion[0]} - Fecha y Hora: {funcion[2]} - Sala: {funcion[3]}"
            self.comboBoxEliminar_Funcion.addItem(descripcion, funcion[0])  # Agrega el IdFunciones como data asociada

    def eliminar_funcion(self):
        """Elimina la función seleccionada de la base de datos."""
        funcion_id = self.comboBoxEliminar_Funcion.currentData()

        # Advertencia si no se selecciona una función
        if funcion_id is None:
            QMessageBox.warning(self, "Advertencia", "Selecciona una función para eliminar.")
            return

        # Primera confirmación de eliminación
        reply = QMessageBox.question(self, "Confirmar eliminación",
                                     "¿Estás seguro de que deseas eliminar la función seleccionada?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Segunda confirmación de eliminación
            second_reply = QMessageBox.question(self, "Confirmación final",
                                                "Esta acción es irreversible. ¿Seguro que deseas continuar?",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if second_reply == QMessageBox.Yes:
                try:
                    sesion= UserSession()
                    id_user = sesion.get_user_id()
                    self.db.eliminar_funcion(funcion_id)
                    QMessageBox.information(self, "Éxito", "Función eliminada correctamente.")
                    self.comboBoxEliminar_Funcion.clear()
                    self.db.registrar_historial_usuario(id_user,self.accion)
                    self.close()

                except Exception as e:
                    log(e, "error")
                    QMessageBox.critical(self, "Error", f"No se pudo eliminar la función: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ventana = EliminarFuncion()
    ventana.show()
    sys.exit(app.exec_())
