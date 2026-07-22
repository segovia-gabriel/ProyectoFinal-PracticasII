import sys
import os
import shutil
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog, QCheckBox, QDialogButtonBox, QVBoxLayout
from database.conexion import Database
from error.logger import log
from datetime import datetime
from views.session import UserSession

# Diálogo para seleccionar géneros
class GenerosPeliculas(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seleccionar Géneros")
        self.seleccionar_generos = []
        layout = QVBoxLayout()
        self.checkboxes = []

        # Cargar géneros desde la base de datos
        try:
            database = Database()
            self.genres = [genre[1] for genre in database.obtener_generos()]
        except Exception as e:
            log(e, "error")
            QMessageBox.critical(self, 'Error', 'No se pudo cargar la lista de géneros.')
            self.genres = []

        # Crear checkboxes para cada género
        for genre in self.genres:
            checkbox = QCheckBox(genre)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        # Botones para aceptar o cancelar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def accept(self):
        self.seleccionar_generos = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
        super().accept()


class AgregarPeliculas(QtWidgets.QWidget):
    def __init__(self):
        super(AgregarPeliculas, self).__init__()
        loadUi('ui\\agregarPelicula.ui', self)  
        
        self.db = Database()
        self.imagenes_dir = 'movies'
        self.imagen_seleccionada = None
        self.accion = "Creo una Pelicula"

        # Establecer el QLineEdit como de solo lectura
        self.lineEdit_generos.setReadOnly(True)

        # Crear el directorio de imágenes si no existe
        if not os.path.exists(self.imagenes_dir):
            os.makedirs(self.imagenes_dir)

        # Configurar la fecha actual como fecha por defecto
        fecha_actual = QtCore.QDate.currentDate()
        self.dateEdit_estreno_mundial.setDate(fecha_actual)
        self.dateEdit_fecha_inicio.setDate(fecha_actual)
        self.dateEdit_fecha_fin.setDate(fecha_actual)

        # Habilitar la selección de fecha mediante un calendario
        self.dateEdit_estreno_mundial.setCalendarPopup(True)
        self.dateEdit_fecha_inicio.setCalendarPopup(True)
        self.dateEdit_fecha_fin.setCalendarPopup(True)

        # Conectar los botones a funciones
        self.btn_cancelar.clicked.connect(self.cancelar)  
        self.btn_aceptar.clicked.connect(self.aceptar)   
        self.btn_seleccionar_pelicula.clicked.connect(self.seleccionar_pelicula)  
        self.btn_generos.clicked.connect(self.abrir_seleccion_generos)  

    def cancelar(self):
        self.close()

    def aceptar(self):
        # Obtener los valores de los campos
        nombre_pelicula = self.nombre_pelicula.text()
        resumen = self.textEdit_Resumen.toPlainText()
        pais_origen = self.lineEdit_pais_origen.text()
        fecha_estreno = self.dateEdit_estreno_mundial.date().toString("yyyy-MM-dd")
        fecha_inicio = self.dateEdit_fecha_inicio.date()
        fecha_fin = self.dateEdit_fecha_fin.date()
        duracion = self.duracion.value()
        clasificacion = self.clasificacion.currentText()
        generos = self.lineEdit_generos.text().split(", ")  # Obtener géneros seleccionados como lista

        # Validar que la fecha de inicio sea menor que la fecha de fin
        if fecha_inicio >= fecha_fin:
            self.mostrar_advertencia("La fecha de inicio debe ser menor que la fecha de fin.")
            return

        # Verificar si los campos están vacíos
        if not nombre_pelicula:
            self.mostrar_advertencia("El campo 'Nombre de la película' está vacío.")
            return
        if not resumen:
            self.mostrar_advertencia("El campo 'Resumen' está vacío.")
            return
        if not pais_origen:
            self.mostrar_advertencia("El campo 'País de Origen' está vacío.")
            return
        if not fecha_estreno:
            self.mostrar_advertencia("El campo 'Fecha de Estreno' está vacío.")
            return
        if duracion < 60:
            self.mostrar_advertencia("La duración debe ser como mínimo 60.")
            return
        if not self.imagen_seleccionada:
            self.mostrar_advertencia("No se ha seleccionado ninguna imagen.")
            return
        if not self.lineEdit_generos.text():
            self.mostrar_advertencia("No se ha seleccionado ningún género.")
            return

        # Guardar la imagen seleccionada
        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_con_fecha_hora = f"{nombre_pelicula}-{fecha_hora_actual}"
        nombre_archivo_guardado = None

        if self.imagen_seleccionada:
            nombre_archivo_imagen = os.path.basename(self.imagen_seleccionada)
            extension = os.path.splitext(nombre_archivo_imagen)[1]
            nueva_ruta_imagen = os.path.join(self.imagenes_dir, f"{nombre_con_fecha_hora}{extension}")
            shutil.copy2(self.imagen_seleccionada, nueva_ruta_imagen)
            nombre_archivo_guardado = f"{nombre_con_fecha_hora}{extension}"

        # Insertar la película en la base de datos
        try:
            sesion = UserSession()
            id_user = sesion.get_user_id()
            # Insertar la película y obtener su ID
            id_pelicula = self.db.insertar_pelicula(
                nombre_pelicula, resumen, pais_origen, fecha_estreno, duracion, clasificacion, nombre_archivo_guardado, 
                fecha_inicio.toString("yyyy-MM-dd"), fecha_fin.toString("yyyy-MM-dd")
            )

            if id_pelicula:
                # Insertar los géneros seleccionados
                for genero in generos:
                    id_genero = self.db.obtener_id_genero_por_nombre(genero)
                    if id_genero:
                        self.db.insertar_generos(id_pelicula, id_genero)
                    else:
                        log(f"No se encontró el género {genero} en la base de datos.", "error")
                        QMessageBox.warning(self, 'Advertencia', f'El género {genero} no se pudo asociar a la película.')

                QMessageBox.information(self, 'Éxito', 'La película ha sido guardada exitosamente.')
            else:
                log("Error: No se pudo obtener el ID de la película después de la inserción.", "error")
                QMessageBox.critical(self, 'Error', 'No se pudo guardar la película correctamente.')
            
            self.db.registrar_historial_usuario(id_user, self.accion)

        except Exception as e:
            log(e, "error")
            QMessageBox.critical(self, 'Error', f'Ocurrió un error al guardar la película: {e}')

        self.close()

    def mostrar_advertencia(self, mensaje):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(mensaje)
        msg_box.setWindowTitle("Advertencia")
        msg_box.exec_()

    def seleccionar_pelicula(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        archivo_imagen, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)", options=options)
        
        if archivo_imagen:
            self.imagen_seleccionada = archivo_imagen
            pixmap = QtGui.QPixmap(self.imagen_seleccionada)
            self.label_peli.setPixmap(pixmap)
            self.label_peli.setScaledContents(True)

    def abrir_seleccion_generos(self):
        dialog = GenerosPeliculas()
        if dialog.exec_():
            generos_seleccionados = ", ".join(dialog.seleccionar_generos)
            self.lineEdit_generos.setText(generos_seleccionados)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AgregarPeliculas()
    window.show()
    sys.exit(app.exec_())

