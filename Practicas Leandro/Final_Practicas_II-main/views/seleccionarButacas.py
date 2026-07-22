import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QGridLayout, QGroupBox, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from database.conexion import Database
from views.session import UserSession

# Subclase de QLabel para manejar eventos de clic
class ClickableLabel(QLabel):
    clicked = pyqtSignal()  # Señal personalizada que se emite cuando se hace clic

    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)

    def mousePressEvent(self, event):
        """Detecta el evento de clic y emite la señal."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # Emitir señal al hacer clic
        super(ClickableLabel, self).mousePressEvent(event)

class Cine(QMainWindow):
    def __init__(self, id_funcion, parent=None):
        super(Cine, self).__init__(parent)
        self.id_funcion = id_funcion
        self.accion="Vendio una Entrada/s"
        self.db = Database()  
        
        # Cargar los asientos reservados desde la base de datos
        asientos_reservados = self.db.obtener_asientos_reservados(self.id_funcion)
        self.asientos_disponibles = [i + 1 not in asientos_reservados for i in range(30)]  # 30 asientos en total

        # Configuración de la ventana principal
        self.setWindowTitle("Venta de Entradas de Cine")
        self.setGeometry(100, 100, 600, 600)

        # Crear los elementos de la UI
        self.boton_comprar = QPushButton("Comprar")
        self.boton_comprar.clicked.connect(self.comprar_asientos)
        self.boton_comprar.setFont(QFont("Arial", 12))

        # Configuración del grupo de asientos
        self.grupo_asientos = QGroupBox("Selecciona tus asientos")
        self.grupo_asientos.setFont(QFont("Arial", 12))
        self.layout_asientos = QGridLayout()
        self.grupo_asientos.setLayout(self.layout_asientos)

        # Layout principal
        layout_principal = QVBoxLayout()
        layout_principal.addWidget(self.grupo_asientos)
        layout_principal.addWidget(self.boton_comprar)

        # Configurar el widget central
        widget_central = QWidget()
        widget_central.setLayout(layout_principal)
        self.setCentralWidget(widget_central)

        # Inicializar la lista de checkboxes para los asientos
        self.asientos_checkboxes = []
        self.actualizar_asientos()

    def actualizar_asientos(self):
        """Actualiza la disposición de los asientos."""
        # Limpiar la cuadrícula de asientos antes de actualizar
        for i in reversed(range(self.layout_asientos.count())):
            widget = self.layout_asientos.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.asientos_checkboxes.clear()  # Limpiar la lista de checkboxes

        # Crear los asientos en una cuadrícula (5 filas por 6 columnas)
        filas = 5
        columnas = 6
        asiento_numero = 0

        for fila in range(filas):
            for columna in range(columnas):
                if asiento_numero < len(self.asientos_disponibles):
                    # Crear un checkbox para el asiento
                    checkbox = QCheckBox(f"Asiento {asiento_numero + 1}")
                    checkbox.setFont(QFont("Arial", 12))

                    # Deshabilitar si el asiento ya está reservado
                    checkbox.setEnabled(self.asientos_disponibles[asiento_numero])

                    # Crear un QLabel para mostrar la imagen del asiento (ClickableLabel)
                    label_asiento = ClickableLabel(self)

                    # Cargar la imagen desde el archivo
                    pixmap = QPixmap("icons\\butacas.png")  # Cambiar ruta según la ubicación de la imagen
                    label_asiento.setPixmap(pixmap)

                    # Ajustar el tamaño máximo del QLabel (para que la imagen no sea muy grande)
                    label_asiento.setFixedSize(50, 50)  # Cambia este valor para ajustar el tamaño
                    label_asiento.setScaledContents(True)

                    # Conectar el clic de la imagen para alternar el checkbox
                    label_asiento.clicked.connect(lambda chk=checkbox: chk.setChecked(not chk.isChecked()))

                    # Crear un layout vertical para superponer el número sobre la imagen
                    layout_asiento = QVBoxLayout()
                    layout_asiento.addWidget(label_asiento)
                    layout_asiento.addWidget(checkbox)
                    layout_asiento.setAlignment(Qt.AlignCenter)

                    # Crear un widget contenedor para el layout del asiento
                    widget_asiento = QWidget()
                    widget_asiento.setLayout(layout_asiento)

                    # Agregar el widget de asiento al grid layout
                    self.layout_asientos.addWidget(widget_asiento, fila, columna)

                    # Almacenar el checkbox para verificar más tarde
                    self.asientos_checkboxes.append(checkbox)
                    asiento_numero += 1

    def comprar_asientos(self):
        """Realiza la compra de los asientos seleccionados y guarda en la base de datos."""
        asientos_a_comprar = []
        for i, checkbox in enumerate(self.asientos_checkboxes):
            if checkbox.isChecked() and self.asientos_disponibles[i]:
                asientos_a_comprar.append(i)

        if not asientos_a_comprar:
            QMessageBox.warning(self, "Error", "No has seleccionado asientos o los seleccionados ya están reservados.")
            return

        # Llama a la función para guardar los asientos en la base de datos

        try:
            sesion= UserSession()
            id_user = sesion.get_user_id()
            self.db.guardar_asientos(self.id_funcion, id_user, asientos=[a + 1 for a in asientos_a_comprar])  
            QMessageBox.information(self, "Éxito", f"Has reservado los asientos: {', '.join([str(a + 1) for a in asientos_a_comprar])}.")
            self.db.registrar_historial_usuario(id_user,self.accion)
            self.close()
            # Actualizar la lista de asientos disponibles
            # for asiento in asientos_a_comprar:
            #     self.asientos_disponibles[asiento] = False
            # self.actualizar_asientos()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

def main():
    app = QApplication(sys.argv)
    id_funcion = 1  # Este valor se debe pasar de forma dinámica
    ventana = Cine(id_funcion)
    ventana.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
