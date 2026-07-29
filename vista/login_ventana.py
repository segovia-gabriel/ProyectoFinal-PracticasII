"""
Ventana de login. Solo UI: carga el .ui, conecta el boton al controlador y
muestra el resultado. La logica (verificar contrasena, registrar historial)
vive en LoginControlador.
"""

import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication

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
            QMessageBox.critical(self, "Error", "No se encontro la pantalla de login.")
            sys.exit(1)

        # Login de tamano fijo: no se agranda, no se redimensiona y el boton de
        # maximizar queda inhabilitado. setFixedSize alcanza en las tres plataformas
        # (el .ui ya trae min == max, esto lo refuerza y lo deja claro en codigo).
        self.setFixedSize(420, 420)
        self._centrar_en_pantalla()

        self.controlador = LoginControlador()
        self.label_error.setText("")

        # Conexion de senales a mano (no autogeneradas), como en sistema_ejemplo.
        self.pushButton_ingresar.clicked.connect(self.ingresar)
        # Enter en el usuario pasa a la contrasena y Enter ahi envia el formulario.
        self.lineEdit_usuario.returnPressed.connect(self.lineEdit_contrasena.setFocus)
        self.lineEdit_contrasena.returnPressed.connect(self.ingresar)

    def _centrar_en_pantalla(self):
        # Centra la ventana chica en la pantalla disponible (descuenta el Dock y
        # la barra de menu en Mac). Se hace por codigo porque el .ui no puede
        # centrar respecto de la pantalla, solo respecto de un padre.
        pantalla = QApplication.primaryScreen().availableGeometry()
        geometria = self.frameGeometry()
        geometria.moveCenter(pantalla.center())
        self.move(geometria.topLeft())

    def ingresar(self):
        nombre_usuario = self.lineEdit_usuario.text().strip()
        contrasena = self.lineEdit_contrasena.text()

        exito, mensaje = self.controlador.intentar_ingresar(nombre_usuario, contrasena)

        if not exito:
            # El error se muestra en la misma pantalla (no solo en un cartel) y
            # se marcan los campos en rojo, que es la retroalimentacion visual
            # que pide la catedra.
            self.label_error.setText(mensaje)
            self._marcar_error(True)
            self.lineEdit_contrasena.clear()
            self.lineEdit_contrasena.setFocus()
            return

        self.label_error.setText("")
        self._marcar_error(False)

        # Login OK: abrimos la ventana principal y cerramos la de login.
        from vista.principal_ventana import VentanaPrincipal

        # showMaximized (no show): la ventana de trabajo ocupa toda la pantalla
        # pero sigue siendo ventana (mantiene barra de titulo y bordes). El login
        # queda chico y centrado.
        self.ventana_principal = VentanaPrincipal()
        self.ventana_principal.showMaximized()
        self.close()

    def _marcar_error(self, hay_error):
        # Prende o apaga la property dinamica 'error' que style.css usa para
        # pintar el borde rojo. Hay que repolish para que Qt vuelva a aplicar
        # la hoja de estilos despues de cambiar la property.
        for campo in (self.lineEdit_usuario, self.lineEdit_contrasena):
            campo.setProperty("error", hay_error)
            campo.style().unpolish(campo)
            campo.style().polish(campo)
