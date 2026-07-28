"""
Dialogo chico para cambiar solo el estado de asistencia de una reserva. Se puede
usar en cualquier reserva, incluso pasadas (para marcar retroactivamente).
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

from utilidades import formato

RUTA_UI = Path(__file__).resolve().parent / "estado_form.ui"


class DialogoEstado(QDialog):
    def __init__(self, estado_actual, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        for texto, valor in formato.ESTADOS_ASISTENCIA:
            self.comboBox_estado.addItem(texto, valor)
        indice = self.comboBox_estado.findData(estado_actual)
        if indice >= 0:
            self.comboBox_estado.setCurrentIndex(indice)

        self.pushButton_guardar.clicked.connect(self.accept)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def estado_elegido(self):
        return self.comboBox_estado.currentData()
