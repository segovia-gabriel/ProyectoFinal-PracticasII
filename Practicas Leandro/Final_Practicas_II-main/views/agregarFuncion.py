import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtCore import QDate
from database.conexion import Database
from error.logger import log
from views.session import UserSession

class AgregarFuncion(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('ui\\agregarFuncion.ui', self)
        self.accion="Agrego una Funcion"
        self.db = Database()  # Instancia de la base de datos

        # Conectar botones a funciones
        self.btn_aceptar.clicked.connect(self.aceptar)
        self.btn_cancelar.clicked.connect(self.cancelar)

        # Cargar datos en los comboBox
        self.cargar_peliculas_en_combo()
        self.cargar_salas_en_combo()
        self.comboBox_sala.currentIndexChanged.connect(self.actualizar_horas)

        self.Fecha.setDate(QDate.currentDate())
        self.Fecha.setCalendarPopup(True)

    def cargar_peliculas_en_combo(self):
        """Carga las películas desde la base de datos al comboBox."""
        try:
            peliculas = self.db.obtener_peliculas()
            self.comboBox_pelicula.clear()
            self.comboBox_pelicula.addItem("Seleccionar Película", None)
            for pelicula in peliculas:
                self.comboBox_pelicula.addItem(pelicula[1], pelicula[0])
        except Exception as e:
            log(e, "error")
            QMessageBox.critical(self, 'Error', 'No se pudo cargar la lista de películas.')

    def cargar_salas_en_combo(self):
        """Carga las salas desde la base de datos al comboBox."""
        try:
            salas = self.db.obtener_salas()
            self.comboBox_sala.clear()
            self.comboBox_sala.addItem("Seleccionar Sala", None)
            for sala in salas:
                self.comboBox_sala.addItem(sala[1], sala[0])
        except Exception as e:
            log(e, "error")
            QMessageBox.critical(self, 'Error', 'No se pudo cargar la lista de salas.')

    def actualizar_horas(self):
        """Actualiza las horas disponibles según la sala seleccionada."""
        idSala = self.comboBox_sala.currentData()
        self.comboBox_Hora.clear()
        if idSala is None:
            return
        horarios = ["10:00", "13:00", "16:00"] if idSala == 0 else ["11:00", "14:00", "17:00"]
        self.comboBox_Hora.addItems(horarios)

    # Eliminando la validación redundante de cantidad de funciones por día
    def aceptar(self):
        """Valida y guarda la función en la base de datos."""
        idPelicula = self.comboBox_pelicula.currentData()
        idSala = self.comboBox_sala.currentData()
        fecha = self.Fecha.date().toString("yyyy-MM-dd")
        hora = self.comboBox_Hora.currentText()
        precio = self.Precio.value()

        # Verificación detallada de cada campo
        if idPelicula is None:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar una película.")
            return

        if idSala is None:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar una sala.")
            return

        if not hora:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar una hora.")
            return

        if precio <= 0:
            QMessageBox.warning(self, "Advertencia", "El precio debe ser mayor a 0.")
            return

        # Validación de fecha dentro del rango
        try:
            # Obtener la lista de películas desde la base de datos
            peliculas = self.db.obtener_peliculas()

            # Buscar la película seleccionada en el ComboBox, usando el idPelicula seleccionado
            pelicula_seleccionada = next(p for p in peliculas if p[0] == idPelicula)

            # Extraer la fecha de inicio y fin de la película seleccionada usando los índices adecuados
            fecha_inicio = QDate.fromString(str(pelicula_seleccionada[6]), "yyyy-MM-dd")  # Índice 6 corresponde a FechaInicio
            fecha_fin = QDate.fromString(str(pelicula_seleccionada[7]), "yyyy-MM-dd")  # Índice 7 corresponde a FechaFin

            # Obtener la fecha seleccionada para la función
            fecha_funcion = self.Fecha.date()

            # Verificar si la fecha de la función está dentro del rango de inicio y fin de la película
            if fecha_funcion < fecha_inicio or fecha_funcion > fecha_fin:
                QMessageBox.warning(self, "Advertencia", "La fecha de la función está fuera del rango permitido para la película.")
                return
        except StopIteration:
            # Manejar el caso en el que la película seleccionada no se encuentra en la lista
            QMessageBox.warning(self, "Advertencia", "No se pudo verificar el rango de fechas de la película.")
            return


        fecha_hora = f"{fecha} {hora}:00"

        # Validación: verificar si ya existe una función en esa sala y hora
        if self.db.funcion_ya_existe(fecha_hora, idSala):
            QMessageBox.warning(self, "Advertencia", "Ya existe una función en esta sala y hora.")
            return

        # Intentar insertar la función
        try:
            sesion = UserSession()
            id_user = sesion.get_user_id()
            self.db.insertar_funcion(idPelicula, fecha_hora, idSala, precio)
            QMessageBox.information(self, "Éxito", "Función agregada correctamente.")
            self.db.registrar_historial_usuario(id_user, self.accion)
            self.close()
        except Exception as e:
            log(e, "error")
            QMessageBox.critical(self, 'Error', f"No se pudo agregar la función: {e}")


    def cancelar(self):
        """Cierra la ventana."""
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AgregarFuncion()
    window.show()
    sys.exit(app.exec_())
