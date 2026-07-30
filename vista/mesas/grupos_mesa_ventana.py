from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QMessageBox, QTableWidgetItem

from controlador.mesas_controlador import MesasControlador
from vista.mesas.grupo_mesa_form_ventana import DialogoGrupoMesa
from utilidades.dialogos import confirmar_eliminacion
from utilidades import formato

RUTA_UI = Path(__file__).resolve().parent / "grupos_mesa.ui"


class VentanaGruposMesa(QDialog):
    def __init__(self, controlador=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        # Reutiliza el mismo controlador que la ventana de Mesas si se lo pasan.
        self.controlador = controlador or MesasControlador()
        self.label_ayuda.setProperty("class", "ayuda")

        self.tableWidget_grupos.verticalHeader().setVisible(False)
        self.tableWidget_grupos.horizontalHeader().setStretchLastSection(True)

        self.pushButton_buscar.clicked.connect(self.cargar_grupos)
        self.lineEdit_filtro.returnPressed.connect(self.cargar_grupos)
        self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)
        self.pushButton_editar.clicked.connect(self.abrir_editar)
        self.pushButton_eliminar.clicked.connect(self.eliminar_seleccionado)
        self.pushButton_volver.clicked.connect(self.close)
        self.tableWidget_grupos.doubleClicked.connect(self.abrir_editar)

        self.cargar_grupos()

    def cargar_grupos(self):
        filtro = self.lineEdit_filtro.text().strip() or None
        exito, resultado = self.controlador.listar_grupos(filtro)
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
            tabla.setItem(fila, 1, QTableWidgetItem(formato.moneda(valor_2h)))
            # El valor de 3h no se guarda: es 125% del de 2h, calculado al vuelo.
            tabla.setItem(fila, 2, QTableWidgetItem(formato.moneda(valor_2h * 1.25)))

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
            QMessageBox.warning(self, "Atencion", "Selecciona un grupo para editar.")
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
            QMessageBox.warning(self, "Atencion", "Selecciona un grupo para eliminar.")
            return
        if not confirmar_eliminacion(self, "¿Seguro que queres eliminar este grupo?"):
            return
        exito, mensaje = self.controlador.eliminar_grupo(grupo_id)
        if exito:
            QMessageBox.information(self, "Listo", mensaje)
            self.cargar_grupos()
        else:
            QMessageBox.warning(self, "No se pudo eliminar", mensaje)

