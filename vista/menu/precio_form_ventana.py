"""
Formulario modal para cargar un precio nuevo de un item. El precio especial y su
medio de pago solo se habilitan si se tilda el checkbox correspondiente.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

RUTA_UI = Path(__file__).resolve().parent / "precio_form.ui"


class DialogoPrecio(QDialog):
    def __init__(self, controlador, item_id, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.item_id = item_id
        self.mensaje_exito = ""

        # El medio de pago guarda el valor tecnico como data de cada opcion.
        self.comboBox_medio.addItem("Efectivo", "efectivo")
        self.comboBox_medio.addItem("Transferencia", "transferencia")

        # Habilitar los campos del especial solo si se tilda el checkbox.
        self.checkBox_especial.toggled.connect(self._alternar_especial)

        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def _alternar_especial(self, activo):
        self.doubleSpinBox_especial.setEnabled(activo)
        self.comboBox_medio.setEnabled(activo)

    def guardar(self):
        tiene_especial = self.checkBox_especial.isChecked()
        exito, mensaje = self.controlador.guardar_precio(
            self.item_id,
            self.doubleSpinBox_lista.value(),
            tiene_especial,
            self.doubleSpinBox_especial.value(),
            self.comboBox_medio.currentData() if tiene_especial else None,
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
