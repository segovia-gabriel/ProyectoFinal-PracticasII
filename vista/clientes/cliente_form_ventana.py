from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QDialog

RUTA_UI = Path(__file__).resolve().parent / "cliente_form.ui"


class DialogoCliente(QDialog):
    def __init__(self, controlador, cliente=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.cliente_id = cliente["id"] if cliente else None
        self.mensaje_exito = ""

        # No dejar elegir una fecha de nacimiento futura.
        self.dateEdit_nacimiento.setMaximumDate(QDate.currentDate())

        # Nombre y apellido: se impide tipear numeros directamente (el validador
        # solo deja pasar caracteres que no sean digitos). Igual el controlador
        # lo revalida antes de guardar.
        sin_numeros = QRegularExpressionValidator(QRegularExpression(r"[^0-9]*"))
        self.lineEdit_nombre.setValidator(sin_numeros)
        self.lineEdit_apellido.setValidator(sin_numeros)
        # Telefono: solo digitos y separadores simples (- + espacio), hasta 20.
        solo_telefono = QRegularExpressionValidator(QRegularExpression(r"[0-9+\- ]{0,20}"))
        self.lineEdit_telefono.setValidator(solo_telefono)

        if cliente:
            self.setWindowTitle("Editar cliente")
            self.label_titulo.setText("Editar cliente")
            self.lineEdit_nombre.setText(cliente["nombre"])
            self.lineEdit_apellido.setText(cliente["apellido"])
            self.lineEdit_dni.setText(cliente["dni"])
            fn = cliente["fecha_nacimiento"]
            self.dateEdit_nacimiento.setDate(QDate(fn.year, fn.month, fn.day))
            self.lineEdit_direccion.setText(cliente["direccion"] or "")
            self.lineEdit_telefono.setText(cliente["telefono"] or "")

        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def guardar(self):
        exito, mensaje = self.controlador.guardar(
            self.cliente_id,
            self.lineEdit_nombre.text(),
            self.lineEdit_apellido.text(),
            self.lineEdit_dni.text(),
            self.dateEdit_nacimiento.date().toPyDate(),
            self.lineEdit_direccion.text(),
            self.lineEdit_telefono.text(),
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
