"""
Dialogo de confirmacion que usan todos los modulos cuando hay que borrar algo.
Armo el QMessageBox a mano (y no QMessageBox.question) porque Qt no traduce los
"Yes"/"No" y los quiero en espanol.
"""

from PyQt5.QtWidgets import QMessageBox


def confirmar(parent, mensaje, titulo="Confirmar", texto_si="Si"):
    # Devuelve True solo si el usuario le da al boton de confirmar.
    caja = QMessageBox(parent)
    caja.setIcon(QMessageBox.Question)
    caja.setWindowTitle(titulo)
    caja.setText(mensaje)
    boton_si = caja.addButton(texto_si, QMessageBox.YesRole)
    boton_cancelar = caja.addButton("Cancelar", QMessageBox.NoRole)
    # Dejo "Cancelar" por defecto: si la accion es delicada, que Enter no la dispare de una.
    caja.setDefaultButton(boton_cancelar)
    caja.exec_()
    return caja.clickedButton() is boton_si


def confirmar_eliminacion(parent, mensaje, titulo="Confirmar eliminacion"):
    # El caso puntual de las bajas de registros, con el mismo estilo.
    return confirmar(parent, mensaje, titulo)
