"""
Ventana principal. Arriba de todo muestra un panel con el resumen del dia
(reservas de hoy, pendientes, ingresos del mes) para que al iniciar sesion la
pantalla diga algo util, y a la izquierda el menu que abre cada modulo en su
propia ventana (patron del profesor: se esconde y vuelve al cerrar el modulo).
Tambien maneja el cierre de sesion, que vuelve al login.
"""

import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QHeaderView, QListWidgetItem, QMainWindow,
                             QMessageBox, QTableWidgetItem)

from controlador.panel_controlador import PanelControlador
from controlador.reservas_controlador import ReservasControlador
from utilidades import formato
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

        self.controlador = PanelControlador()
        # se usa para cambiar la asistencia desde la agenda del panel
        self.reservas_controlador = ReservasControlador()

        # Tarjeta de perfil arriba del menu: nombre + inicial en el avatar.
        nombre = Sesion().nombre_usuario or ""
        self.label_nombreUsuario.setText(nombre)
        self.label_avatar.setText(nombre[:1].upper() if nombre else "?")

        # Las cuatro columnas se reparten el ancho en partes iguales: si solo
        # estirara la del cliente, con la ventana maximizada quedaba un hueco
        # enorme entre el nombre y la mesa.
        self.tableWidget_agenda.verticalHeader().setVisible(False)
        self.tableWidget_agenda.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_agenda.setToolTip(
            "Doble clic en una reserva para marcar la asistencia del cliente.")

        # Los avisos son textos largos: se cortan en varias lineas dentro del
        # ancho del panel, sin barra de scroll horizontal.
        self.listWidget_avisos.setWordWrap(True)
        self.listWidget_avisos.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listWidget_avisos.setToolTip(
            "Doble clic en un pendiente para resolverlo.")

        # Cada boton abre su modulo en su propia ventana (patron del profesor).
        self.pushButton_salon.clicked.connect(self.abrir_salon)
        self.pushButton_usuarios.clicked.connect(self.abrir_usuarios)
        self.pushButton_historial.clicked.connect(self.abrir_historial)
        self.pushButton_mesas.clicked.connect(self.abrir_mesas)
        self.pushButton_clientes.clicked.connect(self.abrir_clientes)
        self.pushButton_menu.clicked.connect(self.abrir_menu)
        self.pushButton_reservas.clicked.connect(self.abrir_reservas)
        self.pushButton_consumo.clicked.connect(self.abrir_consumo)
        self.pushButton_estadisticas.clicked.connect(self.abrir_estadisticas)

        # Doble clic para resolver desde el panel, sin entrar al modulo:
        # en la agenda cambia el estado de asistencia, en los pendientes abre
        # la pantalla que corresponde segun el tipo de aviso.
        self.tableWidget_agenda.doubleClicked.connect(self.cambiar_estado_agenda)
        self.listWidget_avisos.itemDoubleClicked.connect(self.resolver_aviso)

        self.pushButton_actualizar.clicked.connect(self.cargar_panel)
        self.pushButton_cerrarSesion.clicked.connect(self.cerrar_sesion)
        # El panel se carga en showEvent, que corre tanto al abrir la ventana
        # como al volver de un modulo, asi los numeros nunca quedan viejos.

    # ---------- Panel de resumen ----------

    def cargar_panel(self):
        # Encabezado: saludo segun la hora y fecha de hoy en texto largo.
        self.label_titulo.setText(self.controlador.saludo(Sesion().nombre_usuario or ""))
        self.label_fecha.setText(self.controlador.fecha_larga())

        exito, datos = self.controlador.resumen()
        if not exito:
            QMessageBox.warning(self, "Panel principal", datos)
            return

        self.label_valorReservasHoy.setText(str(datos["reservas_hoy"]))
        self.label_valorReservasFuturas.setText(str(datos["reservas_futuras"]))
        self.label_valorClientes.setText(str(datos["clientes"]))
        self.label_valorIngresos.setText(formato.moneda(datos["ingresos_mes"]))

        self._cargar_agenda(datos["agenda"])
        self._cargar_avisos(datos["avisos"])

    def _cargar_agenda(self, filas):
        tabla = self.tableWidget_agenda
        tabla.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            # El id y el estado crudo viajan en la primera celda: los necesita
            # el doble clic para abrir el dialogo de asistencia.
            celda = QTableWidgetItem(fila["horario"])
            celda.setData(Qt.UserRole, fila["id"])
            celda.setData(Qt.UserRole + 1, fila["estado_clave"])
            tabla.setItem(i, 0, celda)
            tabla.setItem(i, 1, QTableWidgetItem(fila["cliente"]))
            tabla.setItem(i, 2, QTableWidgetItem(fila["mesa"]))
            tabla.setItem(i, 3, QTableWidgetItem(fila["estado"]))

        # Si no hay reservas se avisa en el titulo, para no dejar una tabla vacia
        # sin explicacion.
        if filas:
            self.label_subtituloAgenda.setText(f"Agenda de hoy ({len(filas)})")
        else:
            self.label_subtituloAgenda.setText("Agenda de hoy — sin reservas")

    def _cargar_avisos(self, avisos):
        lista = self.listWidget_avisos
        lista.clear()
        if not avisos:
            item = QListWidgetItem("No hay pendientes. Todo al día.")
            item.setTextAlignment(Qt.AlignCenter)
            lista.addItem(item)
            self.label_subtituloAvisos.setText("Pendientes")
            return

        for aviso in avisos:
            item = QListWidgetItem(aviso["texto"])
            # se guarda el aviso entero para saber que abrir en el doble clic
            item.setData(Qt.UserRole, aviso)
            lista.addItem(item)
        self.label_subtituloAvisos.setText(f"Pendientes ({len(avisos)})")

    # ---------- Acciones desde el panel ----------

    def cambiar_estado_agenda(self):
        # Doble clic sobre una reserva de hoy: cambia el estado de asistencia
        # sin tener que entrar al modulo Reservas.
        fila = self.tableWidget_agenda.currentRow()
        if fila < 0:
            return
        celda = self.tableWidget_agenda.item(fila, 0)
        reserva_id = celda.data(Qt.UserRole)
        estado_actual = celda.data(Qt.UserRole + 1)

        from vista.reservas.estado_form_ventana import DialogoEstado

        dialogo = DialogoEstado(estado_actual, parent=self)
        if dialogo.exec_() != QDialog.Accepted:
            return
        exito, mensaje = self.reservas_controlador.cambiar_estado(
            reserva_id, dialogo.estado_elegido())
        if exito:
            QMessageBox.information(self, "Listo", mensaje)
            self.cargar_panel()
        else:
            QMessageBox.warning(self, "Error", mensaje)

    def resolver_aviso(self, item):
        # Doble clic sobre un pendiente: se abre la pantalla donde se resuelve,
        # asi el aviso desaparece del panel apenas se completa.
        aviso = item.data(Qt.UserRole)
        if not aviso:
            return
        if aviso["tipo"] == "consumo":
            self._cargar_consumo_pendiente(aviso["id"])
        elif aviso["tipo"] == "precio":
            self._renovar_precio(aviso["id"])

    def _cargar_consumo_pendiente(self, reserva_id):
        from controlador.consumo_controlador import ConsumoControlador
        from vista.consumo.consumo_form_ventana import DialogoConsumo

        dialogo = DialogoConsumo(ConsumoControlador(), reserva_id=reserva_id, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)
            self.cargar_panel()

    def _renovar_precio(self, item_id):
        # Se abre el historial de precios del item, que es donde se carga el
        # precio nuevo. Al cerrarse, esa ventana vuelve a mostrar esta.
        from controlador.menu_controlador import MenuControlador
        from vista.menu.precios_ventana import VentanaPrecios

        controlador = MenuControlador()
        exito, item = controlador.obtener_item(item_id)
        if not exito or item is None:
            QMessageBox.warning(self, "Error", "No se pudo abrir el ítem de menú.")
            return
        self._abrir_modulo(VentanaPrecios(item, controlador, self))

    # ---------- Navegacion ----------

    def _abrir_modulo(self, ventana_modulo):
        # Patron del profesor: escondo la principal y muestro la del modulo;
        # al cerrarse esa ventana, su closeEvent vuelve a mostrar esta.
        self.hide()
        self.ventana_modulo = ventana_modulo   # se guarda para que no la borre el GC
        self.ventana_modulo.show()

    def showEvent(self, evento):
        # Al volver de un modulo (alta de reserva, carga de consumo, etc.) los
        # numeros del panel pueden haber cambiado, asi que se recalculan.
        super().showEvent(evento)
        self.cargar_panel()

    def abrir_salon(self):
        from vista.salon.salon_ventana import VentanaSalon

        self._abrir_modulo(VentanaSalon(self))

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
