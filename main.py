"""
Arranque de la aplicacion. Crea la QApplication, aplica la hoja de estilos
global una sola vez (como mostro el profesor) y muestra el login.
"""

import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from vista.login_ventana import VentanaLogin

# Ruta al QSS global, calculada desde main.py (regla dura: pathlib).
RUTA_ESTILO = Path(__file__).resolve().parent / "recursos" / "style.css"


def main():
    app = QApplication(sys.argv)

    # Un solo setStyleSheet para toda la app: garantiza que las 8 pantallas se
    # vean iguales sin repetir estilos en cada ventana. Si falla, seguimos igual
    # con el estilo por defecto de Qt en vez de cortar el arranque.
    try:
        app.setStyleSheet(RUTA_ESTILO.read_text(encoding="utf-8"))
    except OSError:
        pass

    ventana = VentanaLogin()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
