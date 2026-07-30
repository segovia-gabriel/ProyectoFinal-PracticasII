"""
Ventana de Reservas. Listado con filtros (cliente y rango de fechas) y ABM, con
la regla de que las reservas pasadas no se editan ni se borran (pero el estado de
asistencia si se puede cambiar). Al cerrarse vuelve la principal.
"""

from datetime import date
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (QDialog, QHeaderView, QWidget, QMessageBox,
                             QTableWidgetItem)

from controlador.reservas_controlador import ReservasControlador
from utilidades import formato
from utilidades.dialogos import confirmar_eliminacion
from utilidades.validaciones import validar_rango_fechas
from vista.reservas.reserva_form_ventana import DialogoReserva
from vista.reservas.estado_form_ventana import DialogoEstado

RUTA_UI = Path(__file__).resolve().parent / "reservas.ui"


class VentanaReservas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = ReservasControlador()

        self.tableWidget_reservas.verticalHeader().setVisible(False)
        # Todas las columnas reparten el ancho por igual, asi no queda scroll
        # horizontal ni huecos cuando maximizo la ventana.
        self.tableWidget_reservas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Al entrar muestro la semana de trabajo: de ayer a 7 dias para adelante.
        # Ayer entra a proposito, porque es la reserva a la que capaz todavia falta
        # marcarle la asistencia. Para ver todo el historial, corres el "Desde"
        # para atras.
        self.dateEdit_desde.setDate(QDate.currentDate().addDays(-1))
        self.dateEdit_hasta.setDate(QDate.currentDate().addDays(7))

        self.pushButton_buscar.clicked.connect(self.cargar_reservas)
        self.lineEdit_filtro.returnPressed.connect(self.cargar_reservas)
        self.pushButton_nueva.clicked.connect(self.abrir_nueva)
        self.pushButton_editar.clicked.connect(self.abrir_editar)
        self.pushButton_eliminar.clicked.connect(self.eliminar_seleccionada)
        self.pushButton_estado.clicked.connect(self.cambiar_estado)
        self.tableWidget_reservas.doubleClicked.connect(self.abrir_editar)

        self.cargar_reservas()

    def cargar_reservas(self):
        filtro = self.lineEdit_filtro.text().strip() or None
        desde = self.dateEdit_desde.date().toPyDate()
        hasta = self.dateEdit_hasta.date().toPyDate()
        valido, mensaje = validar_rango_fechas(desde, hasta)
        if not valido:
            QMessageBox.warning(self, "Rango de fechas invalido", mensaje)
            return
        exito, resultado = self.controlador.listar(filtro, desde, hasta)
        if not exito:
            QMessageBox.warning(self, "Error", resultado)
            return

        tabla = self.tableWidget_reservas
        tabla.setRowCount(0)
        for fila, reserva in enumerate(resultado):
            tabla.insertRow(fila)
            cliente = f"{reserva['cliente_apellido']}, {reserva['cliente_nombre']}"
            item_cliente = QTableWidgetItem(cliente)
            item_cliente.setData(Qt.UserRole, reserva["id"])
            tabla.setItem(fila, 0, item_cliente)
            tabla.setItem(fila, 1, QTableWidgetItem(reserva["mesa_codigo"]))
            tabla.setItem(fila, 2, QTableWidgetItem(reserva["fecha"].strftime("%d/%m/%Y")))
            horario = f"{formato.hora(reserva['hora_inicio'])} - {formato.hora(reserva['hora_fin'])}"
            tabla.setItem(fila, 3, QTableWidgetItem(horario))
            tabla.setItem(fila, 4, QTableWidgetItem(formato.duracion(reserva["duracion_tipo"])))
            tabla.setItem(fila, 5, QTableWidgetItem(formato.moneda(reserva['precio_mesa_aplicado'])))
            tabla.setItem(fila, 6, QTableWidgetItem(formato.estado_asistencia(reserva["estado_asistencia"])))

    def _id_seleccionado(self):
        fila = self.tableWidget_reservas.currentRow()
        if fila < 0:
            return None
        return self.tableWidget_reservas.item(fila, 0).data(Qt.UserRole)

    def _reserva_seleccionada(self):
        # Devuelve la reserva completa desde la base, o None si no hay seleccion.
        reserva_id = self._id_seleccionado()
        if reserva_id is None:
            return None
        exito, reserva = self.controlador.obtener(reserva_id)
        return reserva if exito else None

    def abrir_nueva(self):
        dialogo = DialogoReserva(self.controlador, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_reservas()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def abrir_editar(self):
        reserva = self._reserva_seleccionada()
        if reserva is None:
            QMessageBox.warning(self, "Atencion", "Selecciona una reserva para editar.")
            return
        # Regla: las reservas pasadas no se editan (solo el estado).
        if self.controlador.es_pasada(reserva):
            QMessageBox.information(
                self, "Reserva pasada",
                "No se puede editar una reserva pasada, solo consultarla.",
            )
            return
        dialogo = DialogoReserva(self.controlador, reserva=reserva, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_reservas()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def eliminar_seleccionada(self):
        reserva_id = self._id_seleccionado()
        if reserva_id is None:
            QMessageBox.warning(self, "Atencion", "Selecciona una reserva para eliminar.")
            return
        if not confirmar_eliminacion(self, "¿Seguro que queres eliminar esta reserva?"):
            return
        # El controlador revalida que no sea pasada ni tenga consumo.
        exito, mensaje = self.controlador.eliminar(reserva_id)
        if exito:
            QMessageBox.information(self, "Listo", mensaje)
            self.cargar_reservas()
        else:
            QMessageBox.warning(self, "No se pudo eliminar", mensaje)

    def cambiar_estado(self):
        reserva = self._reserva_seleccionada()
        if reserva is None:
            QMessageBox.warning(self, "Atencion", "Selecciona una reserva para cambiar su estado.")
            return
        # El estado solo lo cambias el mismo dia de la reserva.
        if reserva["fecha"] != date.today():
            QMessageBox.information(
                self, "Solo el dia de la reserva",
                "El estado de asistencia solo se puede cambiar el mismo dia de la reserva.",
            )
            return
        dialogo = DialogoEstado(reserva["estado_asistencia"], parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            exito, mensaje = self.controlador.cambiar_estado(reserva["id"], dialogo.estado_elegido())
            if exito:
                QMessageBox.information(self, "Listo", mensaje)
                self.cargar_reservas()
            else:
                QMessageBox.warning(self, "Error", mensaje)
