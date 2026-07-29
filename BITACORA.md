# Bitacora de cambios — Proyecto Practicas II (Restaurante)

Registro de los cambios que vamos haciendo, para retomar sin releer todo el proyecto.
Se agrega una entrada por cada cambio. Lo mas nuevo va arriba.

## Como esta armado (contexto rapido)
- **Stack:** Python + PyQt5, arquitectura MVC (vista / controlador / modelo).
- **Vistas:** cada pantalla es `algo.ui` (Qt Designer) + `algo_ventana.py` que lo carga con `uic.loadUi`.
- **Estilos:** todo centralizado en `recursos/style.css` (QSS), seleccionado por `objectName`.
- **Navegacion:** SPA de una sola ventana (`QStackedWidget`), sub-ventanas como `QDialog`.
- **Login:** `vista/login.ui` + `vista/login_ventana.py`; controlador en `controlador/login_controlador.py`.
- **Entorno:** venv propio (no Python del sistema), MySQL via XAMPP, `config.ini` local.

---

## Pendiente / en curso

_(nada abierto)_

---

## Historial

### 2026-07-29 — Consumo (Nuevo consumo): columnas, cantidad y buscador de item ✅
Dialogo `DialogoConsumo`:
1. **Columnas ordenadas:** se saco `stretchLastSection` (dejaba "Subtotal" enorme). Ahora "Item" = `Stretch` y Cantidad/Precio unit./Subtotal = `ResizeToContents`. Importes (Precio unit. y Subtotal) alineados a la derecha; Cantidad centrada.
2. **Input de cantidad:** se agrego label "Cantidad" antes del spinbox, se lo achico (max 84px) y se centro el numero. El combo de item pasa a estirarse (ocupa el espacio libre).
3. **Buscador de item:** el combo se volvio editable con autocompletar `MatchContains` (se tipea el nombre y filtra), para no scrollear entre cientos de items. `agregar_item` resuelve el texto tipeado con `findText` y avisa si no coincide. Mismo patron que el buscador de cliente en Reservas.

**Archivos:** `vista/consumo/consumo_form.ui` (fila "Agregar items": sizePolicy del combo, label_cantidad, spinbox angosto/centrado), `vista/consumo/consumo_form_ventana.py` (imports `QComboBox`/`QCompleter`/`QHeaderView`; resize modes; combo buscable; resolucion en `agregar_item`; alineacion de importes).

**Extra (mismo dia):** editar cantidad de un item ya cargado con **doble clic** en la fila → `QInputDialog.getInt` (1–99). Antes solo se podia quitar y volver a agregar. No edita si la cuenta esta cerrada (usa `pushButton_agregar.isEnabled()` como proxy de solo-lectura). Import `QInputDialog`, conexion `doubleClicked`, tooltip en la tabla.

### 2026-07-29 — Salon: registrar reserva desde el plano + renombrar botones ✅
Panel de detalle de la mesa (`frame_detalle`):
1. **Nuevo boton "Registrar Reserva"** (arriba): se habilita solo si la mesa esta **libre** en el horario visto. Abre el mismo `DialogoReserva` del modulo Reservas, precargando la mesa elegida y el horario actual. El choque de horarios lo valida el controlador (`hay_superposicion`) al guardar — no se reimplemento nada.
2. "Marcar asistencia" → **"Cambiar Estado"**.
3. "Cargar / editar consumo" → **"Cargar Consumo"**.
4. "Ver consumo" sin cambios.

**Archivos tocados:**
- `vista/reservas/reserva_form_ventana.py` — `DialogoReserva.__init__` acepta `mesa_id` y `hora_inicio` opcionales (precarga al dar de alta; se ignoran al editar).
- `vista/salon/salon.ui` — nuevo `pushButton_reserva`; renombre de `pushButton_asistencia` y `pushButton_consumo`.
- `vista/salon/salon_ventana.py` — import `LIBRE` y `DialogoReserva`; conexion + metodo `registrar_reserva`; habilita `pushButton_reserva` con `estado == LIBRE` (y lo apaga en la rama sin mesa).

### 2026-07-29 — Pestanas (QTabBar): fix texto recortado al seleccionar ✅
La pestana activa usaba `font-weight: 600` y Qt calcula el ancho con el peso normal → al seleccionarla el texto (negrita, mas ancho) se recortaba. Fix en `recursos/style.css`: mismo `font-weight: 500` en todos los estados (la activa se distingue por el fondo azul), + `padding` y `min-width: 90px` para dar aire, + hover. Afecta a todos los `QTabWidget` (Salon `tabWidget_pisos`, Estadisticas, etc.) por ser CSS global.

### 2026-07-29 — Salon: leyenda de colores movida a tooltip ✅
La franja de referencias del pie se saco. Ahora es un "ⓘ Referencias" en la barra superior (a la derecha, despues del resumen) y los colores van en el tooltip (rich text de Qt, un ■ de color por estado). Se elimino el `layout_botones` del pie (quedaba vacio). Archivos: `vista/salon/salon.ui`, `vista/salon/salon_ventana.py`.

### 2026-07-29 — Salon: fix seleccion multiple + selector de horario simple ✅
Dos cambios en el modulo Salon:

1. **Bug de seleccion multiple:** los cards de mesa (`QPushButton` checkable) no estaban en grupo exclusivo → se acumulaba el borde azul de "seleccionada" en varias a la vez. Fix: `QButtonGroup` exclusivo (`_grupo_mesas`, recreado en cada `cargar_salon`), y al redibujar se re-marca (`setChecked(True)`) la mesa que estaba elegida.
2. **Selector de horario:** se reemplazo `timeEdit_hora` (spinner) + boton "Ahora" + combo "Ir a" por **un solo dropdown** `comboBox_horario` = "Ahora" (hora real, data `None`) + los horarios donde hoy hay reservas (`horarios_sugeridos`). No se elige hora arbitraria: el plano solo tiene sentido en los turnos con reservas. Solo la hora, sin nombre de turno (el modelo devuelve `hora_inicio` nomas).

**Archivos tocados:**
- `vista/salon/salon.ui` — toolbar: label "Ver salon a las" + `comboBox_horario`; se quitaron `timeEdit_hora`, `pushButton_ahora`, `label_sugeridos`, `comboBox_sugeridos`.
- `vista/salon/salon_ventana.py` — import `QButtonGroup`; grupo exclusivo de mesas; `_cargar_horarios()` + `_hora_elegida()` reemplazan `_cargar_horarios_sugeridos`/`ir_a_ahora`/`ir_a_sugerido`; `cargar_salon` lee del combo; se limpio el import `Qt` (ya no se usa).

### 2026-07-29 — Consumo: rango de fechas por defecto ayer→hoy ✅
En `vista/consumo/consumo_ventana.py` el filtro arrancaba con "Hasta" a un ano adelante. Ahora `dateEdit_desde` = ayer (`currentDate().addDays(-1)`) y `dateEdit_hasta` = hoy, asi al entrar se ven los consumos recientes sin filtrar.

### 2026-07-29 — Rediseno del navbar ✅
Cuatro cambios sobre la barra lateral (`widget_menu`):
1. **Orden por prioridad:** Inicio → Salon → Reservas → Consumo → Clientes → Mesas → Menu → Estadisticas → Usuarios → Historial de acciones (operacion diaria arriba, administracion/auditoria abajo).
2. **Estado activo:** el modulo actual queda con fondo azul lleno. Botones `checkable` en un `QButtonGroup` exclusivo (`_grupo_navbar`); arranca marcado "Inicio". CSS: `QPushButton:checked` (+ `:checked:hover`).
3. **Sin logos de letras:** se quito el cuadrado "R" (`label_marcaIcono`) del header y el circulo "A" (`label_avatar`) del usuario. El header queda solo texto: "Restaurante" + "Sistema de gestion".
4. **Usuario reubicado:** bajo al pie del navbar (arriba de "Cerrar sesion") como texto simple (nombre + rol), con un separador fino (`separador_pie`). Se elimino la tarjeta `frame_perfil`.

**Archivos tocados:**
- `vista/principal.ui` — bloque `layout_menu` reescrito completo.
- `recursos/style.css` — se eliminaron `label_marcaIcono`, `frame_perfil`, `label_avatar`; se agrego `QPushButton:checked`/`:checked:hover` (azul activo) y `QFrame#separador_pie`.
- `vista/principal_ventana.py` — import `QButtonGroup`; se quito `label_avatar.setText`; nuevo `_grupo_navbar` exclusivo con los 10 botones checkable + `pushButton_inicio.setChecked(True)`.

**Nota:** `label_rolUsuario` sigue fijo en "Administrador" (texto del `.ui`), no se lee de `Sesion()`.

### 2026-07-29 — Modulo "Inicio" en navbar + quitar boton "Volver" ✅
El panel de resumen que se ve al entrar ahora es un modulo mas del navbar, llamado **"Inicio"**. Se saco el boton "Volver" de los 9 modulos: para volver al panel se hace clic en "Inicio".

**Nombre elegido:** "Inicio" (en espanol, corto; se descarto "Dashboard" por anglicismo en contexto de catedra).

**Como funciona ahora:** el navbar es un `QStackedWidget`. "Inicio" (`pushButton_inicio` → `ir_al_inicio()`) muestra la pagina 0 (panel) y recarga los numeros. Cada modulo se muestra como otra pagina.

**Archivos tocados:**
- `vista/principal.ui` — nuevo `pushButton_inicio` "Inicio" como primer item de MODULOS.
- `vista/principal_ventana.py` — conecta `pushButton_inicio` a `ir_al_inicio`; los 9 `abrir_*` pasan la clase directo (`_mostrar_modulo(VentanaX)`) sin `al_volver`.
- Los 9 `vista/<mod>/<mod>_ventana.py` (salon, usuarios, historial, mesas, clientes, menu, reservas, consumo, estadisticas) — se quito el parametro `al_volver`, `self._al_volver`, la conexion de `pushButton_volver` y el metodo `_volver`.
- Los 9 `vista/<mod>/<mod>.ui` — se quito el `<widget pushButton_volver>` (se dejo el spacer `espaciador_botones`, mantiene los demas botones a la izquierda).

**OJO — no se tocaron:** los sub-dialogos modales (`precios`, `grupos_menu`, `grupos_mesa`, `consumo_detalle`, `cliente_reservas`, `usuario_form`) conservan su "Volver"/"Cerrar" porque cierran un pop-up, no navegan entre modulos del navbar.

**Verificado:** `py_compile` de los 9 modulos + principal (OK); carga con `uic.loadUi` de todos los `.ui` en offscreen (OK). Falta prueba visual real corriendo la app (necesita MySQL/XAMPP arriba).



### 2026-07-29 — Simplificar UI del Login ✅
Login comun y basico, sin el diseno "PRO" de dos paneles.

**Que se saco:**
- Panel oscuro de marca (titulo grande, descripcion "Clientes, reservas…", pie "Practicas II — Macko y Segovia").
- Logo cuadrado azul con la "R".
- Subtitulo "Ingresa con tu usuario de administrador."
- Placeholders redundantes de los campos (repetian el label).

**Que quedo:** una sola columna centrada → encabezado "Gestion de Restaurante", titulo "Iniciar sesion", labels + campos (Usuario / Contrasena), mensaje de error y boton "Ingresar".

**Ventana:** 420×420 fija y centrada en pantalla. No se agranda, no se redimensiona, boton de maximizar inhabilitado (`setFixedSize` en el `__init__`).

**Archivos tocados:**
- `vista/login.ui` — reescrito: `QHBoxLayout` de 2 paneles → `QVBoxLayout` de una columna. Se conservaron los `objectName` que usa el controlador (`lineEdit_usuario`, `lineEdit_contrasena`, `pushButton_ingresar`, `label_error`).
- `recursos/style.css` — se elimino el bloque del login viejo (`widget_marca`, `label_marcaIcono`, `label_marcaTexto`, `label_pie`, `widget_formulario`, `label_bienvenida`). Nuevo: `QWidget#VentanaLogin` fondo blanco + `label_marcaTitulo` como encabezado chico (13pt/600).
- `vista/login_ventana.py` — `setFixedSize(420,420)` + helper `_centrar_en_pantalla()`; import de `QApplication`.

**Verificado:** carga del `.ui` y parseo del CSS en modo offscreen (OK). Falta prueba visual real corriendo la app.
