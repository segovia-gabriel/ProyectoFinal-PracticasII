"""
Formulario modal de la cuenta de una mesa (consumo). Elegis la reserva y el medio
de pago, agregas items con cantidad, y el precio de cada uno se resuelve segun el
medio (el especial si coincide, si no el de lista). El total se recalcula solo,
tambien al cambiar el medio de pago. Mientras la mesa esta abierta guardas con
"Guardar (mesa abierta)"; "Cerrar mesa" cierra la cuenta y la manda al historial
de ventas. El calculo final lo confirma el controlador.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QCompleter, QDialog, QHeaderView,
                             QInputDialog, QMessageBox, QTableWidgetItem)

from utilidades import formato
from utilidades.dialogos import confirmar

RUTA_UI = Path(__file__).resolve().parent / "consumo_form.ui"


class DialogoConsumo(QDialog):
    def __init__(self, controlador, reserva_id=None, parent=None):
        # reserva_id llega cuando se abre para una mesa/reserva puntual (desde el
        # salon, los pendientes del panel o al editar una mesa abierta): ahi el
        # combo arranca con esa reserva ya elegida y, si la mesa ya tenia un
        # consumo abierto, precargo sus items para poder editarlos.
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.mensaje_exito = ""
        # cada item agregado: {"item_id", "nombre", "cantidad"}
        self.items_agregados = []

        self.tableWidget_items.verticalHeader().setVisible(False)
        # Columnas prolijas: "Item" ocupa el espacio libre y las numericas se
        # ajustan a su contenido, en vez de estirar solo la ultima (que dejaba
        # "Subtotal" gigante y las demas apretadas).
        cabecera = self.tableWidget_items.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.Stretch)
        for columna in (1, 2, 3):
            cabecera.setSectionResizeMode(columna, QHeaderView.ResizeToContents)
        self.tableWidget_items.setToolTip(
            "Doble clic en un item para corregir la cantidad.")

        # "Cerrar mesa" va en verde (cierra la venta); el azul primario de la
        # pantalla queda para "Guardar (mesa abierta)".
        self.pushButton_cerrar.setProperty("class", "exito")

        if reserva_id is not None:
            # Reserva fija: el combo se carga SOLO con esa reserva y lo bloqueo,
            # asi no le cargo el consumo a otra por error.
            exito, texto = self.controlador.texto_reserva(reserva_id)
            if exito:
                self.comboBox_reserva.addItem(texto, reserva_id)
            self.comboBox_reserva.setEnabled(False)
        else:
            exito, reservas = self.controlador.listar_reservas_combo()
            if exito:
                for rid, texto in reservas:
                    self.comboBox_reserva.addItem(texto, rid)
        self.comboBox_medio.addItem("Transferencia", "transferencia")
        self.comboBox_medio.addItem("Efectivo", "efectivo")
        exito, items = self.controlador.listar_items_combo()
        if exito:
            for iid, nombre in items:
                self.comboBox_item.addItem(nombre, iid)
        # Buscador de item: con muchos items, scrollear el combo es un embole. Lo
        # hago editable con autocompletar que filtra por cualquier parte del texto,
        # asi tipeas el nombre y aparece. Mismo patron que el buscador de cliente
        # en el alta de reservas.
        self.comboBox_item.setEditable(True)
        self.comboBox_item.setInsertPolicy(QComboBox.NoInsert)
        completer = self.comboBox_item.completer()
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        # Si la mesa ya tiene un consumo, lo precargo para editarlo.
        if reserva_id is not None:
            self._precargar(reserva_id)

        self.pushButton_agregar.clicked.connect(self.agregar_item)
        self.pushButton_quitar.clicked.connect(self.quitar_item)
        # doble clic en una fila para corregir la cantidad ya cargada
        self.tableWidget_items.doubleClicked.connect(self.editar_cantidad)
        # al cambiar el medio de pago, cambian los precios especiales
        self.comboBox_medio.currentIndexChanged.connect(self._refrescar_tabla)
        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cerrar.clicked.connect(self.cerrar_mesa)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def _precargar(self, reserva_id):
        exito, datos = self.controlador.preparar_edicion(reserva_id)
        if not exito or datos is None:
            return  # mesa sin consumo todavia: es una carga nueva
        self.setWindowTitle("Cuenta de la mesa")
        self.label_titulo.setText("Cuenta de la mesa (abierta)")
        indice = self.comboBox_medio.findData(datos["medio_pago"])
        if indice >= 0:
            self.comboBox_medio.setCurrentIndex(indice)
        self.items_agregados = [dict(i) for i in datos["items"]]
        self._refrescar_tabla()
        # Si por lo que sea la cuenta ya estaba cerrada, no la dejo editar.
        if datos["estado"] == "cerrada":
            self.label_titulo.setText("Cuenta cerrada (solo lectura)")
            self.pushButton_guardar.setEnabled(False)
            self.pushButton_cerrar.setEnabled(False)
            self.pushButton_agregar.setEnabled(False)
            self.pushButton_quitar.setEnabled(False)

    def _medio(self):
        return self.comboBox_medio.currentData()

    def agregar_item(self):
        # Como el combo es editable (buscador), matcheo el texto tipeado contra la
        # lista: si no coincide con ningun item, aviso en vez de agregar cualquier cosa.
        indice = self.comboBox_item.findText(self.comboBox_item.currentText())
        if indice < 0:
            QMessageBox.warning(self, "Item invalido",
                                "Elegi un item valido de la lista.")
            return
        self.comboBox_item.setCurrentIndex(indice)
        item_id = self.comboBox_item.currentData()
        # el item tiene que tener precio cargado para poder consumirse
        if self.controlador.precio_item(item_id, self._medio()) is None:
            QMessageBox.warning(self, "Sin precio",
                                "Ese item no tiene un precio cargado. Cargale uno desde Menu → Precios.")
            return

        cantidad = self.spinBox_cantidad.value()
        # si el item ya estaba, le sumo la cantidad en vez de duplicar la fila
        for agregado in self.items_agregados:
            if agregado["item_id"] == item_id:
                agregado["cantidad"] += cantidad
                break
        else:
            self.items_agregados.append({
                "item_id": item_id,
                "nombre": self.comboBox_item.currentText(),
                "cantidad": cantidad,
            })
        self._refrescar_tabla()

    def quitar_item(self):
        fila = self.tableWidget_items.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atencion", "Selecciona un item de la lista para quitar.")
            return
        del self.items_agregados[fila]
        self._refrescar_tabla()

    def editar_cantidad(self):
        # Doble clic en una fila: corregis la cantidad de un item ya cargado sin
        # tener que sacarlo y volver a agregarlo. En una cuenta cerrada (solo
        # lectura) el boton Agregar esta apagado, asi que tampoco se edita.
        if not self.pushButton_agregar.isEnabled():
            return
        fila = self.tableWidget_items.currentRow()
        if fila < 0:
            return
        agregado = self.items_agregados[fila]
        nueva, ok = QInputDialog.getInt(
            self, "Editar cantidad", f"Cantidad de «{agregado['nombre']}»:",
            agregado["cantidad"], 1, 99)
        if ok:
            agregado["cantidad"] = nueva
            self._refrescar_tabla()

    def _refrescar_tabla(self):
        medio = self._medio()
        tabla = self.tableWidget_items
        tabla.setRowCount(0)
        total = 0.0
        for fila, agregado in enumerate(self.items_agregados):
            precio = self.controlador.precio_item(agregado["item_id"], medio)
            precio = float(precio) if precio is not None else 0.0
            subtotal = precio * agregado["cantidad"]
            total += subtotal
            tabla.insertRow(fila)
            tabla.setItem(fila, 0, QTableWidgetItem(agregado["nombre"]))
            item_cant = QTableWidgetItem(str(agregado["cantidad"]))
            item_cant.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(fila, 1, item_cant)
            # Los importes van alineados a la derecha, como corresponde a dinero.
            item_precio = QTableWidgetItem(formato.moneda(precio))
            item_precio.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tabla.setItem(fila, 2, item_precio)
            item_subtotal = QTableWidgetItem(formato.moneda(subtotal))
            item_subtotal.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tabla.setItem(fila, 3, item_subtotal)
        self.label_total.setText(f"Total: {formato.moneda(total)}")

    def _items(self):
        return [(a["item_id"], a["cantidad"]) for a in self.items_agregados]

    def guardar(self):
        # Guarda la cuenta dejando la mesa abierta (podes seguir editando).
        exito, mensaje = self.controlador.guardar_consumo(
            self.comboBox_reserva.currentData(), self._medio(), self._items(), cerrar=False
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)

    def cerrar_mesa(self):
        # Cierra la cuenta: pido confirmacion porque despues no se puede editar.
        if not confirmar(self, "¿Cerrar la mesa y consolidar la cuenta? Despues no se podra editar.",
                         titulo="Cerrar mesa", texto_si="Cerrar mesa"):
            return
        exito, mensaje = self.controlador.guardar_consumo(
            self.comboBox_reserva.currentData(), self._medio(), self._items(), cerrar=True
        )
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
