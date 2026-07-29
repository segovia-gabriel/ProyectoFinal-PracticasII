"""
Dialogo de confirmacion compartido por todos los modulos al eliminar un registro.
Se arma aca en un solo lugar para no repetir el mismo QMessageBox en cada ventana
y, sobre todo, para que los botones salgan en espanol ("Si"/"Cancelar") en vez de
los "Yes"/"No" que Qt pone por defecto segun el idioma del sistema.
"""

from PyQt5.QtWidgets import QMessageBox


def confirmar(parent, mensaje, titulo="Confirmar", texto_si="Si"):
    # Confirmacion generica con botones en espanol. Devuelve True solo si el
    # usuario apreta el boton afirmativo. Se arma el QMessageBox a mano (en vez de
    # QMessageBox.question) porque Qt no traduce "Yes"/"No" solo.
    caja = QMessageBox(parent)
    caja.setIcon(QMessageBox.Question)
    caja.setWindowTitle(titulo)
    caja.setText(mensaje)
    boton_si = caja.addButton(texto_si, QMessageBox.YesRole)
    boton_cancelar = caja.addButton("Cancelar", QMessageBox.NoRole)
    # "Cancelar" queda por defecto: si la accion es delicada, Enter no la dispara.
    caja.setDefaultButton(boton_cancelar)
    caja.exec_()
    return caja.clickedButton() is boton_si


def confirmar_eliminacion(parent, mensaje, titulo="Confirmar eliminacion"):
    # Caso particular para las bajas de registros, con el mismo estilo.
    return confirmar(parent, mensaje, titulo)
