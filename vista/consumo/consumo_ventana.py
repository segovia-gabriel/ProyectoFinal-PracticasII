"""
Ventana de Consumos. Listado de consumos cargados, alta de un consumo nuevo y
vista de detalle. Al cerrarse vuelve la ventana principal.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QMainWindow, QMessageBox, QTableWidgetItem

from controlador.consumo_controlador import ConsumoControlador
from utilidades import formato
from vista.consumo.consumo_form_ventana import DialogoConsumo
from vista.consumo.consumo_detalle_ventana import DialogoDetalleConsumo

RUTA_UI = Path(__file__).resolve().parent / "consumo.ui"


class VentanaConsumo(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = ConsumoControlador()

        self.tableWidget_consumos.verticalHeader().setVisible(False)
        self.tableWidget_consumos.horizontalHeader().setStretchLastSection(True)

        self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)
        self.pushButton_detalle.clicked.connect(self.ver_detalle)
        self.pushButton_volver.clicked.connect(self.close)
        self.tableWidget_consumos.doubleClicked.connect(self.ver_detalle)

        self.cargar_consumos()

    def cargar_consumos(self):
        exito, resultado = self.controlador.listar()
        if not exito:
            QMessageBox.warning(self, "Error", resultado)
            return
        tabla = self.tableWidget_consumos
        tabla.setRowCount(0)
        for fila, consumo in enumerate(resultado):
            tabla.insertRow(fila)
            cliente = f"{consumo['cliente_apellido']}, {consumo['cliente_nombre']}"
            item_cliente = QTableWidgetItem(cliente)
            item_cliente.setData(Qt.UserRole, consumo["id"])
            tabla.setItem(fila, 0, item_cliente)
            tabla.setItem(fila, 1, QTableWidgetItem(consumo["mesa_codigo"]))
            tabla.setItem(fila, 2, QTableWidgetItem(consumo["fecha"].strftime("%d/%m/%Y %H:%M")))
            tabla.setItem(fila, 3, QTableWidgetItem(formato.medio_pago(consumo["medio_pago"])))
            tabla.setItem(fila, 4, QTableWidgetItem(f"$ {float(consumo['precio_total']):,.2f}"))

    def _id_seleccionado(self):
        fila = self.tableWidget_consumos.currentRow()
        if fila < 0:
            return None
        return self.tableWidget_consumos.item(fila, 0).data(Qt.UserRole)

    def abrir_nuevo(self):
        dialogo = DialogoConsumo(self.controlador, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_consumos()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def ver_detalle(self):
        consumo_id = self._id_seleccionado()
        if consumo_id is None:
            QMessageBox.warning(self, "Atención", "Seleccioná un consumo para ver el detalle.")
            return
        exito, detalle = self.controlador.obtener_detalle(consumo_id)
        if not exito:
            QMessageBox.warning(self, "Error", detalle)
            return
        DialogoDetalleConsumo(detalle, parent=self).exec_()

    def closeEvent(self, evento):
        if self.parent() is not None:
            self.parent().show()
        evento.accept()
