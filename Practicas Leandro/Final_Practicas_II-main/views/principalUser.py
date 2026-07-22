import sys
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint
from PyQt5.QtWidgets import QApplication, QMainWindow, QSizeGrip
from PyQt5.uic import loadUi
from PyQt5 import QtCore




class MainWindowUser(QMainWindow):   
    def __init__(self, parent=None):
        super(MainWindowUser, self).__init__(parent)
        # Cargar el archivo .ui que contiene la interfaz gráfica
        loadUi("ui\\menuUser.ui", self)
        

        # Eliminar la barra de título de la ventana y ajustar la opacidad
        self.setWindowFlags(Qt.FramelessWindowHint) 
        self.setWindowOpacity(1.0)  # Opacidad completa (1.0 es totalmente opaco)

        # SizeGrip para redimensionar la ventana desde la esquina inferior derecha
        self.gripSize = 10  # Tamaño del QSizeGrip
        self.grip = QSizeGrip(self)  # Crear el QSizeGrip
        self.grip.resize(self.gripSize, self.gripSize)  # Ajustar el tamaño del grip

        # Ocultar el menú lateral al inicio (iniciar con width=0)
        self.frame_lateral.setMinimumWidth(0)

        # Iniciar en la primera página (self.page)
        self.stackedWidget.setCurrentWidget(self.page)

        # Asignar el evento de mover la ventana al arrastrar el frame superior
        self.frame_superior.mouseMoveEvent = self.mover_ventana  
        
        # Configurar los botones para cambiar de páginas dentro de un stackedWidget
        self.bt_inicio.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page))			
        self.bt_uno.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_uno))
        self.bt_dos.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_dos))	
        self.bt_tres.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_tres))
        self.bt_cuatro.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_cuatro))			
        self.bt_cinco.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_cinco))	

        
        

        # Control de los botones de la barra de títulos (minimizar, maximizar/restaurar, cerrar)
        self.bt_minimizar.clicked.connect(self.control_bt_minimizar)		
        self.bt_restaurar.clicked.connect(self.control_bt_normal)
        self.bt_maximizar.clicked.connect(self.control_bt_maximizar)
        self.bt_cerrar.clicked.connect(lambda: self.close())

        # Ocultar el botón de restaurar por defecto, ya que no está maximizada
        self.bt_restaurar.hide()

        # Asignar el evento al botón del menú lateral para animarlo
        self.bt_menu.clicked.connect(self.mover_menu)





    #==============================================================================================================
    #                         Configuracion - [] X

    # Método para minimizar la ventana
    def control_bt_minimizar(self):
        self.showMinimized()		

    # Método para restaurar la ventana a tamaño normal (si estaba maximizada)
    def control_bt_normal(self): 
        self.showNormal()		
        self.bt_restaurar.hide()  # Ocultar botón restaurar
        self.bt_maximizar.show()  # Mostrar botón maximizar

    # Método para maximizar la ventana
    def control_bt_maximizar(self): 
        self.showMaximized()
        self.bt_maximizar.hide()  # Ocultar botón maximizar
        self.bt_restaurar.show()  # Mostrar botón restaurar

    # Método para mover el menú lateral con una animación
    def mover_menu(self):
        width = self.frame_lateral.width()  # Obtener el ancho actual del menú lateral
        normal = 0  # Ancho mínimo del menú cuando está colapsado
        extender = 200 if width == 0 else normal  # Extender a 200 si está colapsado, si no, reducir a 0
        
        # Animación para cambiar el tamaño del menú lateral
        self.animacion = QPropertyAnimation(self.frame_lateral, b'minimumWidth')
        self.animacion.setDuration(300)  # Duración de la animación en milisegundos
        self.animacion.setStartValue(width)  # Valor inicial (ancho actual)
        self.animacion.setEndValue(extender)  # Valor final (colapsado o extendido)
        self.animacion.setEasingCurve(QtCore.QEasingCurve.InOutQuart)  # Tipo de animación
        self.animacion.start()  # Iniciar la animación

    ## SizeGrip: Reposicionar el grip cuando la ventana se redimensiona
    def resizeEvent(self, event):
        rect = self.rect()  # Obtener el rectángulo actual de la ventana
        self.grip.move(rect.right() - self.gripSize, rect.bottom() - self.gripSize)  # Mover el grip a la esquina inferior derecha
    
    ## Mover la ventana al hacer clic en la parte superior y arrastrar
    def mousePressEvent(self, event):
        self.clickPosition = event.globalPos()  # Capturar la posición del cursor al hacer clic

    def mover_ventana(self, event):
        if not self.isMaximized():  # Solo permitir mover la ventana si no está maximizada
            if event.buttons() == Qt.LeftButton:  # Si se arrastra con el botón izquierdo
                self.move(self.pos() + event.globalPos() - self.clickPosition)  # Mover la ventana
                self.clickPosition = event.globalPos()  # Actualizar la posición del cursor
                event.accept()  # Aceptar el evento

        # Si se arrastra hacia la parte superior de la pantalla, maximizar la ventana
        if event.globalPos().y() <= 20:  
            self.showMaximized()
        else:
            self.showNormal()

    #==============================================================================================================




    #==============================================================================================================
    # 


def main():
    app = QApplication(sys.argv)  
    ventana = MainWindowUser()  
    ventana.show()  
    sys.exit(app.exec_())  

if __name__ == "__main__":
    main()

    

