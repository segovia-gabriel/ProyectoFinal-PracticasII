from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (QHeaderView, QWidget, QMessageBox,
                             QTableWidgetItem)

from controlador.consumo_controlador import ConsumoControlador
from utilidades import formato
from utilidades.validaciones import validar_rango_fechas
from vista.consumo.consumo_detalle_ventana import DialogoDetalleConsumo

RUTA_UI = Path(__file__).resolve().parent / "consumo.ui"


class VentanaConsumo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = ConsumoControlador()
        self._consumos = []   # lo ultimo listado, para resolver la fila elegida

        self.tableWidget_consumos.verticalHeader().setVisible(False)
        # Todas las columnas reparten el ancho por igual (sin huecos al maximizar).
        self.tableWidget_consumos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Rango por defecto: de ayer a hoy. Los consumos se cargan el mismo dia,
        # asi que al entrar se ven los mas recientes sin tener que filtrar.
        self.dateEdit_desde.setDate(QDate.currentDate().addDays(-1))
        self.dateEdit_hasta.setDate(QDate.currentDate())

        self.pushButton_buscar.clicked.connect(self.cargar_consumos)
        self.lineEdit_filtro.returnPressed.connect(self.cargar_consumos)
        self.pushButton_detalle.clicked.connect(self.ver_detalle)
        self.tableWidget_consumos.doubleClicked.connect(self.ver_detalle)

        self.cargar_consumos()

    def cargar_consumos(self):
        filtro = self.lineEdit_filtro.text().strip() or None
        desde = self.dateEdit_desde.date().toPyDate()
        hasta = self.dateEdit_hasta.date().toPyDate()
        valido, mensaje = validar_rango_fechas(desde, hasta)
        if not valido:
            QMessageBox.warning(self, "Rango de fechas invalido", mensaje)
            return
        exito, resultado = self.controlador.listar(filtro, desde, hasta)
        if not exito:
            QMessageBox.warning(self, "Error", resultado)
            return
        self._consumos = resultado
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
            tabla.setItem(fila, 4, QTableWidgetItem(formato.moneda(consumo['precio_total'])))
            estado = "Abierta" if consumo["estado"] == "abierta" else "Cerrada"
            tabla.setItem(fila, 5, QTableWidgetItem(estado))

    def _id_seleccionado(self):
        fila = self.tableWidget_consumos.currentRow()
        if fila < 0:
            return None
        return self.tableWidget_consumos.item(fila, 0).data(Qt.UserRole)

    def _consumo_seleccionado(self):
        fila = self.tableWidget_consumos.currentRow()
        if fila < 0 or fila >= len(self._consumos):
            return None
        return self._consumos[fila]

    def ver_detalle(self):
        consumo_id = self._id_seleccionado()
        if consumo_id is None:
            QMessageBox.warning(self, "Atencion", "Selecciona un consumo para ver el detalle.")
            return
        exito, detalle = self.controlador.obtener_detalle(consumo_id)
        if not exito:
            QMessageBox.warning(self, "Error", detalle)
            return
        DialogoDetalleConsumo(detalle, parent=self).exec_()
