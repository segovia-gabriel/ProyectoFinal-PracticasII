"""
Ventana de login. Solo UI: carga el .ui, conecta el boton al controlador y
muestra el resultado. La logica (verificar contrasena, registrar historial)
vive en LoginControlador.
"""

import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox

from controlador.login_controlador import LoginControlador
from utilidades.logger import registrar

# Ruta al .ui calculada desde este archivo, para que abra corriendo desde
# cualquier carpeta (regla dura: pathlib, nunca rutas escritas a mano).
RUTA_UI = Path(__file__).resolve().parent / "login.ui"


class VentanaLogin(QWidget):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(RUTA_UI, self)
        except FileNotFoundError as error:
            registrar(error, "error")
            QMessageBox.critical(self, "Error", "No se encontró la pantalla de login.")
            sys.exit(1)

        self.controlador = LoginControlador()

        # Conexion de senales a mano (no autogeneradas), como en sistema_ejemplo.
        self.pushButton_ingresar.clicked.connect(self.ingresar)
        # Enter en la contrasena tambien envia el formulario, es lo que uno espera.
        self.lineEdit_contrasena.returnPressed.connect(self.ingresar)

    def ingresar(self):
        nombre_usuario = self.lineEdit_usuario.text().strip()
        contrasena = self.lineEdit_contrasena.text()

        exito, mensaje = self.controlador.intentar_ingresar(nombre_usuario, contrasena)

        if not exito:
            QMessageBox.warning(self, "No se pudo ingresar", mensaje)
            return

        # Login OK: abrimos la ventana principal y cerramos la de login.
        from vista.principal_ventana import VentanaPrincipal

        self.ventana_principal = VentanaPrincipal()
        self.ventana_principal.show()
        self.close()
