from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from user_list_window import UserListWindow  # Importa la nueva clase


class MainWindow(QMainWindow):
    def __init__(self, nombre, email):
        super().__init__()
        uic.loadUi('ui/main_window.ui', self)
        self.label_nombre.setText(f'Nombre: {nombre}')
        self.label_email.setText(f'Email: {email}')
        self.pushButton_lista.clicked.connect(self.mostrar_lista_usuarios)

    def mostrar_lista_usuarios(self):
        self.hide()
        self.user_list_window = UserListWindow(self)  # Crea una instancia de UserListWindow
        self.user_list_window.show()
