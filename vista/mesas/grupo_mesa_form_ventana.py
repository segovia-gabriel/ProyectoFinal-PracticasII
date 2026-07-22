"""
Formulario modal de alta/edicion de grupo de mesa (nombre + valor de 2 horas).
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

RUTA_UI = Path(__file__).resolve().parent / "grupo_mesa_form.ui"


class DialogoGrupoMesa(QDialog):
    def __init__(self, controlador, grupo=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.grupo_id = grupo["id"] if grupo else None
        self.mensaje_exito = ""

        if grupo:
            self.setWindowTitle("Editar grupo de mesa")
            self.label_titulo.setText("Editar grupo de mesa")
            self.lineEdit_nombre.setText(grupo["nombre"])
            self.doubleSpinBox_valor.setValue(float(grupo["valor"]))

        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def guardar(self):
        exito, mensaje = self.controlador.guardar_grupo(
            self.grupo_id,
            self.lineEdit_nombre.text(),
            self.doubleSpinBox_valor.value(),
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
