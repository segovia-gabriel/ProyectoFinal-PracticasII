from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

RUTA_UI = Path(__file__).resolve().parent / "grupo_menu_form.ui"


class DialogoGrupoMenu(QDialog):
    def __init__(self, controlador, grupo=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.grupo_id = grupo["id"] if grupo else None
        self.mensaje_exito = ""

        if grupo:
            self.setWindowTitle("Editar grupo de menu")
            self.label_titulo.setText("Editar grupo de menu")
            self.lineEdit_nombre.setText(grupo["nombre"])

        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def guardar(self):
        exito, mensaje = self.controlador.guardar_grupo(
            self.grupo_id, self.lineEdit_nombre.text()
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
