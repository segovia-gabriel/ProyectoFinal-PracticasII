# Módulo Precios, Notificaciones y Cierre de mesas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplificar la carga de precios (un solo precio, especial automático), permitir editar el precio vigente, arreglar el bug de notificaciones, renombrar "Pendientes" → "Notificaciones", sacar el botón "Actualizar" y agregar cierre de mesas (automático al iniciar sesión + botón "Cerrar día").

**Architecture:** MVC directo (modelo = SQL, controlador = validación/orquestación, vista = PyQt5 + `.ui`). Cada cambio respeta las capas: la vista nunca llama al modelo, el modelo nunca arma widgets.

**Tech Stack:** Python 3.12 (Mac) / 3.8 (Win), PyQt5, `mysql-connector-python`, MySQL 8 / MariaDB.

## Global Constraints

- Nombres, comentarios y textos de UI en **español** (rioplatense simple).
- Rutas siempre con `pathlib`, nunca `/` o `\` a mano (multiplataforma real).
- `try/except` alrededor de toda consulta SQL; el error se muestra con `QMessageBox`, nunca solo en consola.
- Sin sobre-diseño (nada de Repository/Factory/event-bus): nivel de dos alumnos de Prácticas II.
- Los `.ui` deben quedar como XML válido de Qt Designer (`<ui version="4.0">`), abribles sin advertencias.
- Constante del descuento en efectivo: `DESCUENTO_EFECTIVO = 0.10`.
- Umbral de aviso de renovación: 10 días (constante ya existente `DIAS_AVISO_RENOVACION`).

## Nota sobre verificación

El proyecto **no tiene suite de tests automatizada** y se entrega como app de escritorio para defensa oral. La verificación de cada task es **manual**: consultas SQL en MySQL Workbench para los cambios de modelo, y revisión visual de Gabriel para la UI (él verifica cada cambio de pantalla; no se corre la app desde acá). Esto es coherente con la práctica del proyecto y con las reglas de la cátedra. No se agrega pytest ni una base de test: sería sobre-diseño para el nivel del trabajo.

## Estructura de archivos

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `analisis/schema.sql` | DER + datos de prueba | Modificar (columna `consumo_vencido`) |
| `modelo/precio_menu_modelo.py` | SQL de historial de precios | Modificar (fix + `actualizar_vigente`) |
| `modelo/consumo_modelo.py` | SQL de consumos | Modificar (cierre de abiertas, filtro) |
| `modelo/reserva_modelo.py` | SQL de reservas | Modificar (`vencer_consumos_pendientes`) |
| `modelo/panel_modelo.py` | Consultas del panel | Modificar (filtro `consumo_vencido`) |
| `controlador/menu_controlador.py` | Lógica de menú/precios | Modificar (precio especial auto, editar vigente) |
| `controlador/cierre_controlador.py` | Cierre de mesas | **Crear** |
| `vista/menu/precio_form.ui` | Form de precio | Modificar (quitar campos especial) |
| `vista/menu/precio_form_ventana.py` | Ventana del form | Modificar (especial auto, modo edición) |
| `vista/menu/precios.ui` | Ventana historial | Modificar (botón Editar vigente) |
| `vista/menu/precios_ventana.py` | Lógica de la ventana | Modificar (abrir editar) |
| `vista/principal.ui` | Panel de Inicio | Modificar (Notificaciones, Cerrar día) |
| `vista/principal_ventana.py` | Lógica del panel | Modificar (barrido, cerrar día, textos) |

---

### Task 1: Esquema — columna `consumo_vencido` en reservas

**Files:**
- Modify: `analisis/schema.sql:118-130` (tabla `reservas`)

**Interfaces:**
- Produces: columna `reservas.consumo_vencido TINYINT(1) NOT NULL DEFAULT 0`.

- [ ] **Step 1: Agregar la columna a la tabla reservas**

En la definición de `CREATE TABLE reservas`, después de la línea de `estado_asistencia`, agregar:

```sql
    estado_asistencia      ENUM('en_espera','asistio','tardanza','falto') NOT NULL DEFAULT 'en_espera',
    consumo_vencido        TINYINT(1) NOT NULL DEFAULT 0,   -- 1 = asistió pero el consumo no se cargó y el día ya cerró
```

- [ ] **Step 2: Recrear la base**

Como los datos son de prueba y `schema.sql` recrea todo, correr el script completo en MySQL Workbench (o `mysql < analisis/schema.sql`).

- [ ] **Step 3: Verificar la columna**

Correr en Workbench:
```sql
DESCRIBE reservas;
```
Esperado: aparece la fila `consumo_vencido | tinyint(1) | NO | | 0 |`.

---

### Task 2: Modelo de precios — fix del bug + editar vigente

**Files:**
- Modify: `modelo/precio_menu_modelo.py:76-104` (`crear_precio`), agregar `actualizar_vigente`

**Interfaces:**
- Consumes: `obtener_vigente(item_id)` (ya existe, devuelve dict con `id`, `precio_lista`, `precio_especial`, `medio_pago_especial`, `fecha_inicio`, `fecha_fin`).
- Produces: `crear_precio(...)` corregido; `actualizar_vigente(precio_id, precio_lista, precio_especial, medio_pago_especial, fecha_fin)`.

- [ ] **Step 1: Corregir el UPDATE de `crear_precio`**

Reemplazar el bloque del `UPDATE` (líneas ~85-91) por:

```python
        # cerrar el precio activo real al dia anterior al nuevo. Ojo: no alcanza
        # con cerrar el de fecha_fin NULL; un precio por vencer TIENE fecha_fin
        # puesta, y si no se cerraba quedaba pisado con el nuevo y seguia
        # apareciendo en las notificaciones. Por eso se cierra tambien el que
        # tenga fecha_fin todavia vigente al momento de arrancar el nuevo.
        fecha_cierre = fecha_inicio - timedelta(days=1)
        cursor.execute(
            "UPDATE historial_precios_menu SET fecha_fin = %s "
            "WHERE menu_item_id = %s AND (fecha_fin IS NULL OR fecha_fin >= %s)",
            (fecha_cierre, item_id, fecha_inicio),
        )
```

- [ ] **Step 2: Agregar `actualizar_vigente` al final del archivo**

```python
def actualizar_vigente(precio_id, precio_lista, precio_especial, medio_pago_especial, fecha_fin):
    # Corrige el precio vigente (la fila que arranco y no cerro) cuando se cargo
    # mal. No inserta una fila nueva: edita la existente, asi no ensucia el
    # historial ni la variacion con un cambio que en realidad fue un tipeo.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE historial_precios_menu "
            "SET precio_lista = %s, precio_especial = %s, medio_pago_especial = %s, fecha_fin = %s "
            "WHERE id = %s",
            (precio_lista, precio_especial, medio_pago_especial, fecha_fin, precio_id),
        )
        conexion.commit()
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
```

- [ ] **Step 3: Verificar el fix del bug (SQL)**

En Workbench, elegir un ítem con un precio por vencer (fecha_fin dentro de 10 días). Simular renovación:
```sql
-- ver estado antes: deberia haber 1 fila activa con fecha_fin proxima
SELECT id, precio_lista, fecha_inicio, fecha_fin FROM historial_precios_menu
WHERE menu_item_id = <ID> AND (fecha_fin IS NULL OR fecha_fin >= CURDATE());
```
Después de guardar un precio nuevo desde la app (Task 4/5), volver a correr la query: esperado **una sola** fila activa (la nueva), la vieja con `fecha_fin = ayer`.

---

### Task 3: Controlador de menú — precio especial automático + editar vigente

**Files:**
- Modify: `controlador/menu_controlador.py:20` (constante), `:194-222` (`guardar_precio`), agregar `_precio_efectivo`, `editar_precio_vigente`, `precio_vigente`

**Interfaces:**
- Consumes: `precio_menu_modelo.crear_precio`, `precio_menu_modelo.actualizar_vigente`, `precio_menu_modelo.obtener_vigente`.
- Produces:
  - `guardar_precio(item_id, precio_lista, fecha_fin=None) -> (bool, str)`
  - `editar_precio_vigente(item_id, precio_lista, fecha_fin=None) -> (bool, str)`
  - `precio_vigente(item_id) -> (bool, dict|None|str)`

- [ ] **Step 1: Agregar la constante del descuento**

Debajo de `DIAS_AVISO_RENOVACION = 10` (línea 20):

```python
DIAS_AVISO_RENOVACION = 10
# El precio de lista es el de transferencia; en efectivo se aplica este descuento.
# Un solo lugar por si algun dia cambia el porcentaje.
DESCUENTO_EFECTIVO = 0.10
```

- [ ] **Step 2: Reemplazar `guardar_precio` por la versión simplificada**

```python
    def _precio_efectivo(self, precio_lista):
        # El especial se calcula solo: lista (transferencia) menos el descuento.
        return round(precio_lista * (1 - DESCUENTO_EFECTIVO), 2)

    def guardar_precio(self, item_id, precio_lista, fecha_fin=None):
        if precio_lista <= 0:
            return False, "El precio de lista debe ser mayor a cero."
        hoy = date.today()
        if fecha_fin is not None and fecha_fin < hoy:
            return False, "La fecha de fin de vigencia no puede ser anterior a hoy."

        # Se guarda el especial ya calculado (efectivo) para que el historial
        # quede con el numero real y no dependa del porcentaje a futuro.
        precio_especial = self._precio_efectivo(precio_lista)
        try:
            precio_menu_modelo.crear_precio(
                item_id, precio_lista, precio_especial, "efectivo", hoy, fecha_fin
            )
            item = menu_modelo.obtener_por_id(item_id)
            nombre = item["nombre"] if item else f"#{item_id}"
            registrar_accion(Sesion().usuario_id, f"Actualizó precio de ítem de menú: {nombre}")
            return True, "Precio actualizado correctamente."
        except Error:
            return False, "No se pudo guardar el precio."

    def editar_precio_vigente(self, item_id, precio_lista, fecha_fin=None):
        # Corrige el precio vigente sin crear una fila nueva (para el caso de
        # haber cargado mal un precio). Recalcula el especial y la variacion sola.
        if precio_lista <= 0:
            return False, "El precio de lista debe ser mayor a cero."
        hoy = date.today()
        if fecha_fin is not None and fecha_fin < hoy:
            return False, "La fecha de fin de vigencia no puede ser anterior a hoy."
        try:
            vigente = precio_menu_modelo.obtener_vigente(item_id)
        except Error:
            return False, "No se pudo obtener el precio vigente."
        if vigente is None:
            return False, "El ítem no tiene un precio vigente para editar."

        precio_especial = self._precio_efectivo(precio_lista)
        try:
            precio_menu_modelo.actualizar_vigente(
                vigente["id"], precio_lista, precio_especial, "efectivo", fecha_fin
            )
            item = menu_modelo.obtener_por_id(item_id)
            nombre = item["nombre"] if item else f"#{item_id}"
            registrar_accion(Sesion().usuario_id, f"Editó precio vigente de ítem de menú: {nombre}")
            return True, "Precio vigente actualizado correctamente."
        except Error:
            return False, "No se pudo editar el precio vigente."

    def precio_vigente(self, item_id):
        # Lo usa la ventana de precios para precargar el form al editar.
        try:
            return True, precio_menu_modelo.obtener_vigente(item_id)
        except Error:
            return False, "No se pudo obtener el precio vigente."
```

- [ ] **Step 3: Verificar el cálculo del especial (SQL/manual)**

Tras cargar un precio de lista de `$1000` desde la app (Task 5), correr:
```sql
SELECT precio_lista, precio_especial, medio_pago_especial
FROM historial_precios_menu WHERE menu_item_id = <ID> AND fecha_fin IS NULL;
```
Esperado: `precio_lista = 1000.00`, `precio_especial = 900.00`, `medio_pago_especial = efectivo`.

---

### Task 4: Form de precio — quitar campos del especial + modo edición

**Files:**
- Modify: `vista/menu/precio_form.ui` (quitar filas del especial, agregar nota), `vista/menu/precio_form_ventana.py` (reescribir)

**Interfaces:**
- Consumes: `controlador.guardar_precio`, `controlador.editar_precio_vigente`.
- Produces: `DialogoPrecio(controlador, item_id, precio_actual=None, parent=None)` con atributo `mensaje_exito`.

- [ ] **Step 1: Editar `precio_form.ui` — quitar filas 1, 2 y 3**

Borrar del `QFormLayout name="layout_campos"` los tres items del especial: `checkBox_especial` (row 1), `label_especial` + `doubleSpinBox_especial` (row 2) y `label_medio` + `comboBox_medio` (row 3). Renumerar los `row=` restantes: `label_lista`/`doubleSpinBox_lista` quedan en row 0; `label_tieneFin`/`checkBox_fechaFin` pasan a row 2; `label_fin`/`dateEdit_fin` a row 3. En row 1 agregar una nota:

```xml
     <item row="1" column="1">
      <widget class="QLabel" name="label_notaEfectivo">
       <property name="text">
        <string>El precio en efectivo se calcula solo (10% menos).</string>
       </property>
      </widget>
     </item>
```

- [ ] **Step 2: Reescribir `precio_form_ventana.py`**

```python
"""
Formulario modal para cargar o editar el precio de un item. Se carga solo el
precio de lista; el precio en efectivo (10% menos) lo calcula el controlador. Si
se abre con un precio_actual, funciona en modo edicion del precio vigente.
"""

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDialog

RUTA_UI = Path(__file__).resolve().parent / "precio_form.ui"


class DialogoPrecio(QDialog):
    def __init__(self, controlador, item_id, precio_actual=None, parent=None):
        super().__init__(parent)
        uic.loadUi(RUTA_UI, self)

        self.controlador = controlador
        self.item_id = item_id
        # precio_actual: dict del precio vigente si es edicion; None si es nuevo.
        self.precio_actual = precio_actual
        self.mensaje_exito = ""

        # Fecha de fin opcional. El precio arranca hoy, asi que el fin no puede
        # ser anterior; por defecto se sugiere dentro de un mes.
        self.dateEdit_fin.setMinimumDate(QDate.currentDate())
        self.dateEdit_fin.setDate(QDate.currentDate().addDays(30))
        self.checkBox_fechaFin.toggled.connect(self.dateEdit_fin.setEnabled)

        if precio_actual is not None:
            self._precargar(precio_actual)

        self.pushButton_guardar.clicked.connect(self.guardar)
        self.pushButton_cancelar.clicked.connect(self.reject)

    def _precargar(self, precio):
        self.setWindowTitle("Editar precio vigente")
        self.label_titulo.setText("Editar precio vigente")
        self.doubleSpinBox_lista.setValue(float(precio["precio_lista"]))
        if precio["fecha_fin"] is not None:
            self.checkBox_fechaFin.setChecked(True)
            self.dateEdit_fin.setEnabled(True)
            fin = precio["fecha_fin"]
            self.dateEdit_fin.setDate(QDate(fin.year, fin.month, fin.day))

    def guardar(self):
        precio_lista = self.doubleSpinBox_lista.value()
        # Si no se tilda "tiene fecha de fin", se manda None = vigente indefinido.
        fecha_fin = self.dateEdit_fin.date().toPyDate() if self.checkBox_fechaFin.isChecked() else None
        if self.precio_actual is None:
            exito, mensaje = self.controlador.guardar_precio(self.item_id, precio_lista, fecha_fin)
        else:
            exito, mensaje = self.controlador.editar_precio_vigente(self.item_id, precio_lista, fecha_fin)
        if exito:
            self.mensaje_exito = mensaje
            self.accept()
        else:
            self.label_error.setText(mensaje)
```

- [ ] **Step 3: Verificación visual (Gabriel)**

Abrir `precio_form.ui` en Qt Designer: no debe tirar advertencias, se ven solo Precio de lista, la nota del efectivo y la fecha de fin. La app abre "Nuevo precio" sin los campos del especial.

---

### Task 5: Ventana de precios — botón "Editar vigente"

**Files:**
- Modify: `vista/menu/precios.ui` (agregar `pushButton_editar`), `vista/menu/precios_ventana.py` (método `abrir_editar`)

**Interfaces:**
- Consumes: `controlador.precio_vigente`, `DialogoPrecio(controlador, item_id, precio_actual=..., parent=...)`.

- [ ] **Step 1: Agregar el botón al `.ui`**

En `layout_botones` de `precios.ui`, después del item de `pushButton_nuevo` (línea ~103) y antes del `spacer`, agregar:

```xml
      <item>
       <widget class="QPushButton" name="pushButton_editar">
        <property name="text">
         <string>Editar vigente</string>
        </property>
       </widget>
      </item>
```

- [ ] **Step 2: Conectar y agregar `abrir_editar` en `precios_ventana.py`**

En `__init__`, después de `self.pushButton_nuevo.clicked.connect(self.abrir_nuevo)` (línea 34):

```python
        self.pushButton_editar.clicked.connect(self.abrir_editar)
```

Agregar el método (junto a `abrir_nuevo`):

```python
    def abrir_editar(self):
        # Edita el precio vigente (para corregir uno cargado mal). Precarga el
        # form con el precio actual del item.
        exito, vigente = self.controlador.precio_vigente(self.item_id)
        if not exito:
            QMessageBox.warning(self, "Error", vigente)
            return
        if vigente is None:
            QMessageBox.information(self, "Sin precio",
                                    "Este ítem todavía no tiene un precio cargado.")
            return
        dialogo = DialogoPrecio(self.controlador, self.item_id, precio_actual=vigente, parent=self)
        if dialogo.exec_() == QDialog.Accepted:
            self.cargar_precios()
            QMessageBox.information(self, "Listo", dialogo.mensaje_exito)
```

- [ ] **Step 3: Verificación visual (Gabriel)**

En Precios: "Editar vigente" abre el form precargado con el precio actual; al guardar, la tabla se actualiza sola (la fila vigente cambia, no se agrega otra) y la variación se recalcula. La columna "Medio de pago" muestra "Efectivo" en las filas con especial.

---

### Task 6: Modelo — cierre de mesas y filtro de vencidas

**Files:**
- Modify: `modelo/consumo_modelo.py` (agregar dos funciones + filtro en `reservas_sin_consumo`), `modelo/reserva_modelo.py` (agregar `vencer_consumos_pendientes`), `modelo/panel_modelo.py:143-153` (filtro)

**Interfaces:**
- Produces:
  - `consumo_modelo.cerrar_abiertas_con_items(fecha_limite) -> int`
  - `consumo_modelo.eliminar_abiertas_vacias(fecha_limite) -> int`
  - `reserva_modelo.vencer_consumos_pendientes(fecha_limite) -> int`

- [ ] **Step 1: Agregar funciones de cierre a `consumo_modelo.py`**

Al final del archivo:

```python
def cerrar_abiertas_con_items(fecha_limite):
    # Cierra las mesas todavia abiertas que tienen consumo cargado (total > 0)
    # hasta 'fecha_limite' inclusive: pasan a 'cerrada' y recien ahi cuentan como
    # venta. Devuelve cuantas cerro.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE consumos SET estado = 'cerrada' "
            "WHERE estado = 'abierta' AND precio_total > 0 AND DATE(fecha) <= %s",
            (fecha_limite,),
        )
        conexion.commit()
        return cursor.rowcount
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()


def eliminar_abiertas_vacias(fecha_limite):
    # Descarta las mesas abiertas sin consumo cargado (total 0): se abrieron por
    # error y no son una venta. Borra primero el detalle (por la clave foranea) y
    # despues el consumo. Devuelve cuantos consumos borro.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "DELETE cd FROM consumo_detalle cd "
            "JOIN consumos co ON co.id = cd.consumo_id "
            "WHERE co.estado = 'abierta' AND co.precio_total = 0 AND DATE(co.fecha) <= %s",
            (fecha_limite,),
        )
        cursor.execute(
            "DELETE FROM consumos "
            "WHERE estado = 'abierta' AND precio_total = 0 AND DATE(fecha) <= %s",
            (fecha_limite,),
        )
        conexion.commit()
        return cursor.rowcount
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
```

- [ ] **Step 2: Filtrar las vencidas en `reservas_sin_consumo`**

En `consumo_modelo.reservas_sin_consumo` (línea ~70), agregar la condición `r.consumo_vencido = 0`:

```python
            "WHERE co.id IS NULL "
            "AND r.fecha <= CURDATE() "
            "AND r.consumo_vencido = 0 "
            "AND r.estado_asistencia IN ('asistio', 'tardanza') "
            "ORDER BY r.fecha DESC"
```

- [ ] **Step 3: Agregar `vencer_consumos_pendientes` a `reserva_modelo.py`**

Al final del archivo (usa el mismo patrón de conexión que las otras funciones del módulo):

```python
def vencer_consumos_pendientes(fecha_limite):
    # Marca como vencidas las reservas donde el cliente asistio (o llego tarde)
    # pero nunca se cargo el consumo y la fecha ya paso. Al cerrar el dia dejan de
    # figurar como pendientes: esa venta ya no se va a cargar. Devuelve cuantas
    # marco.
    conexion = None
    try:
        conexion = abrir_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE reservas r "
            "LEFT JOIN consumos co ON co.reserva_id = r.id "
            "SET r.consumo_vencido = 1 "
            "WHERE co.id IS NULL AND r.consumo_vencido = 0 "
            "AND r.estado_asistencia IN ('asistio', 'tardanza') "
            "AND r.fecha <= %s",
            (fecha_limite,),
        )
        conexion.commit()
        return cursor.rowcount
    except Error as error:
        registrar(error, "error")
        raise
    finally:
        if conexion is not None and conexion.is_connected():
            conexion.close()
```

> Verificar que `reserva_modelo.py` importe `abrir_conexion`, `Error` y `registrar` (las otras funciones ya los usan; no agregar imports duplicados).

- [ ] **Step 4: Filtrar las vencidas en `panel_modelo.reservas_cumplidas_sin_consumo`**

En `panel_modelo.py` (línea ~150), agregar la misma condición:

```python
            "WHERE co.id IS NULL AND r.fecha <= CURDATE() "
            "AND r.consumo_vencido = 0 "
            "AND r.estado_asistencia IN ('asistio', 'tardanza') "
            "ORDER BY r.fecha DESC"
```

- [ ] **Step 5: Verificación (SQL)**

```sql
-- marcar como vencidas las de dias anteriores
SELECT id, fecha, estado_asistencia, consumo_vencido FROM reservas
WHERE estado_asistencia IN ('asistio','tardanza') AND fecha < CURDATE();
```
Tras el barrido (Task 8), las que no tenían consumo deben quedar con `consumo_vencido = 1` y no aparecer más en el panel.

---

### Task 7: Controlador de cierre — `cierre_controlador.py`

**Files:**
- Create: `controlador/cierre_controlador.py`

**Interfaces:**
- Consumes: `consumo_modelo.cerrar_abiertas_con_items`, `consumo_modelo.eliminar_abiertas_vacias`, `reserva_modelo.vencer_consumos_pendientes`, `registrar_accion`, `Sesion`.
- Produces:
  - `CierreControlador().cerrar_dia() -> (bool, dict|str)`
  - `CierreControlador().barrido_inicial() -> (bool, dict|str)`
  - dict con claves `cerradas`, `descartadas`, `vencidas`.

- [ ] **Step 1: Crear el archivo**

```python
"""
Cierre de mesas del restaurante. Al cerrar el dia (boton) o al abrir el sistema
(barrido de lo que quedo de dias anteriores) se consolidan las mesas abiertas:
las que tienen consumo cargado pasan a 'cerrada', las vacias se descartan y las
reservas que quedaron sin consumo se marcan como vencidas. Orquesta consumo +
reservas, por eso vive en su propio controlador.
"""

from datetime import date, timedelta

from mysql.connector import Error

from modelo import consumo_modelo, reserva_modelo
from modelo.historial_modelo import registrar_accion
from utilidades.sesion import Sesion


class CierreControlador:

    def cerrar_dia(self):
        # Cierre manual desde el panel: incluye el dia de hoy.
        return self._cerrar_hasta(date.today(), "Cerró el día")

    def barrido_inicial(self):
        # Al iniciar sesion: cierra solo lo que quedo de dias ANTERIORES, por si
        # el dia anterior no se cerro a mano. No toca las mesas abiertas de hoy.
        limite = date.today() - timedelta(days=1)
        return self._cerrar_hasta(limite, "Cierre automático de mesas de días anteriores")

    def _cerrar_hasta(self, fecha_limite, descripcion):
        try:
            cerradas = consumo_modelo.cerrar_abiertas_con_items(fecha_limite)
            descartadas = consumo_modelo.eliminar_abiertas_vacias(fecha_limite)
            vencidas = reserva_modelo.vencer_consumos_pendientes(fecha_limite)
        except Error:
            return False, "No se pudo completar el cierre de mesas."

        # Solo se registra en el historial si de verdad hubo algo que cerrar, para
        # no ensuciar el log con un cierre vacio cada vez que se abre el sistema.
        if cerradas + descartadas + vencidas > 0:
            registrar_accion(
                Sesion().usuario_id,
                f"{descripcion}: {cerradas} mesas cerradas, "
                f"{descartadas} vacías descartadas, {vencidas} sin consumo vencidas.",
            )
        return True, {"cerradas": cerradas, "descartadas": descartadas, "vencidas": vencidas}
```

- [ ] **Step 2: Verificación (import)**

Con el venv activo, correr:
```bash
python -c "from controlador.cierre_controlador import CierreControlador; print('ok')"
```
Esperado: imprime `ok` sin errores de import.

---

### Task 8: Panel de Inicio — Notificaciones, Cerrar día, barrido

**Files:**
- Modify: `vista/principal.ui:300-304` (botón), `:555-557` (subtítulo)
- Modify: `vista/principal_ventana.py` (textos, botón, barrido)

**Interfaces:**
- Consumes: `CierreControlador().cerrar_dia()`, `CierreControlador().barrido_inicial()`.

- [ ] **Step 1: Renombrar el botón en `principal.ui`**

Reemplazar el widget `pushButton_actualizar` (líneas 300-304) por:

```xml
          <widget class="QPushButton" name="pushButton_cerrarDia">
           <property name="text">
            <string>Cerrar día</string>
           </property>
          </widget>
```

- [ ] **Step 2: Renombrar el subtítulo en `principal.ui`**

En `label_subtituloAvisos` (línea ~557), cambiar el texto:

```xml
             <widget class="QLabel" name="label_subtituloAvisos">
              <property name="text">
               <string>Notificaciones</string>
              </property>
```

- [ ] **Step 3: Actualizar textos y conexión en `principal_ventana.py`**

- Línea 104: cambiar la conexión del botón:
```python
        self.pushButton_cerrarDia.clicked.connect(self.cerrar_dia)
```
- Línea ~157: `self.label_subtituloAvisos.setText("Pendientes")` → `setText("Notificaciones")`.
- Línea ~154: el texto vacío `"No hay pendientes. Todo al día."` se puede dejar; opcional cambiarlo a `"No hay notificaciones. Todo al día."`.
- Línea ~165: `f"Pendientes ({len(avisos)})"` → `f"Notificaciones ({len(avisos)})"`.

- [ ] **Step 4: Barrido al abrir el sistema**

En `__init__`, después de `self.label_nombreUsuario.setText(...)` (línea 54):

```python
        # Al abrir el sistema, cierra lo que haya quedado abierto de dias
        # anteriores (por si ayer no se cerro a mano). Silencioso: solo actua si
        # hay algo que cerrar.
        from controlador.cierre_controlador import CierreControlador
        CierreControlador().barrido_inicial()
```

- [ ] **Step 5: Método `cerrar_dia`**

Agregar en la sección de acciones del panel (junto a `resolver_aviso`):

```python
    def cerrar_dia(self):
        # Cierre manual del dia: pide confirmacion porque cierra mesas y vence
        # reservas sin consumo. Al terminar, refresca el panel.
        from controlador.cierre_controlador import CierreControlador

        resp = QMessageBox.question(
            self, "Cerrar día",
            "Se van a cerrar todas las mesas abiertas de hoy, descartar las vacías "
            "y marcar como vencidas las reservas sin consumo. ¿Confirmás?",
            QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return

        exito, datos = CierreControlador().cerrar_dia()
        if not exito:
            QMessageBox.warning(self, "Cerrar día", datos)
            return
        QMessageBox.information(
            self, "Cerrar día",
            f"Día cerrado.\n"
            f"Mesas cerradas: {datos['cerradas']}\n"
            f"Mesas vacías descartadas: {datos['descartadas']}\n"
            f"Reservas sin consumo vencidas: {datos['vencidas']}")
        self.cargar_panel()
```

- [ ] **Step 6: Verificación visual (Gabriel)**

Al abrir el sistema, las mesas abiertas de días anteriores quedan cerradas/descartadas y las reservas viejas sin consumo desaparecen de Notificaciones. El panel dice "Notificaciones (N)". El botón "Cerrar día" pide confirmación y muestra el resumen; después el panel se refresca solo. No queda ningún botón "Actualizar".

---

## Commits

Gabriel maneja sus propios commits. Sugerencia de agrupación (uno por task, o los que quiera juntar): `Task 1-3` (precios: modelo + controlador), `Task 4-5` (precios: UI), `Task 6-8` (cierre de mesas + panel). Mensajes en el estilo del repo (ej: "fix precios: especial automatico y editar vigente", "feat: cierre de mesas y notificaciones").

## Self-review — cobertura del spec

- Punto 1 (un solo precio + especial auto) → Tasks 3, 4, 5. ✅
- Punto 2 (Pendientes → Notificaciones) → Task 8. ✅
- Punto 3 (qué falta) → cubierto por editar vigente (Task 5) + especial atado al medio (Task 3). ✅
- Punto 4 (editar el vigente) → Tasks 2, 3, 4, 5. ✅
- Punto 5 (bug notificaciones) → Task 2. ✅
- Punto 6 (sacar Actualizar) → Task 8. ✅
- Punto 7 (cierre de mesas) → Tasks 1, 6, 7, 8. ✅
- Cambio de esquema (`consumo_vencido`) → Task 1, usado en Tasks 6, 8. ✅
