"""
Formulario modal de alta/edicion de mesa. El codigo se muestra en vivo (solo
lectura) a medida que se cambia el piso o el numero, y lo arma el controlador.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

from controlador.mesas_controlador import _codigo_mesa

RUTA_UI = Path(__file__).resolve().parent / "mesa_form.ui"


class DialogoMesa(QDialog):
    def __init__(self, controlador, mesa=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.mesa_id = mesa["id"] if mesa else None
        self.mensaje_exito = ""

        self.label_ayuda.setProperty("class", "ayuda")

        # Combo de grupos (guarda el id como data de cada opcion).
        exito, grupos = self.controlador.listar_grupos_combo()
        if exito:
            for grupo_id, nombre in grupos:
                self.comboBox_grupo.addItem(nombre, grupo_id)

        if mesa:
            self.setWindowTitle("Editar mesa")
            self.label_titulo.setText("Editar mesa")
            self.spinBox_numero.setValue(mesa["numero_mesa"])
            self.spinBox_sillas.setValue(mesa["numero_sillas"])
            indice_piso = self.comboBox_piso.findText(str(mesa["piso"]))
            if indice_piso >= 0:
                self.comboBox_piso.setCurrentIndex(indice_piso)
            indice = self.comboBox_grupo.findData(mesa["grupo_mesa_id"])
            if indice >= 0:
                self.comboBox_grupo.setCurrentIndex(indice)
        else:
            # Alta: se sugiere el numero siguiente al ultimo cargado (queda
            # editable por si el usuario quiere otro).
            self.spinBox_numero.setValue(self.controlador.siguiente_numero_mesa())

        # El codigo se recalcula solo al cambiar piso o numero.
        self.comboBox_piso.currentIndexChanged.connect(self._actualizar_codigo)
        self.spinBox_numero.valueChanged.connect(self._actualizar_codigo)
        self._actualizar_codigo()

        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def _piso(self):
        # El combo guarda el piso como texto ("0" o "1"); se usa como entero.
        return int(self.comboBox_piso.currentText())

    def _actualizar_codigo(self):
        codigo = _codigo_mesa(self._piso(), self.spinBox_numero.value())
        self.lineEdit_codigo.setText(codigo)

    def guardar(self):
        exito, mensaje = self.controlador.guardar_mesa(
            self.mesa_id,
            self.spinBox_numero.value(),
            self.spinBox_sillas.value(),
            self._piso(),
            self.comboBox_grupo.currentData(),
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
