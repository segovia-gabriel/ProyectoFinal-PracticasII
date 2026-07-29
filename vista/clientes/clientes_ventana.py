"""
Ventana de Clientes. Listado con filtros (nombre/apellido y DNI), CRUD y acceso
a la vista de reservas de cada cliente. Al cerrarse vuelve la principal.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (QDialog, QHeaderView, QWidget, QMessageBox,
                             QTableWidgetItem)

from controlador.clientes_controlador import ClientesControlador
from utilidades.dialogos import confirmar_eliminacion
from utilidades.validaciones import validar_rango_fechas
from vista.clientes.cliente_form_ventana import DialogoCliente
from vista.clientes.cliente_reservas_ventana import DialogoReservasCliente

RUTA_UI = Path(__file__).resolve().parent / "clientes.ui"


class VentanaClientes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = ClientesControlador()

        self.tableWidget_clientes.verticalHeader().setVisible(False)
        # Todas las columnas reparten el ancho por igual (sin huecos al maximizar).
        self.tableWidget_clientes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # "Hasta" arranca en hoy: no hay clientes registrados a futuro.
        self.dateEdit_hasta.setDate(QDate.currentDate())

        self.pushButton_buscar.clicked.connect(self.cargar_clientes)
        self.lineEdit_filtroNombre.returnPressed.connect(self.cargar_clientes)
        self.lineEdit_filtroDni.returnPressed.connect(self.cargar_clientes)
        self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)
        self.pushButton_editar.clicked.connect(self.abrir_editar)
        self.pushButton_eliminar.clicked.connect(self.eliminar_seleccionado)
        self.pushButton_reservas.clicked.connect(self.ver_reservas)
        self.tableWidget_clientes.doubleClicked.connect(self.abrir_editar)

        self.cargar_clientes()

    def cargar_clientes(self):
        filtro_nombre = self.lineEdit_filtroNombre.text().strip() or None
        filtro_dni = self.lineEdit_filtroDni.text().strip() or None
        desde = self.dateEdit_desde.date().toPyDate()
        hasta = self.dateEdit_hasta.date().toPyDate()
        # El "Desde" no puede quedar despues del "Hasta".
        valido, mensaje = validar_rango_fechas(desde, hasta)
        if not valido:
            QMessageBox.warning(self, "Rango de fechas invalido", mensaje)
            return
        exito, resultado = self.controlador.listar(filtro_nombre, filtro_dni, desde, hasta)
        if not exito:
            QMessageBox.warning(self, "Error", resultado)
            return

        tabla = self.tableWidget_clientes
        tabla.setRowCount(0)
        for fila, cliente in enumerate(resultado):
            tabla.insertRow(fila)
            item_apellido = QTableWidgetItem(cliente["apellido"])
            item_apellido.setData(Qt.UserRole, cliente["id"])
            tabla.setItem(fila, 0, item_apellido)
            tabla.setItem(fila, 1, QTableWidgetItem(cliente["nombre"]))
            tabla.setItem(fila, 2, QTableWidgetItem(cliente["dni"]))
            tabla.setItem(fila, 3, QTableWidgetItem(cliente["fecha_nacimiento"].strftime("%d/%m/%Y")))
            tabla.setItem(fila, 4, QTableWidgetItem(cliente["telefono"] or "—"))
            tabla.setItem(fila, 5, QTableWidgetItem(cliente["fecha_registro"].strftime("%d/%m/%Y")))

    def _id_seleccionado(self):
        fila = self.tableWidget_clientes.currentRow()
        if fila < 0:
            return None
        return self.tableWidget_clientes.item(fila, 0).data(Qt.UserRole)

    def abrir_nuevo(self):
        dialogo = DialogoCliente(self.controlador, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_clientes()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def abrir_editar(self):
        cliente_id = self._id_seleccionado()
        if cliente_id is None:
            QMessageBox.warning(self, "Atencion", "Selecciona un cliente para editar.")
            return
        exito, cliente = self.controlador.obtener(cliente_id)
        if not exito or cliente is None:
            QMessageBox.warning(self, "Error", "No se pudo abrir el cliente.")
            return
        dialogo = DialogoCliente(self.controlador, cliente=cliente, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_clientes()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def eliminar_seleccionado(self):
        cliente_id = self._id_seleccionado()
        if cliente_id is None:
            QMessageBox.warning(self, "Atencion", "Selecciona un cliente para eliminar.")
            return
        if not confirmar_eliminacion(self, "¿Seguro que queres eliminar este cliente?"):
            return
        exito, mensaje = self.controlador.eliminar(cliente_id)
        if exito:
            QMessageBox.information(self, "Listo", mensaje)
            self.cargar_clientes()
        else:
            QMessageBox.warning(self, "No se pudo eliminar", mensaje)

    def ver_reservas(self):
        cliente_id = self._id_seleccionado()
        if cliente_id is None:
            QMessageBox.warning(self, "Atencion", "Selecciona un cliente para ver sus reservas.")
            return
        exito, cliente = self.controlador.obtener(cliente_id)
        if not exito or cliente is None:
            QMessageBox.warning(self, "Error", "No se pudo abrir el cliente.")
            return
        ok, reservas = self.controlador.listar_reservas(cliente_id)
        if not ok:
            QMessageBox.warning(self, "Error", reservas)
            return
        nombre = f"{cliente['apellido']}, {cliente['nombre']}"
        DialogoReservasCliente(nombre, reservas, parent=self).exec_()
