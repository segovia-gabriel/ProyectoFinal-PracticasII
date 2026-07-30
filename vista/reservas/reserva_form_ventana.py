"""
Formulario modal de alta/edicion de reserva. La hora de fin y el precio salen
solos a partir de la mesa, la hora de inicio y la duracion (2h = 100%, 3h = 125%
del valor del grupo). El precio se guarda como una foto al crear.
"""

from datetime import date
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate, Qt, QTime
from PyQt5.QtWidgets import QComboBox, QCompleter, QDialog

from utilidades import formato

RUTA_UI = Path(__file__).resolve().parent / "reserva_form.ui"


class DialogoReserva(QDialog):
    def __init__(self, controlador, reserva=None, parent=None,
                 mesa_id=None, hora_inicio=None):
        # mesa_id/hora_inicio: precarga opcional cuando el alta viene del Salon (la
        # mesa que elegiste en el plano y el horario que estas viendo). Al editar los ignoro.
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.reserva_id = reserva["id"] if reserva else None
        self.mensaje_exito = ""

        # Aviso de turnos con el estilo de ayuda del sistema.
        self.label_ayuda_horario.setProperty("class", "ayuda")

        # Combos
        exito, clientes = self.controlador.listar_clientes_combo()
        if exito:
            for cid, texto in clientes:
                self.comboBox_cliente.addItem(texto, cid)
        # Buscador de cliente: hago el combo editable con autocompletar que filtra
        # por cualquier parte del texto, asi podes tipear el nombre o el DNI (el
        # DNI va metido en el texto de cada opcion).
        self.comboBox_cliente.setEditable(True)
        self.comboBox_cliente.setInsertPolicy(QComboBox.NoInsert)
        completer = self.comboBox_cliente.completer()
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        exito, mesas = self.controlador.listar_mesas_combo()
        if exito:
            for mid, texto in mesas:
                self.comboBox_mesa.addItem(texto, mid)
        for texto, valor in formato.DURACIONES:
            self.comboBox_duracion.addItem(texto, valor)
        for texto, valor in formato.ESTADOS_ASISTENCIA:
            self.comboBox_estado.addItem(texto, valor)

        if reserva:
            self.setWindowTitle("Editar reserva")
            self.label_titulo.setText("Editar reserva")
            self._seleccionar(self.comboBox_cliente, reserva["cliente_id"])
            self._seleccionar(self.comboBox_mesa, reserva["mesa_id"])
            f = reserva["fecha"]
            self.dateEdit_fecha.setDate(QDate(f.year, f.month, f.day))
            hi = reserva["hora_inicio"]  # timedelta
            total = int(hi.total_seconds())
            self.timeEdit_inicio.setTime(QTime(total // 3600, (total % 3600) // 60))
            self._seleccionar(self.comboBox_duracion, reserva["duracion_tipo"])
            self._seleccionar(self.comboBox_estado, reserva["estado_asistencia"])
            # El estado solo lo podes tocar el mismo dia de la reserva.
            self.comboBox_estado.setEnabled(reserva["fecha"] == date.today())
        else:
            # Alta: la fecha arranca hoy y el estado queda fijo en "en espera".
            self.dateEdit_fecha.setDate(QDate.currentDate())
            self.comboBox_estado.setEnabled(False)
            # Precarga cuando el alta viene del Salon: te ahorra elegir la mesa y
            # la hora a mano. El resto (cliente, duracion) lo completas igual.
            if mesa_id is not None:
                self._seleccionar(self.comboBox_mesa, mesa_id)
            if hora_inicio is not None:
                self.timeEdit_inicio.setTime(hora_inicio)

        # Recalcular hora de fin y precio cuando cambia algo que los afecta.
        self.comboBox_mesa.currentIndexChanged.connect(self._recalcular)
        self.comboBox_duracion.currentIndexChanged.connect(self._recalcular)
        self.timeEdit_inicio.timeChanged.connect(self._recalcular)
        self._recalcular()

        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def _seleccionar(self, combo, valor):
        indice = combo.findData(valor)
        if indice >= 0:
            combo.setCurrentIndex(indice)

    def _recalcular(self):
        mesa_id = self.comboBox_mesa.currentData()
        duracion = self.comboBox_duracion.currentData()
        hora_inicio = self.timeEdit_inicio.time().toPyTime()
        # Hora de fin
        hora_fin = self.controlador._hora_fin(hora_inicio, duracion)
        self.lineEdit_horaFin.setText(hora_fin.strftime("%H:%M"))
        # Precio (puede ser None si todavia no hay mesas cargadas)
        if mesa_id is not None:
            precio = self.controlador.calcular_precio(mesa_id, duracion)
            self.lineEdit_precio.setText(formato.moneda(precio))
        else:
            self.lineEdit_precio.setText("—")

    def guardar(self):
        # Como el combo de cliente es editable, matcheo el texto tipeado contra la
        # lista: si no coincide con ningun cliente, aviso.
        indice_cliente = self.comboBox_cliente.findText(self.comboBox_cliente.currentText())
        if indice_cliente < 0:
            self.label_error.setText("Elegi un cliente valido de la lista (por nombre o DNI).")
            return
        self.comboBox_cliente.setCurrentIndex(indice_cliente)

        exito, mensaje = self.controlador.guardar(
            self.reserva_id,
            self.comboBox_cliente.currentData(),
            self.comboBox_mesa.currentData(),
            self.dateEdit_fecha.date().toPyDate(),
            self.timeEdit_inicio.time().toPyTime(),
            self.comboBox_duracion.currentData(),
            self.comboBox_estado.currentData(),
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
