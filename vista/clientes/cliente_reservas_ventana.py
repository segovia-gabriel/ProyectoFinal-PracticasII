from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QHeaderView, QTableWidgetItem

from utilidades import formato

RUTA_UI = Path(__file__).resolve().parent / "cliente_reservas.ui"


class DialogoReservasCliente(QDialog):
    def __init__(self, nombre_completo, reservas, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.label_titulo.setText(f"Reservas de {nombre_completo}")
        self.tableWidget_reservas.verticalHeader().setVisible(False)
        self.tableWidget_reservas.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch
        )

        self.pushButton_volver.clicked.connect(self.accept)

        self._cargar(reservas)

    def _cargar(self, reservas):
        tabla = self.tableWidget_reservas
        tabla.setRowCount(0)
        for fila, reserva in enumerate(reservas):
            tabla.insertRow(fila)
            tabla.setItem(fila, 0, QTableWidgetItem(reserva["fecha"].strftime("%d/%m/%Y")))
            horario = f"{formato.hora(reserva['hora_inicio'])} - {formato.hora(reserva['hora_fin'])}"
            tabla.setItem(fila, 1, QTableWidgetItem(horario))
            tabla.setItem(fila, 2, QTableWidgetItem(reserva["mesa"]))
            tabla.setItem(fila, 3, QTableWidgetItem(formato.estado_asistencia(reserva["estado_asistencia"])))
