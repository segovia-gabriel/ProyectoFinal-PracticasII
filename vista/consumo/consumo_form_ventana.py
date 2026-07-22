"""
Formulario modal de alta de consumo. Se elige la reserva y el medio de pago, se
agregan items con cantidad, y el precio de cada uno se resuelve segun el medio
(especial si coincide, si no de lista). El total se recalcula solo, y tambien
cuando se cambia el medio de pago. El calculo final lo confirma el controlador.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QMessageBox, QTableWidgetItem

RUTA_UI = Path(__file__).resolve().parent / "consumo_form.ui"


class DialogoConsumo(QDialog):
    def __init__(self, controlador, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.mensaje_exito = ""
        # cada item agregado: {"item_id", "nombre", "cantidad"}
        self.items_agregados = []

        self.tableWidget_items.verticalHeader().setVisible(False)
        self.tableWidget_items.horizontalHeader().setStretchLastSection(True)

        exito, reservas = self.controlador.listar_reservas_combo()
        if exito:
            for rid, texto in reservas:
                self.comboBox_reserva.addItem(texto, rid)
        self.comboBox_medio.addItem("Efectivo", "efectivo")
        self.comboBox_medio.addItem("Transferencia", "transferencia")
        exito, items = self.controlador.listar_items_combo()
        if exito:
            for iid, nombre in items:
                self.comboBox_item.addItem(nombre, iid)

        self.pushButton_agregar.clicked.connect(self.agregar_item)
        self.pushButton_quitar.clicked.connect(self.quitar_item)
        # al cambiar el medio de pago, cambian los precios especiales
        self.comboBox_medio.currentIndexChanged.connect(self._refrescar_tabla)
        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def _medio(self):
        return self.comboBox_medio.currentData()

    def agregar_item(self):
        item_id = self.comboBox_item.currentData()
        if item_id is None:
            return
        # el item tiene que tener precio cargado para poder consumirse
        if self.controlador.precio_item(item_id, self._medio()) is None:
            QMessageBox.warning(self, "Sin precio",
                                "Ese ítem no tiene un precio cargado. Cargale uno desde Menú → Precios.")
            return

        cantidad = self.spinBox_cantidad.value()
        # si el item ya estaba, se suma la cantidad en vez de duplicar la fila
        for agregado in self.items_agregados:
            if agregado["item_id"] == item_id:
                agregado["cantidad"] += cantidad
                break
        else:
            self.items_agregados.append({
                "item_id": item_id,
                "nombre": self.comboBox_item.currentText(),
                "cantidad": cantidad,
            })
        self._refrescar_tabla()

    def quitar_item(self):
        fila = self.tableWidget_items.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccioná un ítem de la lista para quitar.")
            return
        del self.items_agregados[fila]
        self._refrescar_tabla()

    def _refrescar_tabla(self):
        medio = self._medio()
        tabla = self.tableWidget_items
        tabla.setRowCount(0)
        total = 0.0
        for fila, agregado in enumerate(self.items_agregados):
            precio = self.controlador.precio_item(agregado["item_id"], medio)
            precio = float(precio) if precio is not None else 0.0
            subtotal = precio * agregado["cantidad"]
            total += subtotal
            tabla.insertRow(fila)
            tabla.setItem(fila, 0, QTableWidgetItem(agregado["nombre"]))
            item_cant = QTableWidgetItem(str(agregado["cantidad"]))
            item_cant.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(fila, 1, item_cant)
            tabla.setItem(fila, 2, QTableWidgetItem(f"$ {precio:,.2f}"))
            tabla.setItem(fila, 3, QTableWidgetItem(f"$ {subtotal:,.2f}"))
        self.label_total.setText(f"Total: $ {total:,.2f}")

    def guardar(self):
        items = [(a["item_id"], a["cantidad"]) for a in self.items_agregados]
        exito, mensaje = self.controlador.guardar_consumo(
            self.comboBox_reserva.currentData(), self._medio(), items
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
