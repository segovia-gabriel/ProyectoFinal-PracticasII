"""
Ventana de Estadisticas, con tres pestanas: Clientes, Reservas y Consumo. La de
Consumo depende del mes y ano elegidos (con boton Actualizar). Todo con tablas,
sin graficos, para que sea simple de mostrar y explicar. Al cerrarse vuelve la
ventana principal.
"""

from datetime import date
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import (QHeaderView, QWidget, QMessageBox,
                             QTableWidgetItem)

from controlador.estadisticas_controlador import EstadisticasControlador
from utilidades import formato

RUTA_UI = Path(__file__).resolve().parent / "estadisticas.ui"


class VentanaEstadisticas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = EstadisticasControlador()

        for tabla in (self.tableWidget_topClientes, self.tableWidget_reservasMes,
                      self.tableWidget_ingresos, self.tableWidget_topItems):
            tabla.verticalHeader().setVisible(False)
            # Columnas repartidas en partes iguales: con stretch solo en la
            # ultima, la primera quedaba angosta y cortaba los apellidos.
            tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Selector de periodo de la pestana Consumo: meses y ano actual.
        hoy = date.today()
        for numero in range(1, 13):
            self.comboBox_mes.addItem(formato.nombre_mes(numero), numero)
        self.comboBox_mes.setCurrentIndex(hoy.month - 1)
        self.spinBox_anio.setValue(hoy.year)

        self.pushButton_actualizar.clicked.connect(self.cargar_consumo)

        self.cargar_clientes()
        self.cargar_reservas()
        self.cargar_consumo()

    def cargar_clientes(self):
        exito, datos = self.controlador.clientes()
        if not exito:
            QMessageBox.warning(self, "Error", datos)
            return
        self.label_totalClientes.setText(f"Total de clientes: {datos['total']}")
        tabla = self.tableWidget_topClientes
        tabla.setRowCount(0)
        for fila, cliente in enumerate(datos["top"]):
            tabla.insertRow(fila)
            tabla.setItem(fila, 0, QTableWidgetItem(f"{cliente['apellido']}, {cliente['nombre']}"))
            tabla.setItem(fila, 1, QTableWidgetItem(str(cliente["cantidad"])))

    def cargar_reservas(self):
        exito, datos = self.controlador.reservas()
        if not exito:
            QMessageBox.warning(self, "Error", datos)
            return
        self.label_reservasFuturas.setText(
            f"Reservas actuales (hoy): {datos['actuales']}   |   "
            f"Reservas futuras: {datos['futuras']}   |   "
            f"Total: {datos['total']}"
        )
        tabla = self.tableWidget_reservasMes
        tabla.setRowCount(0)
        for fila, registro in enumerate(datos["por_mes"]):
            tabla.insertRow(fila)
            tabla.setItem(fila, 0, QTableWidgetItem(f"{registro['mes_nombre']} {registro['anio']}"))
            tabla.setItem(fila, 1, QTableWidgetItem(str(registro["cantidad"])))

    def cargar_consumo(self):
        mes = self.comboBox_mes.currentData()
        anio = self.spinBox_anio.value()
        exito, datos = self.controlador.consumo(anio, mes)
        if not exito:
            QMessageBox.warning(self, "Error", datos)
            return

        tabla_ing = self.tableWidget_ingresos
        tabla_ing.setRowCount(0)
        for fila, (dia, ingreso) in enumerate(datos["ingresos"]):
            tabla_ing.insertRow(fila)
            tabla_ing.setItem(fila, 0, QTableWidgetItem(dia))
            tabla_ing.setItem(fila, 1, QTableWidgetItem(formato.moneda(ingreso)))

        tabla_top = self.tableWidget_topItems
        tabla_top.setRowCount(0)
        for fila, (dia, item, cantidad) in enumerate(datos["top_items"]):
            tabla_top.insertRow(fila)
            tabla_top.setItem(fila, 0, QTableWidgetItem(dia))
            tabla_top.setItem(fila, 1, QTableWidgetItem(item))
            tabla_top.setItem(fila, 2, QTableWidgetItem(str(cantidad)))
