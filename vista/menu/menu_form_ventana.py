from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QFileDialog

RUTA_UI = Path(__file__).resolve().parent / "menu_form.ui"
# La raiz del proyecto para resolver la ruta relativa que guardo de la imagen.
RAIZ = Path(__file__).resolve().parents[2]


class DialogoItemMenu(QDialog):
    def __init__(self, controlador, item=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.item_id = item["id"] if item else None
        self.mensaje_exito = ""
        self.imagen_origen = None                       # ruta nueva elegida (o None)
        self.imagen_actual = item["imagen_path"] if item else None

        exito, grupos = self.controlador.listar_grupos_combo()
        if exito:
            for grupo_id, nombre in grupos:
                self.comboBox_grupo.addItem(nombre, grupo_id)

        if item:
            self.setWindowTitle("Editar item de menu")
            self.label_titulo.setText("Editar item de menu")
            self.lineEdit_nombre.setText(item["nombre"])
            self.plainTextEdit_descripcion.setPlainText(item["descripcion"] or "")
            indice = self.comboBox_grupo.findData(item["grupo_menu_id"])
            if indice >= 0:
                self.comboBox_grupo.setCurrentIndex(indice)
            if item["imagen_path"]:
                self._mostrar_preview(RAIZ / item["imagen_path"])
            self._mostrar_aviso_renovacion()

        self.pushButton_imagen.clicked.connect(self.seleccionar_imagen)
        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def _mostrar_aviso_renovacion(self):
        # Avisa, al ver los datos de un item, cuando faltan 10 dias o menos para
        # que venza su precio. El calculo esta en el controlador (el mismo que usa
        # la pantalla de precios); aca solo se muestra.
        aviso = self.controlador.aviso_renovacion(self.item_id)
        if not aviso:
            self.label_aviso.setText("")
            return
        self.label_aviso.setText("⚠ " + aviso)
        self.label_aviso.setProperty("class", "aviso")
        self.label_aviso.style().unpolish(self.label_aviso)
        self.label_aviso.style().polish(self.label_aviso)

    def seleccionar_imagen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Elegir imagen", "", "Imagenes (*.png *.jpg *.jpeg *.bmp)"
        )
        if ruta:
            self.imagen_origen = ruta
            self._mostrar_preview(Path(ruta))

    def _mostrar_preview(self, ruta):
        # Si el archivo no existe o no es imagen valida, se deja el placeholder.
        try:
            pixmap = QPixmap(str(ruta))
            if pixmap.isNull():
                self.label_imagen.setText("Sin imagen")
                return
            self.label_imagen.setPixmap(
                pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        except OSError:
            self.label_imagen.setText("Sin imagen")

    def guardar(self):
        exito, mensaje = self.controlador.guardar_item(
            self.item_id,
            self.lineEdit_nombre.text(),
            self.plainTextEdit_descripcion.toPlainText(),
            self.comboBox_grupo.currentData(),
            self.imagen_origen,
            self.imagen_actual,
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
