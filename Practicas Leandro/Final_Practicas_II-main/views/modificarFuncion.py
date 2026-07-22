import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QDate
from database.conexion import Database
from error.logger import log
from views.session import UserSession

class ModificarFuncion(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui\\modificarFuncion.ui", self)  # Cargar el archivo de interfaz .ui

        self.accion = "Modifico una Funcion"  
        self.db = Database()  

        # Llenar los ComboBox con datos al iniciar
        self.cargar_peliculas_en_combo()
        self.cargar_salas_en_combo()
        self.llenar_comboBox_funciones()

        # Conectar los botones y eventos a sus funciones respectivas
        self.comboBox_funciones.currentIndexChanged.connect(self.cargar_datos_funcion)
        self.comboBox_sala.currentIndexChanged.connect(self.actualizar_horas)
        self.btn_aceptar.clicked.connect(self.modificar_funcion)
        self.btn_cancelar.clicked.connect(self.close)

    def cargar_peliculas_en_combo(self):
        """Carga las películas desde la base de datos al comboBox."""
        try:
            peliculas = self.db.obtener_peliculas()  # Obtener lista de películas
            self.comboBox_pelicula.clear()
            self.comboBox_pelicula.addItem("Seleccionar Película", None)  # Opción predeterminada

            # Agregar cada película al comboBox
            for pelicula in peliculas:
                self.comboBox_pelicula.addItem(pelicula[1], pelicula[0])
        except Exception as e:
            log(e, "error")  # Registrar el error
            QMessageBox.critical(self, 'Error', 'No se pudo cargar la lista de películas.')

    def cargar_salas_en_combo(self):
        """Carga las salas desde la base de datos al comboBox."""
        try:
            salas = self.db.obtener_salas()  # Obtener lista de salas
            self.comboBox_sala.clear()
            self.comboBox_sala.addItem("Seleccionar Sala", None)  # Opción predeterminada

            # Agregar cada sala al comboBox
            for sala in salas:
                self.comboBox_sala.addItem(sala[1], sala[0])
        except Exception as e:
            log(e, "error")  # Registrar el error
            QMessageBox.critical(self, 'Error', 'No se pudo cargar la lista de salas.')

    def llenar_comboBox_funciones(self):
        """Llena el comboBox con funciones desde la base de datos."""
        funciones = self.db.obtener_funciones()  # Obtener lista de funciones
        self.comboBox_funciones.clear()
        self.comboBox_funciones.addItem("Seleccionar Función", None)  # Opción predeterminada

        # Agregar cada función al comboBox con una descripción detallada
        for funcion in funciones:
            descripcion = f"Función: {funcion[0]} - Fecha y Hora: {funcion[2]} - Sala: {funcion[3]}"
            self.comboBox_funciones.addItem(descripcion, funcion[0])

    def cargar_datos_funcion(self):
        """Carga los datos de la función seleccionada en los campos correspondientes."""
        funcion_id = self.comboBox_funciones.currentData()  # Obtener ID de la función seleccionada

        if funcion_id is None:
            # Limpiar los campos si no hay función seleccionada
            self.comboBox_pelicula.setCurrentIndex(0)
            self.comboBox_sala.setCurrentIndex(0)
            self.Fecha.setDate(QDate.currentDate())
            self.comboBox_Hora.clear()
            return

        # Obtener detalles de la función seleccionada por ID
        funcion = self.db.obtener_funcion_por_id(funcion_id)
        if funcion:
            id_pelicula, fecha_hora, id_sala, precio = funcion[1], funcion[2], funcion[3], funcion[4]

            # Seleccionar la película y sala correspondientes en los ComboBox
            index_pelicula = self.comboBox_pelicula.findData(id_pelicula)
            if index_pelicula != -1:
                self.comboBox_pelicula.setCurrentIndex(index_pelicula)

            index_sala = self.comboBox_sala.findData(id_sala)
            if index_sala != -1:
                self.comboBox_sala.setCurrentIndex(index_sala)

            # Establecer la fecha, hora y precio en los campos correspondientes
            self.Fecha.setDate(fecha_hora.date())
            self.comboBox_Hora.setCurrentText(fecha_hora.time().strftime("%H:%M"))
            self.Precio.setValue(precio)

    def actualizar_horas(self):
        """Actualiza las horas disponibles según la sala seleccionada."""
        idSala = self.comboBox_sala.currentData()
        self.comboBox_Hora.clear()  # Limpiar las horas previas

        if idSala is None:
            return

        # Definir horarios según la sala seleccionada
        horarios = ["10:00", "13:00", "16:00"] if idSala == 0 else ["11:00", "14:00", "17:00"]
        self.comboBox_Hora.addItems(horarios)

    def modificar_funcion(self):
        """Modifica la función seleccionada en la base de datos."""
        funcion_id = self.comboBox_funciones.currentData()

        if funcion_id is None:
            QMessageBox.warning(self, "Advertencia", "Selecciona una función para modificar.")
            return

        # Obtener los datos de la función desde los campos
        id_pelicula = self.comboBox_pelicula.currentData()
        id_sala = self.comboBox_sala.currentData()
        fecha = self.Fecha.date().toString("yyyy-MM-dd")
        hora = self.comboBox_Hora.currentText()
        fecha_hora = f"{fecha} {hora}:00"  # Formato de fecha y hora completo
        precio = self.Precio.value()

        # Validar si la fecha de la función está dentro del rango de inicio y fin de la película
        try:
            peliculas = self.db.obtener_peliculas()
            pelicula_seleccionada = next(p for p in peliculas if p[0] == id_pelicula)
            fecha_inicio = QDate.fromString(str(pelicula_seleccionada[6]), "yyyy-MM-dd")
            fecha_fin = QDate.fromString(str(pelicula_seleccionada[7]), "yyyy-MM-dd")
            fecha_funcion = self.Fecha.date()

            if fecha_funcion < fecha_inicio or fecha_funcion > fecha_fin:
                QMessageBox.warning(self, "Advertencia", "La fecha de la función está fuera del rango permitido para la película.")
                return
        except StopIteration:
            QMessageBox.warning(self, "Advertencia", "No se pudo verificar el rango de fechas de la película.")
            return

        # Validar si existe otra función en la misma sala y hora (excluyendo la actual)
        if self.db.funcion_ya_existe(fecha_hora, id_sala, funcion_id):
            QMessageBox.warning(self, "Advertencia", "Ya existe una función en esta sala y hora.")
            return

        # Validar si ya hay tres funciones en la misma sala en el mismo día
        if self.db.contar_funciones_por_dia(fecha, id_sala) >= 3:
            QMessageBox.warning(self, "Advertencia", "No se pueden agregar más de tres funciones en esta sala en un día.")
            return

        try:
            # Obtener el ID del usuario de la sesión y actualizar la función
            sesion = UserSession()
            id_user = sesion.get_user_id()
            self.db.actualizar_funcion(funcion_id, id_pelicula, fecha_hora, id_sala, precio)

            # Mostrar mensaje de éxito, actualizar el comboBox y registrar la acción
            QMessageBox.information(self, "Éxito", "Función modificada correctamente.")
            self.llenar_comboBox_funciones()
            self.db.registrar_historial_usuario(id_user, self.accion)
            self.close()
        except Exception as e:
            log(e, "error")  # Registrar el error
            QMessageBox.critical(self, "Error", f"No se pudo modificar la función: {e}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ventana = ModificarFuncion()
    ventana.show()
    sys.exit(app.exec_())