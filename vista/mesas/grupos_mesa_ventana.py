"""
Ventana de Grupos de mesa. Se abre desde la ventana de Mesas. Muestra el valor
de 2h (el guardado) y el de 3h calculado (125%). Al cerrarse vuelve a Mesas.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHeaderView, QMainWindow, QMessageBox, QTableWidgetItem

from controlador.mesas_controlador import MesasControlador
from vista.mesas.grupo_mesa_form_ventana import DialogoGrupoMesa

RUTA_UI = Path(__file__).resolve().parent / "grupos_mesa.ui"


class VentanaGruposMesa(QMainWindow):
    def __init__(self, controlador=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        # Reutiliza el mismo controlador que la ventana de Mesas si se lo pasan.
        self.controlador = controlador or MesasControlador()
        self.label_ayuda.setProperty("class", "ayuda")

        self.tableWidget_grupos.verticalHeader().setVisible(False)
        self.tableWidget_grupos.horizontalHeader().setStretchLastSection(True)

        self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)
        self.pushButton_editar.clicked.connect(self.abrir_editar)
        self.pushButton_eliminar.clicked.connect(self.eliminar_seleccionado)
        self.pushButton_volver.clicked.connect(self.close)
        self.tableWidget_grupos.doubleClicked.connect(self.abrir_editar)

        self.cargar_grupos()

    def cargar_grupos(self):
        exito, resultado = self.controlador.listar_grupos()
        if not exito:
            QMessageBox.warning(self, "Error", resultado)
            return

        tabla = self.tableWidget_grupos
        tabla.setRowCount(0)
        for fila, grupo in enumerate(resultado):
            tabla.insertRow(fila)
            item_nombre = QTableWidgetItem(grupo["nombre"])
            item_nombre.setData(Qt.UserRole, grupo["id"])
            tabla.setItem(fila, 0, item_nombre)
            valor_2h = float(grupo["valor"])
            tabla.setItem(fila, 1, QTableWidgetItem(f"$ {valor_2h:,.2f}"))
            # El valor de 3h no se guarda: es 125% del de 2h, calculado al vuelo.
            tabla.setItem(fila, 2, QTableWidgetItem(f"$ {valor_2h * 1.25:,.2f}"))

    def _id_seleccionado(self):
        fila = self.tableWidget_grupos.currentRow()
        if fila < 0:
            return None
        return self.tableWidget_grupos.item(fila, 0).data(Qt.UserRole)

    def abrir_nuevo(self):
        dialogo = DialogoGrupoMesa(self.controlador, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_grupos()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def abrir_editar(self):
        grupo_id = self._id_seleccionado()
        if grupo_id is None:
            QMessageBox.warning(self, "Atención", "Seleccioná un grupo para editar.")
            return
        exito, grupo = self.controlador.obtener_grupo(grupo_id)
        if not exito or grupo is None:
            QMessageBox.warning(self, "Error", "No se pudo abrir el grupo.")
            return
        dialogo = DialogoGrupoMesa(self.controlador, grupo=grupo, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_grupos()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def eliminar_seleccionado(self):
        grupo_id = self._id_seleccionado()
        if grupo_id is None:
            QMessageBox.warning(self, "Atención", "Seleccioná un grupo para eliminar.")
            return
        confirmar = QMessageBox.question(
            self, "Confirmar", "¿Seguro que querés eliminar este grupo?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if confirmar != QMessageBox.Yes:
            return
        exito, mensaje = self.controlador.eliminar_grupo(grupo_id)
        if exito:
            QMessageBox.information(self, "Listo", mensaje)
            self.cargar_grupos()
        else:
            QMessageBox.warning(self, "No se pudo eliminar", mensaje)

    def closeEvent(self, evento):
        if self.parent() is not None:
            self.parent().show()
        evento.accept()
