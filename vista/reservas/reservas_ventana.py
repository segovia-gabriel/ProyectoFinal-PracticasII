"""
Ventana de Reservas. Listado con filtros (cliente y rango de fechas) y CRUD, con
la regla de que las reservas pasadas no se editan ni eliminan (pero su estado de
asistencia si se puede cambiar). Al cerrarse vuelve la principal.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (QDialog, QHeaderView, QMainWindow, QMessageBox,
                             QTableWidgetItem)

from controlador.reservas_controlador import ReservasControlador
from utilidades import formato
from vista.reservas.reserva_form_ventana import DialogoReserva
from vista.reservas.estado_form_ventana import DialogoEstado

RUTA_UI = Path(__file__).resolve().parent / "reservas.ui"

_DURACION_TEXTO = {"2h": "2 horas", "3h": "3 horas"}


class VentanaReservas(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = ReservasControlador()

        self.tableWidget_reservas.verticalHeader().setVisible(False)
        # El cliente se queda con el ancho sobrante y el resto de las columnas
        # se ajusta a su contenido, asi no aparece scroll horizontal.
        cabecera = self.tableWidget_reservas.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(0, QHeaderView.Stretch)
        # Al entrar se muestra la semana de trabajo: de ayer a 7 dias adelante.
        # Ayer entra a proposito, porque es la reserva que todavia puede faltar
        # marcarle la asistencia. Para ver el historial completo se corre el
        # "Desde" hacia atras.
        self.dateEdit_desde.setDate(QDate.currentDate().addDays(-1))
        self.dateEdit_hasta.setDate(QDate.currentDate().addDays(7))

        self.pushButton_buscar.clicked.connect(self.cargar_reservas)
        self.lineEdit_filtro.returnPressed.connect(self.cargar_reservas)
        self.pushButton_nueva.clicked.connect(self.abrir_nueva)
        self.pushButton_editar.clicked.connect(self.abrir_editar)
        self.pushButton_eliminar.clicked.connect(self.eliminar_seleccionada)
        self.pushButton_estado.clicked.connect(self.cambiar_estado)
        self.pushButton_volver.clicked.connect(self.close)
        self.tableWidget_reservas.doubleClicked.connect(self.abrir_editar)

        self.cargar_reservas()

    def cargar_reservas(self):
        filtro = self.lineEdit_filtro.text().strip() or None
        desde = self.dateEdit_desde.date().toPyDate()
        hasta = self.dateEdit_hasta.date().toPyDate()
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
            tabla.setItem(fila, 4, QTableWidgetItem(_DURACION_TEXTO.get(reserva["duracion_tipo"], reserva["duracion_tipo"])))
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
            QMessageBox.warning(self, "Atención", "Seleccioná una reserva para editar.")
            return
        # Regla: las reservas pasadas no se editan (solo su estado).
        if self.controlador.es_pasada(reserva):
            QMessageBox.information(
                self, "Reserva pasada",
                "No se puede editar una reserva pasada. Usá 'Cambiar estado' para marcar la asistencia.",
            )
            return
        dialogo = DialogoReserva(self.controlador, reserva=reserva, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_reservas()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def eliminar_seleccionada(self):
        reserva_id = self._id_seleccionado()
        if reserva_id is None:
            QMessageBox.warning(self, "Atención", "Seleccioná una reserva para eliminar.")
            return
        confirmar = QMessageBox.question(
            self, "Confirmar", "¿Seguro que querés eliminar esta reserva?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if confirmar != QMessageBox.Yes:
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
            QMessageBox.warning(self, "Atención", "Seleccioná una reserva para cambiar su estado.")
            return
        dialogo = DialogoEstado(reserva["estado_asistencia"], parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            exito, mensaje = self.controlador.cambiar_estado(reserva["id"], dialogo.estado_elegido())
            if exito:
                QMessageBox.information(self, "Listo", mensaje)
                self.cargar_reservas()
            else:
                QMessageBox.warning(self, "Error", mensaje)

    def closeEvent(self, evento):
        if self.parent() is not None:
            self.parent().show()
        evento.accept()
