"""
Ventana del Historial de acciones (solo lectura). Llena el combo de usuarios,
aplica los filtros de usuario y rango de fechas, y muestra las filas. Sigue el
patron del profesor: al cerrarse vuelve la ventana principal.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QHeaderView, QWidget, QMessageBox, QTableWidgetItem

from controlador.historial_controlador import HistorialControlador
from utilidades.validaciones import validar_rango_fechas

RUTA_UI = Path(__file__).resolve().parent / "historial.ui"


class VentanaHistorial(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = HistorialControlador()

        self.tableWidget_historial.verticalHeader().setVisible(False)
        # Todas las columnas reparten el ancho por igual (sin huecos al maximizar).
        self.tableWidget_historial.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.dateEdit_desde.setDate(QDate.currentDate().addDays(-30))
        self.dateEdit_hasta.setDate(QDate.currentDate())

        self._cargar_combo_usuarios()

        self.pushButton_filtrar.clicked.connect(self.cargar_historial)
        self.pushButton_limpiar.clicked.connect(self.limpiar)

        self.cargar_historial()

    def _cargar_combo_usuarios(self):
        # Primera opcion "Todos" (sin filtro); el resto guarda el id como data.
        self.comboBox_usuario.addItem("Todos", None)
        exito, resultado = self.controlador.listar_usuarios()
        if exito:
            for usuario_id, nombre in resultado:
                self.comboBox_usuario.addItem(nombre, usuario_id)

    def cargar_historial(self):
        usuario_id = self.comboBox_usuario.currentData()   # None si es "Todos"
        fecha_desde = self.dateEdit_desde.date().toPyDate()
        fecha_hasta = self.dateEdit_hasta.date().toPyDate()

        valido, mensaje = validar_rango_fechas(fecha_desde, fecha_hasta)
        if not valido:
            QMessageBox.warning(self, "Rango de fechas inválido", mensaje)
            return

        exito, resultado = self.controlador.listar(usuario_id, fecha_desde, fecha_hasta)
        if not exito:
            QMessageBox.warning(self, "Error", resultado)
            return

        tabla = self.tableWidget_historial
        tabla.setRowCount(0)
        for fila, registro in enumerate(resultado):
            tabla.insertRow(fila)
            tabla.setItem(fila, 0, QTableWidgetItem(registro["nombre_usuario"]))
            tabla.setItem(fila, 1, QTableWidgetItem(registro["accion"]))
            fecha = registro["fecha_hora"].strftime("%d/%m/%Y %H:%M")
            tabla.setItem(fila, 2, QTableWidgetItem(fecha))

    def limpiar(self):
        # Vuelve a los valores por defecto (todos los usuarios, rango amplio).
        self.comboBox_usuario.setCurrentIndex(0)
        self.dateEdit_desde.setDate(QDate.currentDate().addDays(-30))
        self.dateEdit_hasta.setDate(QDate.currentDate())
        self.cargar_historial()
