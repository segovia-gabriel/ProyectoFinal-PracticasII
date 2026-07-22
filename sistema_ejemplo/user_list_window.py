from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox
from create_user_window import CreateUserWindow
from edit_user_window import EditUserWindow
from util.session import UserSession
from python_mysql_config import config_db
from mysql.connector import MySQLConnection


class UserListWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('ui/user_list.ui', self)
        self.pushButton_crear.clicked.connect(self.crear_usuario)
        self.pushButton_editar.clicked.connect(self.editar_usuario)
        self.pushButton_eliminar.clicked.connect(self.eliminar_usuario)
        self.cargar_usuarios()

    def cargar_usuarios(self):
        db_config = config_db()
        db = MySQLConnection(**db_config)
        cursor = db.cursor()
        cursor.execute("SELECT nombre, email, rol FROM usuarios")
        resultados = cursor.fetchall()
        db.close()

        self.tableWidget.setRowCount(0)  # Limpiar la tabla

        for row_num, row_data in enumerate(resultados):
            self.tableWidget.insertRow(row_num)
            for column_num, data in enumerate(row_data):
                self.tableWidget.setItem(row_num, column_num, QTableWidgetItem(str(data)))

    def crear_usuario(self):
        self.create_user_window = CreateUserWindow(self)
        self.create_user_window.show()

    def editar_usuario(self):
        fila_seleccionada = self.tableWidget.currentRow()
        if fila_seleccionada == -1:
            QMessageBox.warning(self, 'Error', 'No hay usuario seleccionado.')
            return

        nombre = self.tableWidget.item(fila_seleccionada, 0).text()
        email = self.tableWidget.item(fila_seleccionada, 1).text()
        rol = self.tableWidget.item(fila_seleccionada, 2).text()

        user_data = (nombre, email, rol)
        self.edit_user_window = EditUserWindow(self, user_data)
        self.edit_user_window.show()

    def eliminar_usuario(self):
        fila_seleccionada = self.tableWidget.currentRow()
        if fila_seleccionada == -1:
            QMessageBox.warning(self, 'Error', 'No hay usuario seleccionado.')
            return

        email_usuario_seleccionado = self.tableWidget.item(fila_seleccionada, 1).text()

        # Acceder a la sesión para verificar el usuario logueado
        session = UserSession()
        if email_usuario_seleccionado == session.email:
            QMessageBox.warning(self, 'Error', 'No puedes eliminar tu propio usuario.')
            return

        # Confirmación de eliminación
        confirmacion = QMessageBox.question(
            self, 'Confirmar Eliminación',
            '¿Estás seguro de que deseas eliminar este usuario?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if confirmacion == QMessageBox.Yes:
            email = self.tableWidget.item(fila_seleccionada, 1).text()  # Asumimos que el email está en la segunda columna

            db_config = config_db()
            db = MySQLConnection(**db_config)
            cursor = db.cursor()
            cursor.execute("DELETE FROM usuarios WHERE email=%s", (email,))
            db.commit()
            db.close()

            QMessageBox.information(self, 'Éxito', 'Usuario eliminado exitosamente.')
            self.cargar_usuarios()  # Actualiza la lista de usuarios después de la eliminación

    def closeEvent(self, event):
        self.parent().show()  # Mostrar el dashboard al cerrar el listado de usuarios
        event.accept()
