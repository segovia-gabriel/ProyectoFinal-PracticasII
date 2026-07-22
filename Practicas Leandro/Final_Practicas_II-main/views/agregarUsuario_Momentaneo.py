import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout, QWidget

class ClaseAgregarUsuarioMomentaneo(QMainWindow):
    def __init__(self, parent=None):
        super(ClaseAgregarUsuarioMomentaneo, self).__init__(parent)
        self.setWindowTitle("Agregar Usuario")
        self.setGeometry(100, 100, 500, 300)
        self.setup_ui()

    def setup_ui(self):
        # Crear widgets
        self.label_nombre = QLabel("Nombre")
        self.line_edit_nombre = QLineEdit()
        self.line_edit_nombre.setMinimumHeight(30)

        self.label_contrasenia = QLabel("Contraseña")
        self.line_edit_contrasenia = QLineEdit()
        self.line_edit_contrasenia.setMinimumHeight(30)
        self.line_edit_contrasenia.setEchoMode(QLineEdit.Password)

        self.combo_box = QComboBox()
        self.combo_box.setMinimumHeight(30)
        self.combo_box.addItems(["Administrador", "Usuario Común"])

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setMinimumHeight(30)
        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.setMinimumHeight(30)

        # Layouts
        layout = QVBoxLayout()
        layout.addWidget(self.label_nombre)
        layout.addWidget(self.line_edit_nombre)
        layout.addWidget(self.label_contrasenia)
        layout.addWidget(self.line_edit_contrasenia)
        layout.addWidget(self.combo_box)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_cancelar)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_agregar)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

def main():
    app = QApplication(sys.argv)
    ventana = ClaseAgregarUsuarioMomentaneo()
    ventana.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
