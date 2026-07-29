"""
Ventana de historial de precios de un item. Muestra cada precio con su variacion
porcentual respecto al anterior y avisa si el precio vigente esta por vencer.
Se abre desde Menú; al cerrarse vuelve a Menú.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import (QDialog, QHeaderView, QMessageBox,
                             QTableWidgetItem)

from controlador.menu_controlador import MenuControlador
from utilidades import formato
from vista.menu.precio_form_ventana import DialogoPrecio

RUTA_UI = Path(__file__).resolve().parent / "precios.ui"


class VentanaPrecios(QDialog):
    def __init__(self, item, controlador=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador or MenuControlador()
        self.item_id = item["id"]
        self.label_titulo.setText(f"Precios — {item['nombre']}")

        self.tableWidget_precios.verticalHeader().setVisible(False)
        # Columnas parejas: son todas cortas (importes y fechas) y asi no queda
        # scroll horizontal ni una ultima columna desproporcionada.
        self.tableWidget_precios.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)
        self.pushButton_volver.clicked.connect(self.close)

        self.cargar_precios()

    def cargar_precios(self):
        self._mostrar_aviso()
        exito, filas = self.controlador.historial_precios(self.item_id)
        if not exito:
            QMessageBox.warning(self, "Error", filas)
            return

        tabla = self.tableWidget_precios
        tabla.setRowCount(0)
        for i, fila in enumerate(filas):
            tabla.insertRow(i)
            tabla.setItem(i, 0, QTableWidgetItem(formato.moneda(fila['precio_lista'])))
            if fila["precio_especial"] is not None:
                especial = formato.moneda(fila['precio_especial'])
                medio = formato.medio_pago(fila["medio_pago_especial"])
            else:
                especial = "—"
                medio = "—"
            tabla.setItem(i, 1, QTableWidgetItem(especial))
            tabla.setItem(i, 2, QTableWidgetItem(medio))
            tabla.setItem(i, 3, QTableWidgetItem(fila["fecha_inicio"].strftime("%d/%m/%Y")))
            hasta = fila["fecha_fin"].strftime("%d/%m/%Y") if fila["fecha_fin"] else "Vigente"
            tabla.setItem(i, 4, QTableWidgetItem(hasta))
            # variacion con signo; el primer precio no tiene con que compararse
            variacion = "—" if fila["variacion"] is None else f"{fila['variacion']:+.1f}%"
            tabla.setItem(i, 5, QTableWidgetItem(variacion))

    def _mostrar_aviso(self):
        aviso = self.controlador.aviso_renovacion(self.item_id)
        if aviso:
            self.label_aviso.setText("⚠ " + aviso)
            self.label_aviso.setProperty("class", "aviso")
        else:
            self.label_aviso.setText("")
            self.label_aviso.setProperty("class", "")
        # refresca el estilo para que tome (o suelte) el color de aviso
        self.label_aviso.style().unpolish(self.label_aviso)
        self.label_aviso.style().polish(self.label_aviso)

    def abrir_nuevo(self):
        dialogo = DialogoPrecio(self.controlador, self.item_id, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_precios()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

