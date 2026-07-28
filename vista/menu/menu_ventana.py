"""
Ventana de Menú (items). Listado con precio vigente y acceso a Grupos de menú y
a Precios de cada item. Al cerrarse vuelve la ventana principal.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QHeaderView, QMainWindow, QMessageBox,
                             QTableWidgetItem)

from controlador.menu_controlador import MenuControlador
from vista.menu.menu_form_ventana import DialogoItemMenu
from vista.menu.grupos_menu_ventana import VentanaGruposMenu
from vista.menu.precios_ventana import VentanaPrecios
from utilidades.dialogos import confirmar_eliminacion
from utilidades import formato

RUTA_UI = Path(__file__).resolve().parent / "menu.ui"


class VentanaMenu(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = MenuControlador()

        self.tableWidget_menu.verticalHeader().setVisible(False)
        # Nombre, grupo y precio se ajustan a su contenido; la descripcion, que
        # es el texto mas largo, se queda con lo que sobra.
        cabecera = self.tableWidget_menu.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(3, QHeaderView.Stretch)

        self.pushButton_buscar.clicked.connect(self.cargar_items)
        self.lineEdit_filtro.returnPressed.connect(self.cargar_items)
        self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)
        self.pushButton_editar.clicked.connect(self.abrir_editar)
        self.pushButton_eliminar.clicked.connect(self.eliminar_seleccionado)
        self.pushButton_grupos.clicked.connect(self.abrir_grupos)
        self.pushButton_precios.clicked.connect(self.abrir_precios)
        self.pushButton_volver.clicked.connect(self.close)
        self.tableWidget_menu.doubleClicked.connect(self.abrir_editar)

        self.cargar_items()

    def cargar_items(self):
        filtro = self.lineEdit_filtro.text().strip() or None
        exito, resultado = self.controlador.listar_items(filtro)
        if not exito:
            QMessageBox.warning(self, "Error", resultado)
            return

        tabla = self.tableWidget_menu
        tabla.setRowCount(0)
        for fila, item in enumerate(resultado):
            tabla.insertRow(fila)
            item_nombre = QTableWidgetItem(item["nombre"])
            item_nombre.setData(Qt.UserRole, item["id"])
            tabla.setItem(fila, 0, item_nombre)
            tabla.setItem(fila, 1, QTableWidgetItem(item["grupo_nombre"]))
            precio = item["precio_vigente"]
            tabla.setItem(fila, 2, QTableWidgetItem(formato.moneda(precio)))
            tabla.setItem(fila, 3, QTableWidgetItem(item["descripcion"] or "—"))

    def _id_seleccionado(self):
        fila = self.tableWidget_menu.currentRow()
        if fila < 0:
            return None
        return self.tableWidget_menu.item(fila, 0).data(Qt.UserRole)

    def abrir_nuevo(self):
        dialogo = DialogoItemMenu(self.controlador, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_items()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def abrir_editar(self):
        item_id = self._id_seleccionado()
        if item_id is None:
            QMessageBox.warning(self, "Atención", "Seleccioná un ítem para editar.")
            return
        exito, item = self.controlador.obtener_item(item_id)
        if not exito or item is None:
            QMessageBox.warning(self, "Error", "No se pudo abrir el ítem.")
            return
        dialogo = DialogoItemMenu(self.controlador, item=item, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_items()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def eliminar_seleccionado(self):
        item_id = self._id_seleccionado()
        if item_id is None:
            QMessageBox.warning(self, "Atención", "Seleccioná un ítem para eliminar.")
            return
        if not confirmar_eliminacion(self, "¿Seguro que querés eliminar este ítem?"):
            return
        exito, mensaje = self.controlador.eliminar_item(item_id)
        if exito:
            QMessageBox.information(self, "Listo", mensaje)
            self.cargar_items()
        else:
            QMessageBox.warning(self, "No se pudo eliminar", mensaje)

    def abrir_grupos(self):
        self.hide()
        self.ventana_grupos = VentanaGruposMenu(self.controlador, self)
        self.ventana_grupos.show()

    def abrir_precios(self):
        item_id = self._id_seleccionado()
        if item_id is None:
            QMessageBox.warning(self, "Atención", "Seleccioná un ítem para ver sus precios.")
            return
        exito, item = self.controlador.obtener_item(item_id)
        if not exito or item is None:
            QMessageBox.warning(self, "Error", "No se pudo abrir el ítem.")
            return
        self.hide()
        self.ventana_precios = VentanaPrecios(item, self.controlador, self)
        self.ventana_precios.show()

    def closeEvent(self, evento):
        if self.parent() is not None:
            self.parent().show()
        evento.accept()
