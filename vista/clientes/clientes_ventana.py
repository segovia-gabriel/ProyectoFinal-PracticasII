"""
Ventana de Clientes. Listado con filtros (nombre/apellido y DNI), CRUD y acceso
a la vista de reservas de cada cliente. Al cerrarse vuelve la principal.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QMainWindow, QMessageBox, QTableWidgetItem

from controlador.clientes_controlador import ClientesControlador
from vista.clientes.cliente_form_ventana import DialogoCliente
from vista.clientes.cliente_reservas_ventana import DialogoReservasCliente

RUTA_UI = Path(__file__).resolve().parent / "clientes.ui"


class VentanaClientes(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = ClientesControlador()

        self.tableWidget_clientes.verticalHeader().setVisible(False)
        self.tableWidget_clientes.horizontalHeader().setStretchLastSection(True)

        self.pushButton_buscar.clicked.connect(self.cargar_clientes)
        self.lineEdit_filtroNombre.returnPressed.connect(self.cargar_clientes)
        self.lineEdit_filtroDni.returnPressed.connect(self.cargar_clientes)
        self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)
        self.pushButton_editar.clicked.connect(self.abrir_editar)
        self.pushButton_eliminar.clicked.connect(self.eliminar_seleccionado)
        self.pushButton_reservas.clicked.connect(self.ver_reservas)
        self.pushButton_volver.clicked.connect(self.close)
        self.tableWidget_clientes.doubleClicked.connect(self.abrir_editar)

        self.cargar_clientes()

    def cargar_clientes(self):
        filtro_nombre = self.lineEdit_filtroNombre.text().strip() or None
        filtro_dni = self.lineEdit_filtroDni.text().strip() or None
        exito, resultado = self.controlador.listar(filtro_nombre, filtro_dni)
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
            QMessageBox.warning(self, "Atención", "Seleccioná un cliente para editar.")
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
            QMessageBox.warning(self, "Atención", "Seleccioná un cliente para eliminar.")
            return
        confirmar = QMessageBox.question(
            self, "Confirmar", "¿Seguro que querés eliminar este cliente?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if confirmar != QMessageBox.Yes:
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
            QMessageBox.warning(self, "Atención", "Seleccioná un cliente para ver sus reservas.")
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

    def closeEvent(self, evento):
        if self.parent() is not None:
            self.parent().show()
        evento.accept()
