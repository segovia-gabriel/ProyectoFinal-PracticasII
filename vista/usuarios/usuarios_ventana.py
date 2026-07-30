from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QHeaderView, QWidget, QMessageBox,
                             QTableWidgetItem)

from controlador.usuarios_controlador import UsuariosControlador
from vista.usuarios.usuario_form_ventana import DialogoUsuario
from utilidades.dialogos import confirmar_eliminacion

RUTA_UI = Path(__file__).resolve().parent / "usuarios.ui"


class VentanaUsuarios(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = UsuariosControlador()

        # La numeracion de filas de la izquierda no aporta nada y compite con el
        # encabezado, asi que la oculto. Todas las columnas reparten el ancho por
        # igual, asi no queda una gigante con la ventana maximizada.
        self.tableWidget_usuarios.verticalHeader().setVisible(False)
        self.tableWidget_usuarios.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.pushButton_buscar.clicked.connect(self.cargar_usuarios)
        self.lineEdit_filtro.returnPressed.connect(self.cargar_usuarios)
        self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)
        self.pushButton_editar.clicked.connect(self.abrir_editar)
        self.pushButton_eliminar.clicked.connect(self.eliminar_seleccionado)
        # Doble clic en una fila abre la edicion, que es lo que uno espera de una tabla.
        self.tableWidget_usuarios.doubleClicked.connect(self.abrir_editar)

        self.cargar_usuarios()

    def cargar_usuarios(self):
        filtro = self.lineEdit_filtro.text().strip() or None
        exito, resultado = self.controlador.listar(filtro)
        if not exito:
            QMessageBox.warning(self, "Error", resultado)
            return

        tabla = self.tableWidget_usuarios
        tabla.setRowCount(0)
        for fila, usuario in enumerate(resultado):
            tabla.insertRow(fila)
            item_nombre = QTableWidgetItem(usuario["nombre_usuario"])
            # Guardo el id (invisible) en el item para saber a quien editar o borrar.
            item_nombre.setData(Qt.UserRole, usuario["id"])
            tabla.setItem(fila, 0, item_nombre)
            tabla.setItem(fila, 1, QTableWidgetItem(self._fecha(usuario["fecha_creacion"])))
            tabla.setItem(fila, 2, QTableWidgetItem(self._fecha(usuario["fecha_modificacion"])))
            tabla.setItem(fila, 3, QTableWidgetItem(self._fecha(usuario["fecha_ultimo_acceso"])))

    def _fecha(self, valor):
        # Las fechas opcionales (modificacion, ultimo acceso) pueden venir None.
        return valor.strftime("%d/%m/%Y %H:%M") if valor else "—"

    def _id_seleccionado(self):
        # Devuelve el id del usuario de la fila seleccionada, o None si no hay.
        fila = self.tableWidget_usuarios.currentRow()
        if fila < 0:
            return None
        return self.tableWidget_usuarios.item(fila, 0).data(Qt.UserRole)

    def abrir_nuevo(self):
        dialogo = DialogoUsuario(self.controlador, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_usuarios()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def abrir_editar(self):
        usuario_id = self._id_seleccionado()
        if usuario_id is None:
            QMessageBox.warning(self, "Atencion", "Selecciona un usuario para editar.")
            return

        exito, usuario = self.controlador.obtener(usuario_id)
        if not exito or usuario is None:
            QMessageBox.warning(self, "Error", "No se pudo abrir el usuario.")
            return

        dialogo = DialogoUsuario(self.controlador, usuario=usuario, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_usuarios()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)

    def eliminar_seleccionado(self):
        usuario_id = self._id_seleccionado()
        if usuario_id is None:
            QMessageBox.warning(self, "Atencion", "Selecciona un usuario para eliminar.")
            return

        if not confirmar_eliminacion(self, "¿Seguro que queres eliminar este usuario?"):
            return

        exito, mensaje = self.controlador.eliminar(usuario_id)
        if exito:
            QMessageBox.information(self, "Listo", mensaje)
            self.cargar_usuarios()
        else:
            QMessageBox.warning(self, "No se pudo eliminar", mensaje)
