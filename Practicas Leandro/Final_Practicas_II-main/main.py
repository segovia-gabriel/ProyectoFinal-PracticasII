import sys
from PyQt5.QtWidgets import QApplication
from views.login import ClaseLogin 

def main():
    app = QApplication(sys.argv)
    
    # Crear instancia de la ventana de login
    ventana_login = ClaseLogin()
    ventana_login.show()
    
    # Ejecutar la aplicación
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
