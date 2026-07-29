# Especificacion de modulos — Sistema de Gestion de Restaurante

Basado en la consigna de Practicas II. Este documento es la referencia que Claude Code debe seguir al programar cada modulo. Todas las reglas de negocio estan tomadas literalmente de la consigna.

Tabla de referencia cruzada con `schema.sql`: cada modulo indica que tablas usa.

---

## 0. Login / Sesion

**Tablas:** `usuarios`

- Formulario con usuario + contrasena (`QLineEdit` en modo password para la contrasena).
- Verificacion de contrasena con `bcrypt.checkpw` contra `contrasena_hash`.
- Al loguear correctamente: actualizar `fecha_ultimo_acceso` y registrar `"Inicio de sesion"` en `historial_acciones`.
- Si falla: `QMessageBox.warning`, sin indicar si el error fue el usuario o la contrasena (buena practica de seguridad).
- Todos los usuarios son administradores → acceso completo a todos los modulos, no hay roles diferenciados.

---

## 1. Usuarios

**Tablas:** `usuarios`, `historial_acciones`

**Campos:** nombre_usuario, contrasena, fecha_creacion, fecha_modificacion, fecha_ultimo_acceso.

**CRUD:** ver (tabla/lista), alta, modificar, eliminar. Reservado a administradores (todos lo son).

**Validaciones:**
- nombre_usuario unico, sin espacios, longitud razonable (ej. 4–30).
- contrasena: minimo 8 caracteres, al menos una mayuscula y un numero (mismo criterio que ya usa `sistema_ejemplo`).
- Nunca guardar ni mostrar la contrasena en texto plano — hash con `bcrypt` antes de insertar.
- No permitir eliminar el unico usuario restante (para no bloquear el acceso al sistema).

**Widgets:** `QLineEdit` (usuario), `QLineEdit` con `setEchoMode(Password)` (contrasena), `QTableView`/`QTableWidget` para el listado, fechas mostradas en `QLabel` (son de solo lectura, gestionadas por el sistema).

**Al guardar cualquier alta/baja/modificacion:** registrar la accion en `historial_acciones`.

---

## 2. Historial de acciones

**Tablas:** `historial_acciones`, `usuarios`

- Listado de acciones con: usuario que la realizo, descripcion de la accion, fecha y hora.
- Filtro por usuario (`QComboBox` con lista de usuarios) y por rango de fechas (`QDateEdit` desde/hasta, o `QCalendarWidget`).
- Es de solo lectura (no se edita ni elimina el historial).

**Convencion de registro:** cada modulo (Usuarios, Clientes, Reservas, Mesas, Menu, Consumo) debe llamar a una funcion comun `registrar_accion(usuario_id, descripcion)` al hacer alta/baja/modificacion e inicio de sesion. Esto evita duplicar codigo (item evaluado explicitamente en la consigna).

---

## 3. Clientes

**Tablas:** `clientes`, `reservas`

**Campos:** nombre, apellido, DNI, fecha de nacimiento, direccion, telefono, fecha de registro.

**CRUD:** ver, alta, modificar, eliminar.

**Validaciones:**
- DNI unico, solo numerico, longitud 7–8 (Argentina).
- fecha_nacimiento: `QDateEdit`, no puede ser fecha futura, cliente debe ser mayor de edad si aplica (a definir con el docente si es requisito; por defecto solo se valida que no sea futura).
- telefono: formato numerico simple, se puede usar `QLineEdit` con validador de `QRegularExpressionValidator`.

**Regla critica de eliminacion:** antes de eliminar un cliente, comprobar que no tenga reservas con fecha actual o futura (`SELECT` en `reservas` con `fecha >= CURDATE()`). Si tiene, bloquear el borrado y avisar con `QMessageBox`.

**Vista de detalle de cliente:** al ver un cliente especifico, mostrar sus reservas (pasadas, actuales, futuras) en una tabla embebida o ventana secundaria, con fecha, mesa y estado.

**Estadisticas (pantalla o seccion aparte):**
- Numero total de clientes: `SELECT COUNT(*) FROM clientes`.
- Top 5 clientes con mas reservas: `SELECT cliente_id, COUNT(*) FROM reservas GROUP BY cliente_id ORDER BY COUNT(*) DESC LIMIT 5` + join con `clientes` para mostrar nombre.

**Widgets:** `QLineEdit` (texto), `QDateEdit` (fechas), `QTableView` para listado y para reservas del cliente.

---

## 4. Reservas

**Tablas:** `reservas`, `clientes`, `mesas`, `grupos_mesa`

**Campos:** cliente, mesa, fecha, hora inicio, hora fin, duracion (2h/3h), estado de asistencia.

**CRUD:** ver, alta, modificar, eliminar — **excepto reservas pasadas** (fecha < hoy): no se pueden modificar ni eliminar, solo consultar. Validar esto tanto deshabilitando los botones en la UI como revalidando en la capa de datos antes de ejecutar el `UPDATE`/`DELETE`.

**Calculo de precio:**
- 2 horas → 100% del valor del grupo de la mesa.
- 3 horas → 125% del valor del grupo de la mesa.
- El precio calculado se guarda en `reservas.precio_mesa_aplicado` al momento de crear la reserva (no se recalcula despues, aunque cambie el valor del grupo).

**Estado de asistencia:** `QComboBox` con las 4 opciones: en espera, asistio, tardanza, falto. Editable en cualquier momento (incluso en reservas pasadas, para poder marcar retroactivamente si asistio o falto).

**Validaciones:**
- No permitir superposicion de horario para la misma mesa (mismo dia, rango de horas que se cruza) — buena practica aunque no esta explicitamente pedida, vale la pena mencionarla en la defensa.
- hora_fin debe ser posterior a hora_inicio y coherente con la duracion elegida (2h o 3h exactas).

**Widgets:** `QComboBox` (cliente, mesa, duracion, estado), `QDateEdit` (fecha), `QTimeEdit` (horas).

**Estadisticas:**
- Reservas actuales y futuras: `SELECT COUNT(*) FROM reservas WHERE fecha >= CURDATE()`.
- Reservas por mes: `SELECT MONTH(fecha), YEAR(fecha), COUNT(*) FROM reservas GROUP BY YEAR(fecha), MONTH(fecha) ORDER BY YEAR(fecha), MONTH(fecha)`.

---

## 5. Mesas

**Tablas:** `mesas`, `grupos_mesa`

**Campos:** numero de sillas, numero unico de mesa, piso, codigo (letra de piso + numero), grupo.

**CRUD:** ver, alta, modificar, eliminar.

**Regla del codigo:** se genera automaticamente combinando la letra del piso (0→A, 1→B, 2→C, ...) con el numero de mesa. Ej: piso 0, mesa 5 → "A5". Generarlo en la capa de aplicacion al guardar y mostrarlo como campo de solo lectura en el formulario (no editable a mano, para evitar inconsistencias).

**Grupos de mesa:** pantalla/seccion aparte para crear y editar grupos (nombre + valor). El valor es el precio base de 2 horas; el precio de 3 horas se calcula (no se guarda un segundo valor).

**Validaciones:**
- numero de mesa unico.
- numero de sillas: `QSpinBox` (entero positivo, sin decimales).
- piso: `QSpinBox` o `QComboBox` con las opciones disponibles.
- valor del grupo: `QDoubleSpinBox` (nunca `QLineEdit` para precios).

**Widgets:** `QSpinBox` (sillas, piso), `QComboBox` (grupo), `QDoubleSpinBox` (valor de grupo).

---

## 6. Menu

**Tablas:** `menu_items`, `grupos_menu`, `historial_precios_menu`

**Campos del item:** nombre, descripcion, imagen, grupo, precio (gestionado via historial).

**CRUD:** ver, alta, modificar, eliminar items de menu. Crear y editar grupos de menu (nombre) desde una pantalla aparte, igual que los grupos de mesa.

**Precio del item:**
- Cada cambio de precio crea una nueva fila en `historial_precios_menu` con `fecha_inicio` = hoy y cierra la fila anterior poniendo su `fecha_fin` = ayer (o el dia anterior al nuevo `fecha_inicio`).
- Precio de lista (siempre) + precio especial opcional asociado a un medio de pago (efectivo o transferencia).
- Precio vigente = la fila cuya `fecha_inicio <= hoy` y (`fecha_fin IS NULL` o `fecha_fin >= hoy`).

**Aviso de renovacion:** al ver el detalle de un item, si `fecha_fin` del precio vigente esta a 10 dias o menos (y no es NULL), mostrar un mensaje de advertencia (`QMessageBox.information` o un `QLabel` destacado en rojo/naranja) indicando que se acerca la fecha de renovacion.

**Historial de precios:** pantalla o pestana con la lista de precios historicos del item, mostrando ademas la **variacion porcentual** entre cada cambio: `(precio_nuevo - precio_anterior) / precio_anterior * 100`, calculada en Python al recorrer la lista ordenada por fecha.

**Imagen:** selector de archivo (`QFileDialog`), copiar la imagen a una carpeta del proyecto gestionada con `pathlib` (ej. `data/img/menu/`), y guardar solo la ruta relativa en la base. Nunca guardar la imagen binaria en MySQL.

**Widgets:** `QComboBox` (grupo), `QDoubleSpinBox` (precios), `QLabel` con `QPixmap` (previsualizacion de imagen), `QDateEdit` (si se necesita fijar fecha de inicio manualmente, aunque por defecto es "hoy").

---

## 7. Consumo

**Tablas:** `consumos`, `consumo_detalle`, `reservas`, `menu_items`, `historial_precios_menu`

**Campos:** reserva asociada, fecha, medio de pago, items consumidos (con cantidad), precio final calculado.

**Regla de un consumo por reserva:** `consumos.reserva_id` es `UNIQUE` — no se puede cargar mas de un consumo por reserva (columna refleja la regla de negocio).

**Calculo del precio final:**
1. Por cada item agregado al consumo, resolver su precio vigente a la fecha del consumo.
2. Si el item tiene precio especial y coincide con el medio de pago elegido → usar `precio_especial`.
3. Si no, usar `precio_lista`.
4. Guardar ese precio resuelto en `consumo_detalle.precio_unitario_aplicado` (snapshot, no se recalcula despues).
5. `consumos.precio_total` = suma de `cantidad * precio_unitario_aplicado` de todos los detalles.

**Widgets:** `QComboBox` (reserva, medio de pago), tabla editable (`QTableWidget`) para agregar items con `QSpinBox` de cantidad, `QDoubleSpinBox` de solo lectura para mostrar precio total.

**Estadisticas de consumo (mensual, por dia de la semana):**
- Top 5 items mas consumidos por dia de la semana del mes seleccionado:
  ```sql
  SELECT DAYNAME(c.fecha) AS dia, mi.nombre, SUM(cd.cantidad) AS total
  FROM consumo_detalle cd
  JOIN consumos c ON c.id = cd.consumo_id
  JOIN menu_items mi ON mi.id = cd.menu_item_id
  WHERE YEAR(c.fecha) = %s AND MONTH(c.fecha) = %s
  GROUP BY dia, mi.id
  ORDER BY dia, total DESC;
  ```
  (en Python, agrupar por dia y quedarse con el top 5 de cada uno).
- Dinero que ingresa por dia de la semana:
  ```sql
  SELECT DAYNAME(c.fecha) AS dia, SUM(c.precio_total) AS ingreso
  FROM consumos c
  WHERE YEAR(c.fecha) = %s AND MONTH(c.fecha) = %s
  GROUP BY dia;
  ```

---

## 8. Filtros (transversal a todos los listados)

Todos los listados (usuarios, clientes, reservas, mesas, menu) deben soportar:
- Filtro por nombre (o campo de texto principal de la entidad) — `QLineEdit` con busqueda al tipear o boton "Buscar".
- Filtro por codigo de registro (DNI en clientes, codigo en mesas, id en otros).
- Filtro por rango de fechas (`QDateEdit` desde/hasta).

**Recomendacion de implementacion:** una funcion generica `construir_filtro_sql(nombre=None, codigo=None, fecha_desde=None, fecha_hasta=None)` reutilizada por los distintos modulos, para no repetir logica de armado de `WHERE` (cumple el item de "reutilizacion de codigo mediante funciones").

---

## Resumen de widgets obligatorios por tipo de dato

| Tipo de dato | Widget |
|---|---|
| Precio / valor monetario | `QDoubleSpinBox` |
| Cantidad entera (sillas, cantidad de items) | `QSpinBox` |
| Fecha | `QDateEdit` (o `QCalendarWidget`) |
| Hora | `QTimeEdit` |
| Seleccion cerrada (grupo, estado, medio de pago, rol) | `QComboBox` |
| Texto libre corto | `QLineEdit` |
| Texto libre largo (descripcion) | `QPlainTextEdit` o `QTextEdit` |
| Listados | `QTableView` (con modelo) o `QTableWidget` |

Prohibido usar `QLineEdit` para precios, cantidades o fechas (marcado explicitamente en la consigna como error a evitar).

---

## Convencion de nombres de widgets en los `.ui`

Mismo criterio en los 8 modulos, tomado de `sistema_ejemplo` (prefijo = nombre de clase del widget):

`lineEdit_<campo>`, `pushButton_<accion>`, `label_<contenido>`, `label_error_<campo>` (para mensajes de validacion), `comboBox_<campo>`, `dateEdit_<campo>`, `timeEdit_<campo>`, `doubleSpinBox_<campo>`, `spinBox_<campo>`, `tableWidget_<entidad>`.

Ej: `lineEdit_dni`, `pushButton_guardar`, `label_error_dni`, `comboBox_estadoAsistencia`, `doubleSpinBox_precioLista`, `tableWidget_reservas`.

Cada modulo mapea a estos archivos (ver `CLAUDE.md` para la estructura completa):

| Modulo | Modelo | Vista | Controlador |
|---|---|---|---|
| Usuarios | `modelo/usuario_modelo.py` | `vista/usuarios/*` | `controlador/usuarios_controlador.py` |
| Historial | `modelo/historial_modelo.py` | `vista/historial/*` | `controlador/historial_controlador.py` |
| Clientes | `modelo/cliente_modelo.py` | `vista/clientes/*` | `controlador/clientes_controlador.py` |
| Reservas | `modelo/reserva_modelo.py` | `vista/reservas/*` | `controlador/reservas_controlador.py` |
| Mesas | `modelo/mesa_modelo.py`, `modelo/grupo_mesa_modelo.py` | `vista/mesas/*` | `controlador/mesas_controlador.py` |
| Menu | `modelo/menu_modelo.py`, `modelo/grupo_menu_modelo.py`, `modelo/precio_menu_modelo.py` | `vista/menu/*` | `controlador/menu_controlador.py` |
| Consumo | `modelo/consumo_modelo.py` | `vista/consumo/*` | `controlador/consumo_controlador.py` |
| Estadisticas | (consultas directas o `modelo/estadisticas_modelo.py`) | `vista/estadisticas/*` | `controlador/estadisticas_controlador.py` |
