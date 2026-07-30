from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

RUTA_UI = Path(__file__).resolve().parent / "usuario_form.ui"


class DialogoUsuario(QDialog):
    def __init__(self, controlador, usuario=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        # usuario None => alta; usuario dict => edicion.
        self.usuario_id = usuario["id"] if usuario else None
        self.mensaje_exito = ""

        # label_ayuda en gris (property "class" que toma el QSS global).
        self.label_ayuda.setProperty("class", "ayuda")

        if usuario:
            self.setWindowTitle("Editar usuario")
            self.label_titulo.setText("Editar usuario")
            self.lineEdit_usuario.setText(usuario["nombre_usuario"])
            # En edicion la contrasena es opcional: vacia = no cambiarla.
            self.label_ayuda.setText("Deja la contrasena vacia para no cambiarla.")

        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def guardar(self):
        exito, mensaje = self.controlador.guardar(
            self.usuario_id,
            self.lineEdit_usuario.text(),
            self.lineEdit_contrasena.text(),
            self.lineEdit_contrasenaRepetir.text(),
        )

        if exito:
            # Se lo guardamos a la ventana de listado para que lo muestre al volver.
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
