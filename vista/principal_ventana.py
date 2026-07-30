
import sys
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import (QButtonGroup, QDialog, QHeaderView, QListWidgetItem,
                             QMainWindow, QMessageBox, QStackedWidget,
                             QStyle, QStyledItemDelegate, QTableWidgetItem)

from controlador.panel_controlador import PanelControlador
from controlador.reservas_controlador import ReservasControlador
from utilidades.logger import registrar
from utilidades.sesion import Sesion

RUTA_UI = Path(__file__).resolve().parent / "principal.ui"


class _AgendaDelegate(QStyledItemDelegate):
    """
    Con el QStyleSheetStyle activo, initStyleOption no alcanza: el motor de QSS
    pinta sus propios colores encima. Pisar paint() es la unica forma de asegurar
    que se vean los colores de cada fila.
    """
    _BG_NORMAL   = QColor("#ffffff")
    _BG_SELECTED = QColor("#dbeafe")
    _FG          = QColor("#0f172a")
    _BORDER      = QColor("#eef2f7")

    def paint(self, painter, option, index):
        is_selected = bool(option.state & QStyle.State_Selected)
        row_color   = index.data(Qt.BackgroundRole)

        painter.save()

        # Fondo
        if is_selected:
            painter.fillRect(option.rect, self._BG_SELECTED)
        elif row_color is not None:
            painter.fillRect(option.rect, row_color)
        else:
            painter.fillRect(option.rect, self._BG_NORMAL)

        # El borde de abajo, igual que el QSS global
        painter.setPen(QPen(self._BORDER, 1))
        r = option.rect
        painter.drawLine(r.left(), r.bottom(), r.right(), r.bottom())

        # Texto
        text = index.data(Qt.DisplayRole)
        if text:
            painter.setPen(self._FG)
            painter.setFont(option.font)
            painter.drawText(
                r.adjusted(8, 0, -8, 0),
                Qt.AlignVCenter | Qt.AlignLeft,
                str(text),
            )

        painter.restore()


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(RUTA_UI, self)
        except FileNotFoundError as error:
            registrar(error, "error")
            QMessageBox.critical(self, "Error", "No se encontro la pantalla principal.")
            sys.exit(1)

        self.controlador = PanelControlador()
        # lo uso para cambiar la asistencia desde la agenda del panel
        self.reservas_controlador = ReservasControlador()

        # El area de contenido pasa a ser un QStackedWidget: el panel de inicio
        # es la pagina 0 y cada modulo va como una pagina mas, todo dentro de la
        # misma ventana (el navbar cambia de pagina, no abre ventanas nuevas).
        layout_central = self.widget_central.layout()
        layout_central.removeWidget(self.widget_contenido)
        self.stack_contenido = QStackedWidget()
        self.stack_contenido.addWidget(self.widget_contenido)  # pagina 0: inicio
        layout_central.addWidget(self.stack_contenido)
        self._modulo_actual = None  # el modulo que se ve ahora (fuera del inicio)

        # El usuario logueado al pie del navbar: solo el nombre (el rol esta fijo en el .ui).
        self.label_nombreUsuario.setText(Sesion().nombre_usuario or "")

        # Al abrir el sistema, cierro lo que haya quedado abierto de dias
        # anteriores (por si ayer no lo cerraron a mano). Va en silencio: solo
        # hace algo si hay algo que cerrar.
        from controlador.cierre_controlador import CierreControlador
        CierreControlador().barrido_inicial()

        # Las cuatro columnas se reparten el ancho por igual: si estiraba solo la
        # del cliente, con la ventana maximizada quedaba un hueco enorme entre el
        # nombre y la mesa.
        self.tableWidget_agenda.verticalHeader().setVisible(False)
        self.tableWidget_agenda.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_agenda.setToolTip(
            "Doble clic en una reserva para marcar la asistencia del cliente.")
        # El delegate hace que anden los colores de fila aunque haya QSS global.
        self.tableWidget_agenda.setItemDelegate(_AgendaDelegate(self))
        self.tableWidget_agenda.setAlternatingRowColors(False)

        # Los avisos son textos largos: los corto en varias lineas dentro del
        # ancho del panel, sin scroll horizontal.
        self.listWidget_avisos.setWordWrap(True)
        self.listWidget_avisos.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listWidget_avisos.setToolTip(
            "Doble clic en un pendiente para resolverlo.")

        # El navbar cambia la pagina del stack: "Inicio" vuelve al panel de
        # resumen y cada modulo aparece como su propia pagina.
        self.pushButton_inicio.clicked.connect(self.ir_al_inicio)
        self.pushButton_usuarios.clicked.connect(self.abrir_usuarios)
        self.pushButton_historial.clicked.connect(self.abrir_historial)
        self.pushButton_mesas.clicked.connect(self.abrir_mesas)
        self.pushButton_clientes.clicked.connect(self.abrir_clientes)
        self.pushButton_menu.clicked.connect(self.abrir_menu)
        self.pushButton_reservas.clicked.connect(self.abrir_reservas)
        self.pushButton_consumo.clicked.connect(self.abrir_consumo)
        self.pushButton_estadisticas.clicked.connect(self.abrir_estadisticas)

        # Grupo exclusivo del navbar: deja un solo boton marcado (checked) a la
        # vez. El CSS pinta de azul el :checked, asi se ve en que modulo estas
        # parado. Arranca marcado "Inicio", que es la pagina que se ve al abrir.
        self._grupo_navbar = QButtonGroup(self)
        self._grupo_navbar.setExclusive(True)
        for boton in (self.pushButton_inicio,
                      self.pushButton_reservas, self.pushButton_consumo,
                      self.pushButton_clientes, self.pushButton_mesas,
                      self.pushButton_menu, self.pushButton_estadisticas,
                      self.pushButton_usuarios, self.pushButton_historial):
            boton.setCheckable(True)
            self._grupo_navbar.addButton(boton)
        self.pushButton_inicio.setChecked(True)

        # Doble clic para resolver desde el panel sin entrar al modulo: en la
        # agenda cambia el estado de asistencia, y en los pendientes abre la
        # pantalla que corresponde segun el tipo de aviso.
        self.tableWidget_agenda.doubleClicked.connect(self.cambiar_estado_agenda)
        self.pushButton_cambiarEstado.clicked.connect(self.cambiar_estado_agenda)
        self.pushButton_cargarConsumo.clicked.connect(self.cargar_consumo_agenda)
        self.listWidget_avisos.itemDoubleClicked.connect(self.resolver_aviso)

        self.pushButton_cerrarDia.clicked.connect(self.cerrar_dia)
        self.pushButton_cerrarSesion.clicked.connect(self.cerrar_sesion)
        # El panel se carga en showEvent, que corre tanto al abrir la ventana como
        # al volver de un modulo, asi los numeros nunca quedan desactualizados.

    # ---------- Panel de resumen ----------

    def cargar_panel(self):
        # Encabezado: el saludo segun la hora y la fecha de hoy en texto largo.
        self.label_titulo.setText(self.controlador.saludo(Sesion().nombre_usuario or ""))
        self.label_fecha.setText(self.controlador.fecha_larga())

        exito, datos = self.controlador.resumen()
        if not exito:
            QMessageBox.warning(self, "Panel principal", datos)
            return

        self.label_valorReservasHoy.setText(str(datos["reservas_hoy"]))
        self.label_valorReservasFuturas.setText(str(datos["reservas_manana"]))
        self.label_valorClientes.setText(str(datos["reservas_futuras"]))

        self._cargar_agenda(datos["agenda"])
        self._cargar_avisos(datos["avisos"])

    def _cargar_agenda(self, filas):
        # Verde  = asistio (sin consumo todavia)
        # Naranja = consumo abierto (mesa en uso)
        # Azul   = consumo cerrado (mesa pagada)
        # Rojo   = falto
        COLOR_ASISTIO  = QColor(183, 230, 199)
        COLOR_ABIERTA  = QColor(255, 220, 130)
        COLOR_CERRADA  = QColor(173, 207, 245)
        COLOR_FALTO    = QColor(255, 187, 187)

        tabla = self.tableWidget_agenda
        tabla.setRowCount(len(filas))
        for i, fila in enumerate(filas):
            celda = QTableWidgetItem(fila["horario"])
            celda.setData(Qt.UserRole, fila["id"])
            celda.setData(Qt.UserRole + 1, fila["estado_clave"])
            tabla.setItem(i, 0, celda)
            tabla.setItem(i, 1, QTableWidgetItem(fila["cliente"]))
            tabla.setItem(i, 2, QTableWidgetItem(fila["mesa"]))
            tabla.setItem(i, 3, QTableWidgetItem(fila["estado"]))

            consumo = fila.get("estado_consumo")
            asistencia = fila["estado_clave"]
            if consumo == "cerrada":
                color = COLOR_CERRADA
            elif consumo == "abierta":
                color = COLOR_ABIERTA
            elif asistencia == "asistio":
                color = COLOR_ASISTIO
            elif asistencia == "falto":
                color = COLOR_FALTO
            else:
                color = None  # en_espera y tardanza sin color

            if color:
                for col in range(tabla.columnCount()):
                    if tabla.item(i, col):
                        tabla.item(i, col).setBackground(color)

        # Si no hay reservas lo aviso en el titulo, para no dejar una tabla vacia
        # sin explicacion.
        if filas:
            self.label_subtituloAgenda.setText(f"Agenda de hoy ({len(filas)})")
        else:
            self.label_subtituloAgenda.setText("Agenda de hoy — sin reservas")

    def _cargar_avisos(self, avisos):
        lista = self.listWidget_avisos
        lista.clear()
        if not avisos:
            item = QListWidgetItem("No hay notificaciones. Todo al dia.")
            item.setTextAlignment(Qt.AlignCenter)
            lista.addItem(item)
            self.label_subtituloAvisos.setText("Notificaciones")
            return

        for aviso in avisos:
            item = QListWidgetItem(aviso["texto"])
            # guardo el aviso entero para saber que abrir en el doble clic
            item.setData(Qt.UserRole, aviso)
            lista.addItem(item)
        self.label_subtituloAvisos.setText(f"Notificaciones ({len(avisos)})")

    # ---------- Acciones desde el panel ----------

    def cargar_consumo_agenda(self):
        fila = self.tableWidget_agenda.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atencion", "Selecciona una reserva de la agenda.")
            return
        reserva_id = self.tableWidget_agenda.item(fila, 0).data(Qt.UserRole)
        self._cargar_consumo_pendiente(reserva_id)

    def cambiar_estado_agenda(self):
        fila = self.tableWidget_agenda.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atencion", "Selecciona una reserva de la agenda.")
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

    def cerrar_dia(self):
        # Cierre manual del dia: pido confirmacion porque cierra mesas y vence
        # reservas sin consumo. Al terminar, refresco el panel.
        from controlador.cierre_controlador import CierreControlador

        resp = QMessageBox.question(
            self, "Cerrar dia",
            "Se van a cerrar todas las mesas abiertas de hoy, descartar las vacias "
            "y marcar como vencidas las reservas sin consumo. ¿Confirmas?",
            QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return

        exito, datos = CierreControlador().cerrar_dia()
        if not exito:
            QMessageBox.warning(self, "Cerrar dia", datos)
            return
        QMessageBox.information(
            self, "Cerrar dia",
            f"Dia cerrado.\n"
            f"Mesas cerradas: {datos['cerradas']}\n"
            f"Mesas vacias descartadas: {datos['descartadas']}\n"
            f"Reservas sin consumo vencidas: {datos['vencidas']}")
        self.cargar_panel()

    def resolver_aviso(self, item):
        # Doble clic sobre un pendiente: abro la pantalla donde se resuelve, asi el
        # aviso desaparece del panel apenas se completa.
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
        # Abro el historial de precios del item, que es donde se carga el precio
        # nuevo. Cuando se cierra, esa ventana vuelve a mostrar esta.
        from controlador.menu_controlador import MenuControlador
        from vista.menu.precios_ventana import VentanaPrecios

        controlador = MenuControlador()
        exito, item = controlador.obtener_item(item_id)
        if not exito or item is None:
            QMessageBox.warning(self, "Error", "No se pudo abrir el item de menu.")
            return
        VentanaPrecios(item, controlador, self).exec_()  # dialogo modal
        self.cargar_panel()  # capaz ya se resolvio el aviso de renovacion

    # ---------- Navegacion ----------
    # Todo pasa dentro de la misma ventana: cada modulo va como una pagina del
    # QStackedWidget en vez de abrir una ventana nueva.

    def _mostrar_modulo(self, fabrica):
        # Crea el modulo de cero (datos al dia) y tira el anterior, para no ir
        # acumulando widgets ni mostrar datos viejos. Fuera del inicio vive uno solo.
        if self._modulo_actual is not None:
            self.stack_contenido.removeWidget(self._modulo_actual)
            self._modulo_actual.deleteLater()
        modulo = fabrica()
        self._modulo_actual = modulo
        self.stack_contenido.addWidget(modulo)
        self.stack_contenido.setCurrentWidget(modulo)

    def ir_al_inicio(self):
        # El boton "Inicio" del navbar te trae de vuelta el panel de resumen.
        self.stack_contenido.setCurrentWidget(self.widget_contenido)
        self.cargar_panel()  # los numeros pudieron cambiar mientras estabas adentro

    def showEvent(self, evento):
        # La carga inicial del panel cuando se muestra la ventana.
        super().showEvent(evento)
        self.cargar_panel()

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
