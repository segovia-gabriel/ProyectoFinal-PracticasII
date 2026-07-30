"""
El arranque de la app. Crea la QApplication, le mete la hoja de estilos una
sola vez para todas las pantallas y abre el login.
"""

import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from vista.login_ventana import VentanaLogin

RUTA_ESTILO = Path(__file__).resolve().parent / "recursos" / "style.css"


def main():
    app = QApplication(sys.argv)

    # Un solo setStyleSheet para toda la app, asi todas las pantallas usan el
    # mismo QSS. Si no encuentra el archivo no pasa nada, sigue con el look default de Qt.
    try:
        app.setStyleSheet(RUTA_ESTILO.read_text(encoding="utf-8"))
    except OSError:
        pass

    ventana = VentanaLogin()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
