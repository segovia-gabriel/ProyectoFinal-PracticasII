"""
Plano del salon: dibuja las mesas de cada piso como botones y las pinta segun lo
que pasa en el horario elegido (libre, reservada, ocupada, con consumo cerrado).
Desde aca se marca la asistencia y se carga el consumo de la reserva que ocupa
la mesa, reutilizando los mismos dialogos de Reservas y Consumo. No crea
consumos sueltos: el consumo siempre cuelga de una reserva, como en el modelo.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QTime, Qt
from PyQt5.QtWidgets import (QDialog, QGridLayout, QMainWindow, QMessageBox,
                             QPushButton, QWidget)

from controlador.consumo_controlador import ConsumoControlador
from controlador.reservas_controlador import ReservasControlador
from controlador.salon_controlador import (CERRADA, ETIQUETAS, OCUPADA,
                                           SalonControlador)
from utilidades import formato
from vista.consumo.consumo_detalle_ventana import DialogoDetalleConsumo
from vista.consumo.consumo_form_ventana import DialogoConsumo
from vista.reservas.estado_form_ventana import DialogoEstado

RUTA_UI = Path(__file__).resolve().parent / "salon.ui"

# Cuantas mesas por fila en la grilla de cada piso.
COLUMNAS = 4


class VentanaSalon(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = SalonControlador()
        self.reservas_controlador = ReservasControlador()
        self.consumo_controlador = ConsumoControlador()
        self.mesa_seleccionada = None

        self.label_fecha.setText(self._texto_fecha())
        self.label_referencias.setProperty("class", "ayuda")
        self.label_referencias.setText(
            "Blanco: libre   ·   Azul: reservada   ·   Verde: mesa abierta   ·   "
            "Gris: cuenta cerrada   ·   Rojo: no se presentó")

        self.timeEdit_hora.setTime(QTime.currentTime())
        self._cargar_horarios_sugeridos()

        self.timeEdit_hora.timeChanged.connect(self.cargar_salon)
        self.pushButton_ahora.clicked.connect(self.ir_a_ahora)
        self.comboBox_sugeridos.activated.connect(self.ir_a_sugerido)
        self.pushButton_asistencia.clicked.connect(self.marcar_asistencia)
        self.pushButton_consumo.clicked.connect(self.cargar_consumo)
        self.pushButton_verConsumo.clicked.connect(self.ver_consumo)
        self.pushButton_volver.clicked.connect(self.close)

        self.cargar_salon()

    def _texto_fecha(self):
        from datetime import date

        hoy = date.today()
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return (f"{dias[hoy.weekday()]} {hoy.day} de "
                f"{formato.nombre_mes(hoy.month).lower()}")

    def _cargar_horarios_sugeridos(self):
        # Accesos rapidos a las horas en las que hoy hay reservas: si se defiende
        # a la manana, el plano estaria vacio y no se veria nada.
        self.comboBox_sugeridos.addItem("—", None)
        exito, horarios = self.controlador.horarios_sugeridos()
        if not exito:
            return
        for valor in horarios:
            texto = formato.hora(valor)
            self.comboBox_sugeridos.addItem(texto, texto)

    # ---------- Dibujo del plano ----------

    def cargar_salon(self):
        hora = self.timeEdit_hora.time().toString("HH:mm:ss")
        exito, pisos = self.controlador.estado_del_salon(hora)
        if not exito:
            QMessageBox.warning(self, "Error", pisos)
            return

        self.label_resumen.setText(self.controlador.resumen(pisos))

        # Se redibuja todo: son pocas mesas y evita tener que sincronizar
        # el estado de cada boton por separado.
        recordada = self.mesa_seleccionada["id"] if self.mesa_seleccionada else None
        pestana_actual = self.tabWidget_pisos.currentIndex()
        self.tabWidget_pisos.clear()
        self.mesa_seleccionada = None

        for piso in sorted(pisos):
            self.tabWidget_pisos.addTab(self._armar_piso(pisos[piso], recordada),
                                        self.controlador.nombre_piso(piso))
        if 0 <= pestana_actual < self.tabWidget_pisos.count():
            self.tabWidget_pisos.setCurrentIndex(pestana_actual)

        if self.mesa_seleccionada is None:
            self._mostrar_detalle(None)

    def _armar_piso(self, mesas, id_recordado):
        contenedor = QWidget()
        grilla = QGridLayout(contenedor)
        grilla.setSpacing(12)
        for indice, mesa in enumerate(mesas):
            boton = self._armar_boton(mesa)
            grilla.addWidget(boton, indice // COLUMNAS, indice % COLUMNAS)
            if mesa["id"] == id_recordado:
                self._seleccionar(mesa)
        # una fila elastica al final para que las mesas queden arriba
        grilla.setRowStretch(grilla.rowCount(), 1)
        return contenedor

    def _armar_boton(self, mesa):
        # El texto del boton es lo que se lee de un vistazo: codigo, sillas y,
        # si esta ocupada, el apellido del cliente.
        lineas = [mesa["codigo"], f"{mesa['sillas']} sillas"]
        if mesa["cliente"]:
            lineas.append(mesa["cliente"].split(",")[0])
            lineas.append(mesa["horario"])
        else:
            lineas.append(mesa["grupo"])

        boton = QPushButton("\n".join(lineas))
        boton.setMinimumSize(140, 96)
        boton.setCheckable(True)
        # la property dinamica 'estado' es la que usa style.css para el color
        boton.setProperty("estado", mesa["estado"])
        boton.setProperty("class", "mesa")
        boton.setToolTip(f"{mesa['codigo']} — {ETIQUETAS[mesa['estado']]}\n{mesa['detalle']}")
        boton.clicked.connect(lambda _, m=mesa: self._seleccionar(m))
        return boton

    def _seleccionar(self, mesa):
        self.mesa_seleccionada = mesa
        self._mostrar_detalle(mesa)

    def _mostrar_detalle(self, mesa):
        if mesa is None:
            self.label_mesaCodigo.setText("—")
            self.label_mesaDatos.setText("Seleccioná una mesa del plano.")
            self.label_mesaEstado.setText("")
            self.pushButton_asistencia.setEnabled(False)
            self.pushButton_consumo.setEnabled(False)
            self.pushButton_verConsumo.setEnabled(False)
            return

        self.label_mesaCodigo.setText(mesa["codigo"])
        # Lineas cortas: el panel es angosto y los textos largos se cortaban.
        datos = [f"{mesa['sillas']} sillas · grupo {mesa['grupo']}",
                 f"Valor 2 h: {formato.moneda(mesa['grupo_valor'])}"]
        if mesa["cliente"]:
            datos.append("")
            datos.append(mesa["cliente"])
            datos.append(mesa["horario"])
        self.label_mesaDatos.setText("\n".join(datos))

        self.label_mesaEstado.setText(f"{ETIQUETAS[mesa['estado']]}. {mesa['detalle']}")
        self.label_mesaEstado.setProperty(
            "class", "aviso" if mesa["estado"] == OCUPADA else "ayuda")
        self.label_mesaEstado.style().unpolish(self.label_mesaEstado)
        self.label_mesaEstado.style().polish(self.label_mesaEstado)

        hay_reserva = mesa["reserva_id"] is not None
        self.pushButton_asistencia.setEnabled(hay_reserva and mesa["consumo_id"] is None)
        self.pushButton_consumo.setEnabled(mesa["estado"] == OCUPADA)
        self.pushButton_verConsumo.setEnabled(mesa["estado"] == CERRADA)

    # ---------- Acciones sobre la reserva de la mesa ----------

    def _mesa_con_reserva(self):
        mesa = self.mesa_seleccionada
        if mesa is None or mesa["reserva_id"] is None:
            QMessageBox.warning(self, "Atención",
                                "Elegí una mesa que tenga una reserva en este horario.")
            return None
        return mesa

    def marcar_asistencia(self):
        mesa = self._mesa_con_reserva()
        if mesa is None:
            return
        dialogo = DialogoEstado(mesa["estado_reserva"], parent=self)
        if dialogo.exec_() != QDialog.Accepted:
            return
        exito, mensaje = self.reservas_controlador.cambiar_estado(
            mesa["reserva_id"], dialogo.estado_elegido())
        if exito:
            self.cargar_salon()
        else:
            QMessageBox.warning(self, "Error", mensaje)

    def cargar_consumo(self):
        mesa = self._mesa_con_reserva()
        if mesa is None:
            return
        dialogo = DialogoConsumo(self.consumo_controlador,
                                 reserva_id=mesa["reserva_id"], parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)
            self.cargar_salon()

    def ver_consumo(self):
        mesa = self.mesa_seleccionada
        if mesa is None or mesa["consumo_id"] is None:
            return
        exito, detalle = self.consumo_controlador.obtener_detalle(mesa["consumo_id"])
        if not exito:
            QMessageBox.warning(self, "Error", detalle)
            return
        DialogoDetalleConsumo(detalle, parent=self).exec_()

    # ---------- Navegacion ----------

    def ir_a_ahora(self):
        self.timeEdit_hora.setTime(QTime.currentTime())

    def ir_a_sugerido(self):
        texto = self.comboBox_sugeridos.currentData()
        if texto:
            self.timeEdit_hora.setTime(QTime.fromString(texto, "HH:mm"))

    def closeEvent(self, evento):
        if self.parent() is not None:
            self.parent().show()
        evento.accept()
