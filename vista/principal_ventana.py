"""
Ventana principal (unica ventana de trabajo). A la izquierda el menu y a la
derecha un QStackedWidget: la pagina de inicio muestra el panel con el resumen
del dia (reservas de hoy, pendientes, ingresos del mes) y cada modulo se muestra
como otra pagina del stack, sin abrir ventanas nuevas. El menu cambia de pagina:
el boton "Inicio" trae de vuelta el panel de resumen.
Tambien maneja el cierre de sesion, que vuelve al login.
"""

import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QButtonGroup, QDialog, QHeaderView, QListWidgetItem,
                             QMainWindow, QMessageBox, QStackedWidget,
                             QTableWidgetItem)

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

        # El area de contenido pasa a ser un QStackedWidget: el panel de inicio
        # es la pagina 0 y cada modulo se muestra como una pagina mas, todo
        # dentro de esta misma ventana (el navbar cambia de pagina, no abre
        # ventanas nuevas).
        layout_central = self.widget_central.layout()
        layout_central.removeWidget(self.widget_contenido)
        self.stack_contenido = QStackedWidget()
        self.stack_contenido.addWidget(self.widget_contenido)  # pagina 0: inicio
        layout_central.addWidget(self.stack_contenido)
        self._modulo_actual = None  # modulo visible ahora (fuera del inicio)

        # Usuario logueado al pie del navbar: solo el nombre (el rol es fijo en el .ui).
        self.label_nombreUsuario.setText(Sesion().nombre_usuario or "")

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

        # El navbar cambia la pagina del stack: "Inicio" vuelve al panel de
        # resumen y cada modulo se muestra como su propia pagina.
        self.pushButton_inicio.clicked.connect(self.ir_al_inicio)
        self.pushButton_salon.clicked.connect(self.abrir_salon)
        self.pushButton_usuarios.clicked.connect(self.abrir_usuarios)
        self.pushButton_historial.clicked.connect(self.abrir_historial)
        self.pushButton_mesas.clicked.connect(self.abrir_mesas)
        self.pushButton_clientes.clicked.connect(self.abrir_clientes)
        self.pushButton_menu.clicked.connect(self.abrir_menu)
        self.pushButton_reservas.clicked.connect(self.abrir_reservas)
        self.pushButton_consumo.clicked.connect(self.abrir_consumo)
        self.pushButton_estadisticas.clicked.connect(self.abrir_estadisticas)

        # Grupo exclusivo del navbar: hace que un solo boton quede marcado
        # (checked) a la vez. El CSS pinta de azul el :checked, asi se ve en que
        # modulo estamos. Arranca marcado "Inicio", que es la pagina que se muestra.
        self._grupo_navbar = QButtonGroup(self)
        self._grupo_navbar.setExclusive(True)
        for boton in (self.pushButton_inicio, self.pushButton_salon,
                      self.pushButton_reservas, self.pushButton_consumo,
                      self.pushButton_clientes, self.pushButton_mesas,
                      self.pushButton_menu, self.pushButton_estadisticas,
                      self.pushButton_usuarios, self.pushButton_historial):
            boton.setCheckable(True)
            self._grupo_navbar.addButton(boton)
        self.pushButton_inicio.setChecked(True)

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
        VentanaPrecios(item, controlador, self).exec_()  # ahora es un dialogo modal
        self.cargar_panel()  # el aviso de renovacion pudo resolverse

    # ---------- Navegacion ----------
    # Todo pasa dentro de la misma ventana: cada modulo se muestra como una
    # pagina del QStackedWidget en vez de abrir una ventana nueva.

    def _mostrar_modulo(self, fabrica):
        # Crea el modulo fresco (datos al dia) y descarta el anterior, para no
        # acumular widgets ni mostrar datos viejos. Fuera del inicio vive uno solo.
        if self._modulo_actual is not None:
            self.stack_contenido.removeWidget(self._modulo_actual)
            self._modulo_actual.deleteLater()
        modulo = fabrica()
        self._modulo_actual = modulo
        self.stack_contenido.addWidget(modulo)
        self.stack_contenido.setCurrentWidget(modulo)

    def ir_al_inicio(self):
        # El boton "Inicio" del navbar trae de vuelta el panel de resumen.
        self.stack_contenido.setCurrentWidget(self.widget_contenido)
        self.cargar_panel()  # los numeros pudieron cambiar mientras estabas adentro

    def showEvent(self, evento):
        # Carga inicial del panel cuando se muestra la ventana.
        super().showEvent(evento)
        self.cargar_panel()

    def abrir_salon(self):
        from vista.salon.salon_ventana import VentanaSalon
        self._mostrar_modulo(VentanaSalon)

    def abrir_usuarios(self):
        from vista.usuarios.usuarios_ventana import VentanaUsuarios
        self._mostrar_modulo(VentanaUsuarios)

    def abrir_historial(self):
        from vista.historial.historial_ventana import VentanaHistorial
        self._mostrar_modulo(VentanaHistorial)

    def abrir_mesas(self):
        from vista.mesas.mesas_ventana import VentanaMesas
        self._mostrar_modulo(VentanaMesas)

    def abrir_clientes(self):
        from vista.clientes.clientes_ventana import VentanaClientes
        self._mostrar_modulo(VentanaClientes)

    def abrir_menu(self):
        from vista.menu.menu_ventana import VentanaMenu
        self._mostrar_modulo(VentanaMenu)

    def abrir_reservas(self):
        from vista.reservas.reservas_ventana import VentanaReservas
        self._mostrar_modulo(VentanaReservas)

    def abrir_consumo(self):
        from vista.consumo.consumo_ventana import VentanaConsumo
        self._mostrar_modulo(VentanaConsumo)

    def abrir_estadisticas(self):
        from vista.estadisticas.estadisticas_ventana import VentanaEstadisticas
        self._mostrar_modulo(VentanaEstadisticas)

    def cerrar_sesion(self):
        Sesion().cerrar()
        from vista.login_ventana import VentanaLogin

        self.ventana_login = VentanaLogin()
        self.ventana_login.show()
        self.close()
