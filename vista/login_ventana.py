import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication

from controlador.login_controlador import LoginControlador
from utilidades.logger import registrar

# La ruta al .ui la calculo desde este archivo asi abre corriendo desde
# cualquier carpeta.
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

        # Login de tamano fijo: no se agranda ni se estira. El .ui ya trae
        # min == max; setFixedSize lo refuerza y lo deja bien claro en el codigo.
        self.setFixedSize(420, 420)
        self._centrar_en_pantalla()

        self.controlador = LoginControlador()
        self.label_error.setText("")

        self.pushButton_ingresar.clicked.connect(self.ingresar)
        # Enter en el usuario pasa a la contrasena y Enter ahi envia el formulario.
        self.lineEdit_usuario.returnPressed.connect(self.lineEdit_contrasena.setFocus)
        self.lineEdit_contrasena.returnPressed.connect(self.ingresar)

    def _centrar_en_pantalla(self):
        # Centro la ventana chica en la pantalla disponible (descontando el Dock y
        # la barra de menu en Mac). Lo hago por codigo porque el .ui no puede
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
            # El error se muestra en la misma pantalla (no en un cartel aparte) y
            # marco los campos en rojo para que se note.
            self.label_error.setText(mensaje)
            self._marcar_error(True)
            self.lineEdit_contrasena.clear()
            self.lineEdit_contrasena.setFocus()
            return

        self.label_error.setText("")
        self._marcar_error(False)

        # Login OK: abro la ventana principal y cierro la de login.
        from vista.principal_ventana import VentanaPrincipal

        # showMaximized (no show): la ventana de trabajo ocupa toda la pantalla
        # pero sigue siendo una ventana (conserva la barra de titulo y los bordes).
        # El login queda chico y centrado.
        self.ventana_principal = VentanaPrincipal()
        self.ventana_principal.showMaximized()
        self.close()

    def _marcar_error(self, hay_error):
        # Prende o apaga la property dinamica 'error' que style.css usa para
        # pintar el borde rojo. Despues de cambiar la property hay que repolish
        # para que Qt vuelva a aplicar la hoja de estilos.
        for campo in (self.lineEdit_usuario, self.lineEdit_contrasena):
            campo.setProperty("error", hay_error)
            campo.style().unpolish(campo)
            campo.style().polish(campo)
