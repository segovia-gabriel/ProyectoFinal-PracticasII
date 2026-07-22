"""
Ventana principal. Muestra el menu lateral y abre cada modulo en su propia
ventana (patron del profesor: se esconde y vuelve al cerrar el modulo). Tambien
maneja el cierre de sesion, que vuelve al login.
"""

import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from utilidades.logger import registrar
from utilidades.sesion import Sesion

RUTA_UI = Path(__file__).resolve().parent / "principal.ui"


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(RUTA_UI, self)
        except FileNotFoundError as error:
            registrar(error, "error")
            QMessageBox.critical(self, "Error", "No se encontró la pantalla principal.")
            sys.exit(1)

        # Tarjeta de perfil arriba del menu: nombre + inicial en el avatar.
        nombre = Sesion().nombre_usuario or ""
        self.label_nombreUsuario.setText(nombre)
        self.label_avatar.setText(nombre[:1].upper() if nombre else "?")

        # Cada boton abre su modulo en su propia ventana (patron del profesor).
        self.pushButton_usuarios.clicked.connect(self.abrir_usuarios)
        self.pushButton_historial.clicked.connect(self.abrir_historial)
        self.pushButton_mesas.clicked.connect(self.abrir_mesas)
        self.pushButton_clientes.clicked.connect(self.abrir_clientes)
        self.pushButton_menu.clicked.connect(self.abrir_menu)
        self.pushButton_reservas.clicked.connect(self.abrir_reservas)
        self.pushButton_consumo.clicked.connect(self.abrir_consumo)
        self.pushButton_estadisticas.clicked.connect(self.abrir_estadisticas)

        self.pushButton_cerrarSesion.clicked.connect(self.cerrar_sesion)

    def _abrir_modulo(self, ventana_modulo):
        # Patron del profesor: escondo la principal y muestro la del modulo;
        # al cerrarse esa ventana, su closeEvent vuelve a mostrar esta.
        self.hide()
        self.ventana_modulo = ventana_modulo   # se guarda para que no la borre el GC
        self.ventana_modulo.show()

    def abrir_usuarios(self):
        from vista.usuarios.usuarios_ventana import VentanaUsuarios

        self._abrir_modulo(VentanaUsuarios(self))

    def abrir_historial(self):
        from vista.historial.historial_ventana import VentanaHistorial

        self._abrir_modulo(VentanaHistorial(self))

    def abrir_mesas(self):
        from vista.mesas.mesas_ventana import VentanaMesas

        self._abrir_modulo(VentanaMesas(self))

    def abrir_clientes(self):
        from vista.clientes.clientes_ventana import VentanaClientes

        self._abrir_modulo(VentanaClientes(self))

    def abrir_menu(self):
        from vista.menu.menu_ventana import VentanaMenu

        self._abrir_modulo(VentanaMenu(self))

    def abrir_reservas(self):
        from vista.reservas.reservas_ventana import VentanaReservas

        self._abrir_modulo(VentanaReservas(self))

    def abrir_consumo(self):
        from vista.consumo.consumo_ventana import VentanaConsumo

        self._abrir_modulo(VentanaConsumo(self))

    def abrir_estadisticas(self):
        from vista.estadisticas.estadisticas_ventana import VentanaEstadisticas

        self._abrir_modulo(VentanaEstadisticas(self))

    def cerrar_sesion(self):
        Sesion().cerrar()
        from vista.login_ventana import VentanaLogin

        self.ventana_login = VentanaLogin()
        self.ventana_login.show()
        self.close()
