"""
Formulario modal para cargar o editar el precio de un item. Se carga solo el
precio de lista; el precio en efectivo (10% menos) lo calcula el controlador.
La fecha de fin siempre es obligatoria; se avisa 10 dias antes del vencimiento.
Si se abre con precio_actual, funciona en modo edicion del vigente.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDialog

RUTA_UI = Path(__file__).resolve().parent / "precio_form.ui"


class DialogoPrecio(QDialog):
    def __init__(self, controlador, item_id, precio_actual=None,
                 fecha_fin_sugerida=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.item_id = item_id
        self.precio_actual = precio_actual
        self.mensaje_exito = ""

        # La fecha de fin siempre es obligatoria y minimo hoy.
        # Si hay un precio anterior, se pre-carga su fecha_fin como referencia
        # (el usuario la ve y decide desde ahi), pero puede elegir cualquier
        # fecha futura sin restriccion del precio anterior.
        self.dateEdit_fin.setMinimumDate(QDate.currentDate())
        if fecha_fin_sugerida is not None:
            q_sugerida = QDate(fecha_fin_sugerida.year,
                               fecha_fin_sugerida.month,
                               fecha_fin_sugerida.day)
            self.dateEdit_fin.setDate(q_sugerida)
        else:
            self.dateEdit_fin.setDate(QDate.currentDate().addDays(30))

        if precio_actual is not None:
            self._precargar(precio_actual)

        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def _precargar(self, precio):
        self.setWindowTitle("Editar precio vigente")
        self.label_titulo.setText("Editar precio vigente")
        self.doubleSpinBox_lista.setValue(float(precio["precio_lista"]))
        if precio["fecha_fin"] is not None:
            fin = precio["fecha_fin"]
            self.dateEdit_fin.setDate(QDate(fin.year, fin.month, fin.day))

    def guardar(self):
        precio_lista = self.doubleSpinBox_lista.value()
        fecha_fin = self.dateEdit_fin.date().toPyDate()
        if self.precio_actual is None:
            exito, mensaje = self.controlador.guardar_precio(
                self.item_id, precio_lista, fecha_fin)
        else:
            exito, mensaje = self.controlador.editar_precio_vigente(
                self.item_id, precio_lista, fecha_fin)
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
