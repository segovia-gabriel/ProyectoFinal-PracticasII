# Convenciones de Fase 2 — que ningun modulo (ni su logica ni su UI) se pise

Este documento es el contrato entre Gabriel y Mijail para construir los 8 modulos
en paralelo sin chocarse, y para que todo sea **defendible con lo que dio el
profesor** (nada de patrones que el no haya mostrado). Se lee una vez antes de
arrancar cada modulo.

## 1. Regla de oro: quien toca que archivo

Cada uno toca SOLO los archivos de sus modulos. Los archivos compartidos se
definieron en la Fase 1 y **no se modifican sin avisar al otro**.

| | Gabriel | Mijail |
|---|---|---|
| Modulos | Usuarios, Historial, Clientes, Reservas | Mesas + Grupos de mesa, Menu + Grupos + Precios, Consumo, Estadisticas |
| `modelo/` | `usuario_modelo.py`, `historial_modelo.py`, `cliente_modelo.py`, `reserva_modelo.py` | `mesa_modelo.py`, `grupo_mesa_modelo.py`, `menu_modelo.py`, `grupo_menu_modelo.py`, `precio_menu_modelo.py`, `consumo_modelo.py` |
| `vista/` | `usuarios/`, `historial/`, `clientes/`, `reservas/` | `mesas/`, `menu/`, `consumo/`, `estadisticas/` |
| `controlador/` | `*_controlador.py` de sus modulos | idem |

**Compartidos (read-only salvo aviso):** `modelo/conexion.py`, `utilidades/*.py`,
`recursos/style.css`, `main.py`, `vista/principal.ui`, `vista/principal_ventana.py`,
`analisis/schema.sql`, `config.ini.example`.

Como cada modulo vive en sus propios archivos, dos personas nunca editan el mismo
archivo → **cero conflictos de merge de logica**.

## 2. Patron de navegacion (fiel al profesor, una sola ventana visible)

Igual que `sistema_ejemplo` (main_window → user_list_window):

- La **ventana principal** (menu lateral) abre la ventana del modulo con
  `self.hide()` y `ventana_modulo.show()`.
- La ventana del modulo, al cerrarse, vuelve a mostrar la principal
  (`closeEvent` → `self.parent().show()`), como hace `user_list_window` del
  ejemplo.
- **Regla anti-pisado:** siempre esconder la ventana anterior antes de abrir la
  nueva. Asi **solo hay una ventana de trabajo visible a la vez** y ninguna se
  superpone a otra.
- Los **formularios de alta/edicion** (equivalentes a `CreateUserWindow` /
  `EditUserWindow` del ejemplo) se abren como ventana **modal**
  (`setWindowModality(Qt.ApplicationModal)` o `QDialog.exec_()`): quedan al
  frente, bloquean la de atras y no se pierden. Nada de `QStackedWidget` ni
  cosas que el profesor no mostro.

## 3. Patron de cada modulo (Modelo / Vista / Controlador)

Copiar la estructura del login (ya hecha) para todos:

- **Modelo** (`modelo/<entidad>_modelo.py`): funciones sueltas, **una = una
  operacion SQL**. Abren conexion con `abrir_conexion()`, usan
  `try/except Error` + `registrar(error, "error")` + `finally` que cierra la
  conexion. Devuelven datos planos (dict/lista/tupla/None). **Nunca importan
  PyQt.**
- **Controlador** (`controlador/<modulo>_controlador.py`): valida los datos,
  llama al modelo, registra la accion en el historial si corresponde, y
  devuelve `(exito, mensaje)` o los datos pedidos. **No importa PyQt.**
- **Vista** (`vista/<modulo>/...`): carga el `.ui` con `uic.loadUi` (ruta con
  `pathlib`), conecta las senales a mano a metodos que llaman al controlador, y
  muestra el resultado (`QMessageBox`, refrescar tabla, etc.). **No hace SQL.**

## 4. No duplicar codigo (lo evalua el profesor)

Usar siempre estas funciones comunes en vez de copiar y pegar:

- Conexion: `from modelo.conexion import abrir_conexion` (nunca hardcodear
  credenciales ni volver a leer `config.ini` a mano).
- Auditoria: `from modelo.historial_modelo import registrar_accion` — llamarla
  en cada alta/baja/modificacion e inicio de sesion.
  `registrar_accion(Sesion().usuario_id, "Creo cliente: Perez, Juan")`.
- Sesion: `from utilidades.sesion import Sesion` — para saber quien esta logueado.
- Hash: `from utilidades.seguridad import hashear_contrasena, verificar_contrasena`.
- Log: `from utilidades.logger import registrar`.
- **Validaciones** (`utilidades/validaciones.py`, a crear al arrancar Fase 2):
  validadores reutilizados por varios modulos (`validar_dni`, `validar_email`,
  `validar_contrasena`, `no_futura`, etc.). Si un validador lo usan los dos,
  vive aca; si es propio de un modulo, va en su controlador.
- **Filtros** (`construir_filtro_sql(...)` en `utilidades/validaciones.py` o
  `modelo/conexion.py`): armado comun del `WHERE` para los filtros transversales
  (nombre, codigo, rango de fechas), para no repetir la logica en cada listado.

Quien cree primero `utilidades/validaciones.py` avisa al otro; a partir de ahi se
agregan validadores sin borrar los del otro (solo se suman funciones).

## 5. Sistema de diseno (todo sale de `recursos/style.css`)

No poner `setStyleSheet` en ninguna ventana: el estilo es global. Para que el QSS
agarre, respetar los `objectName`:

- Titulo de pantalla: `label_titulo`. Subtitulo: `label_subtitulo`. Ayuda: darle
  `property("class", "ayuda")`. Error de campo: `label_error_<campo>`.
- Botones: la accion principal es un `QPushButton` comun (azul). Secundario:
  `pushButton_cancelar` / `pushButton_volver`. Destructivo: `pushButton_eliminar`.
  **Un solo boton primario por pantalla.**
- Campo invalido: `campo.setProperty("error", True)` y refrescar el estilo
  (`campo.style().unpolish(campo); campo.style().polish(campo)`) para que se pinte
  el borde rojo; al corregir, poner `False` y refrescar.
- Widget correcto por dato (obligatorio): `QDoubleSpinBox` precios, `QSpinBox`
  enteros, `QDateEdit` fechas, `QTimeEdit` horas, `QComboBox` opciones cerradas.
  Prohibido `QLineEdit` para precios/cantidades/fechas.
- Layouts reales en los `.ui` (`QVBoxLayout`/`QHBoxLayout`/`QGridLayout`), nunca
  `setGeometry`. Textos en espanol rioplatense simple.

## 6. Checklist antes de mergear un modulo a main

- [ ] Compila y corre (`python main.py`) sin excepciones.
- [ ] Toda consulta SQL y toda carga de archivo/imagen dentro de `try/except`
      con `QMessageBox` claro (no crashea nunca en la demo).
- [ ] Cada campo se valida antes de guardar; el error se ve en pantalla.
- [ ] Cada alta/baja/modificacion llama a `registrar_accion(...)`.
- [ ] Al abrir el modulo se esconde la principal; al cerrarlo, vuelve.
- [ ] Solo se tocaron los archivos propios del modulo.
- [ ] Se puede explicar cada linea en la defensa.
