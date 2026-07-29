# Bitácora de cambios — Proyecto Prácticas II (Restaurante)

Registro de los cambios que vamos haciendo, para retomar sin releer todo el proyecto.
Se agrega una entrada por cada cambio. Lo más nuevo va arriba.

## Cómo está armado (contexto rápido)
- **Stack:** Python + PyQt5, arquitectura MVC (vista / controlador / modelo).
- **Vistas:** cada pantalla es `algo.ui` (Qt Designer) + `algo_ventana.py` que lo carga con `uic.loadUi`.
- **Estilos:** todo centralizado en `recursos/style.css` (QSS), seleccionado por `objectName`.
- **Navegación:** SPA de una sola ventana (`QStackedWidget`), sub-ventanas como `QDialog`.
- **Login:** `vista/login.ui` + `vista/login_ventana.py`; controlador en `controlador/login_controlador.py`.
- **Entorno:** venv propio (no Python del sistema), MySQL vía XAMPP, `config.ini` local.

---

## Pendiente / en curso

_(nada abierto)_

---

## Historial

### 2026-07-29 — Rediseño del navbar ✅
Cuatro cambios sobre la barra lateral (`widget_menu`):
1. **Orden por prioridad:** Inicio → Salón → Reservas → Consumo → Clientes → Mesas → Menú → Estadísticas → Usuarios → Historial de acciones (operación diaria arriba, administración/auditoría abajo).
2. **Estado activo:** el módulo actual queda con fondo azul lleno. Botones `checkable` en un `QButtonGroup` exclusivo (`_grupo_navbar`); arranca marcado "Inicio". CSS: `QPushButton:checked` (+ `:checked:hover`).
3. **Sin logos de letras:** se quitó el cuadrado "R" (`label_marcaIcono`) del header y el círculo "A" (`label_avatar`) del usuario. El header queda solo texto: "Restaurante" + "Sistema de gestión".
4. **Usuario reubicado:** bajó al pie del navbar (arriba de "Cerrar sesión") como texto simple (nombre + rol), con un separador fino (`separador_pie`). Se eliminó la tarjeta `frame_perfil`.

**Archivos tocados:**
- `vista/principal.ui` — bloque `layout_menu` reescrito completo.
- `recursos/style.css` — se eliminaron `label_marcaIcono`, `frame_perfil`, `label_avatar`; se agregó `QPushButton:checked`/`:checked:hover` (azul activo) y `QFrame#separador_pie`.
- `vista/principal_ventana.py` — import `QButtonGroup`; se quitó `label_avatar.setText`; nuevo `_grupo_navbar` exclusivo con los 10 botones checkable + `pushButton_inicio.setChecked(True)`.

**Nota:** `label_rolUsuario` sigue fijo en "Administrador" (texto del `.ui`), no se lee de `Sesion()`.

### 2026-07-29 — Módulo "Inicio" en navbar + quitar botón "Volver" ✅
El panel de resumen que se ve al entrar ahora es un módulo más del navbar, llamado **"Inicio"**. Se sacó el botón "Volver" de los 9 módulos: para volver al panel se hace clic en "Inicio".

**Nombre elegido:** "Inicio" (en español, corto; se descartó "Dashboard" por anglicismo en contexto de cátedra).

**Cómo funciona ahora:** el navbar es un `QStackedWidget`. "Inicio" (`pushButton_inicio` → `ir_al_inicio()`) muestra la página 0 (panel) y recarga los números. Cada módulo se muestra como otra página.

**Archivos tocados:**
- `vista/principal.ui` — nuevo `pushButton_inicio` "Inicio" como primer ítem de MÓDULOS.
- `vista/principal_ventana.py` — conecta `pushButton_inicio` a `ir_al_inicio`; los 9 `abrir_*` pasan la clase directo (`_mostrar_modulo(VentanaX)`) sin `al_volver`.
- Los 9 `vista/<mod>/<mod>_ventana.py` (salon, usuarios, historial, mesas, clientes, menu, reservas, consumo, estadisticas) — se quitó el parámetro `al_volver`, `self._al_volver`, la conexión de `pushButton_volver` y el método `_volver`.
- Los 9 `vista/<mod>/<mod>.ui` — se quitó el `<widget pushButton_volver>` (se dejó el spacer `espaciador_botones`, mantiene los demás botones a la izquierda).

**OJO — no se tocaron:** los sub-diálogos modales (`precios`, `grupos_menu`, `grupos_mesa`, `consumo_detalle`, `cliente_reservas`, `usuario_form`) conservan su "Volver"/"Cerrar" porque cierran un pop-up, no navegan entre módulos del navbar.

**Verificado:** `py_compile` de los 9 módulos + principal (OK); carga con `uic.loadUi` de todos los `.ui` en offscreen (OK). Falta prueba visual real corriendo la app (necesita MySQL/XAMPP arriba).



### 2026-07-29 — Simplificar UI del Login ✅
Login común y básico, sin el diseño "PRO" de dos paneles.

**Qué se sacó:**
- Panel oscuro de marca (título grande, descripción "Clientes, reservas…", pie "Prácticas II — Macko y Segovia").
- Logo cuadrado azul con la "R".
- Subtítulo "Ingresá con tu usuario de administrador."
- Placeholders redundantes de los campos (repetían el label).

**Qué quedó:** una sola columna centrada → encabezado "Gestión de Restaurante", título "Iniciar sesión", labels + campos (Usuario / Contraseña), mensaje de error y botón "Ingresar".

**Ventana:** 420×420 fija y centrada en pantalla. No se agranda, no se redimensiona, botón de maximizar inhabilitado (`setFixedSize` en el `__init__`).

**Archivos tocados:**
- `vista/login.ui` — reescrito: `QHBoxLayout` de 2 paneles → `QVBoxLayout` de una columna. Se conservaron los `objectName` que usa el controlador (`lineEdit_usuario`, `lineEdit_contrasena`, `pushButton_ingresar`, `label_error`).
- `recursos/style.css` — se eliminó el bloque del login viejo (`widget_marca`, `label_marcaIcono`, `label_marcaTexto`, `label_pie`, `widget_formulario`, `label_bienvenida`). Nuevo: `QWidget#VentanaLogin` fondo blanco + `label_marcaTitulo` como encabezado chico (13pt/600).
- `vista/login_ventana.py` — `setFixedSize(420,420)` + helper `_centrar_en_pantalla()`; import de `QApplication`.

**Verificado:** carga del `.ui` y parseo del CSS en modo offscreen (OK). Falta prueba visual real corriendo la app.
