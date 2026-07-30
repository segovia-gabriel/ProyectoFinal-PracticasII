from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QHeaderView, QTableWidgetItem

from utilidades import formato

RUTA_UI = Path(__file__).resolve().parent / "consumo_detalle.ui"


class DialogoDetalleConsumo(QDialog):
    def __init__(self, detalle, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.tableWidget_detalle.verticalHeader().setVisible(False)
        self.tableWidget_detalle.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.pushButton_volver.clicked.connect(self.accept)

        self._cargar(detalle)

    def _cargar(self, detalle):
        tabla = self.tableWidget_detalle
        tabla.setRowCount(0)
        total = 0.0
        for fila, linea in enumerate(detalle):
            precio = float(linea["precio_unitario_aplicado"])
            subtotal = precio * linea["cantidad"]
            total += subtotal
            tabla.insertRow(fila)
            tabla.setItem(fila, 0, QTableWidgetItem(linea["nombre"]))
            tabla.setItem(fila, 1, QTableWidgetItem(str(linea["cantidad"])))
            tabla.setItem(fila, 2, QTableWidgetItem(formato.moneda(precio)))
            tabla.setItem(fila, 3, QTableWidgetItem(formato.moneda(subtotal)))
        self.label_total.setText(f"Total: {formato.moneda(total)}")
