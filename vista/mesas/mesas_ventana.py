from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QHeaderView, QWidget, QMessageBox,
                             QTableWidgetItem)

from controlador.mesas_controlador import MesasControlador
from vista.mesas.mesa_form_ventana import DialogoMesa
from vista.mesas.grupos_mesa_ventana import VentanaGruposMesa
from utilidades.dialogos import confirmar_eliminacion

RUTA_UI = Path(__file__).resolve().parent / "mesas.ui"


class VentanaMesas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = MesasControlador()

        self.tableWidget_mesas.verticalHeader().setVisible(False)
        # Todas las columnas reparten el ancho por igual (sin huecos al maximizar).
        self.tableWidget_mesas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.pushButton_buscar.clicked.connect(self.cargar_mesas)
        self.lineEdit_filtro.returnPressed.connect(self.cargar_mesas)
        self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)
        self.pushButton_editar.clicked.connect(self.abrir_editar)
        self.pushButton_eliminar.clicked.connect(self.eliminar_seleccionado)
        self.pushButton_grupos.clicked.connect(self.abrir_grupos)
        self.tableWidget_mesas.doubleClicked.connect(self.abrir_editar)

        self.cargar_mesas()

    def cargar_mesas(self):
        filtro = self.lineEdit_filtro.text().strip() or None
        exito, resultado = self.controlador.listar_mesas(filtro)
        if not exito:
            QMessageBox.warning(self, "Error", resultado)
            return

        tabla = self.tableWidget_mesas
        tabla.setRowCount(0)
        for fila, mesa in enumerate(resultado):
            tabla.insertRow(fila)
            item_numero = QTableWidgetItem(str(mesa["numero_mesa"]))
            item_numero.setData(Qt.UserRole, mesa["id"])
            tabla.setItem(fila, 0, item_numero)
            tabla.setItem(fila, 1, QTableWidgetItem(mesa["codigo"]))
            tabla.setItem(fila, 2, QTableWidgetItem(str(mesa["numero_sillas"])))
            tabla.setItem(fila, 3, QTableWidgetItem(str(mesa["piso"])))
            tabla.setItem(fila, 4, QTableWidgetItem(mesa["grupo_nombre"]))

    def _id_seleccionado(self):
        fila = self.tableWidget_mesas.currentRow()
        if fila < 0:
            return None
        return self.tableWidget_mesas.item(fila, 0).data(Qt.UserRole)

    def abrir_nuevo(self):
        dialogo = DialogoMesa(self.controlador, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_mesas()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def abrir_editar(self):
        mesa_id = self._id_seleccionado()
        if mesa_id is None:
            QMessageBox.warning(self, "Atencion", "Selecciona una mesa para editar.")
            return
        exito, mesa = self.controlador.obtener_mesa(mesa_id)
        if not exito or mesa is None:
            QMessageBox.warning(self, "Error", "No se pudo abrir la mesa.")
            return
        dialogo = DialogoMesa(self.controlador, mesa=mesa, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_mesas()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def eliminar_seleccionado(self):
        mesa_id = self._id_seleccionado()
        if mesa_id is None:
            QMessageBox.warning(self, "Atencion", "Selecciona una mesa para eliminar.")
            return
        if not confirmar_eliminacion(self, "¿Seguro que queres eliminar esta mesa?"):
            return
        exito, mensaje = self.controlador.eliminar_mesa(mesa_id)
        if exito:
            QMessageBox.information(self, "Listo", mensaje)
            self.cargar_mesas()
        else:
            QMessageBox.warning(self, "No se pudo eliminar", mensaje)

    def abrir_grupos(self):
        # Sub-pantalla como dialogo modal encima de la ventana unica.
        VentanaGruposMesa(self.controlador, self).exec_()
