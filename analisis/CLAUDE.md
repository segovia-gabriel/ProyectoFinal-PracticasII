# CLAUDE.md — Sistema de Gestión de Restaurante (Prácticas II)

Copiar este archivo a la raíz del repo real (el que van a abrir con Claude Code) para que tenga contexto en cada sesión. Este archivo asume que Claude Code va a leer esto primero y arrancar a trabajar solo, así que es intencionalmente explícito.

## Qué es esto

Trabajo final de la cátedra Prácticas II. Sistema de escritorio en Python + PyQt5 + MySQL para gestionar clientes, reservas, mesas y menú de un restaurante. Lo desarrollan dos alumnos (Gabriel y Mijail) en paralelo, con Git, en 4 días. Se va a defender oralmente ante un tribunal — **tienen que poder explicar cada línea**, así que el código debe quedar simple y legible, al nivel de dos alumnos de la materia, no "impresionante".

Documentos de referencia en `analisis/`: `schema.sql` (DER + datos de prueba), `ESPECIFICACION_MODULOS.md` (reglas de negocio por módulo), `PLAN_4_DIAS.md` (cronograma y reparto).

## De dónde partimos — usar los sistemas de ejemplo del profesor

No arrancar de cero. El profesor dio dos proyectos de referencia que hay que leer antes de escribir una sola línea:

- **`sistema_ejemplo/`**: proyecto base con login, alta de usuarios, conexión a MySQL vía `config.ini` + `ConfigParser`, hash de contraseñas con `bcrypt`, logging a archivo con `python-json-logger`, y un singleton `UserSession`. **Esta es la base principal** — el flujo de login, la función `config_db()`, el logger y el patrón de sesión se toman de acá y se adaptan a la estructura MVC nueva.
- **`Practicas Leandro/Final_Practicas_II-main/`**: proyecto completo de un compañero (sistema de cine, otro dominio pero misma cátedra). Sirve como referencia de organización (`views/`, `database/`, `error/`) y de convenciones (`UserSession`, `Database` con métodos tipo `obtener_usuario`, `registrar_historial_usuario`, manejo de `QMessageBox` en cada acción). **Ojo:** ese proyecto arma las pantallas con posición absoluta (`setGeometry` en el `.ui`) y sin capa de controlador separada — eso es exactamente lo que la cátedra pide evitar, así que se toma la idea de organización pero se corrige con layouts reales y separación en Modelo/Vista/Controlador.

Tomar ambos, mejorarlos y armar el proyecto nuevo a partir de esa base es intencional — no es necesario reinventar el login o el logger, sí adaptarlos a MySQL Workbench, a `pathlib`, a la estructura MVC y al dominio de restaurante.

## Estructura de carpetas — MVC

La cátedra pide explícitamente separar acceso a datos, controladores y diseño de interfaz. Se traduce en tres carpetas de primer nivel:

```
restaurante/
├── main.py                     # arranque: crea QApplication, carga style.css, muestra login
├── config.ini                  # credenciales MySQL locales (NO se sube a git)
├── config.ini.example          # plantilla sin datos reales, sí se sube
├── requirements.txt
├── analisis/                   # este análisis + schema.sql + DER
├── recursos/
│   ├── style.css                # hoja de estilos global (ver sección Estilos)
│   └── img/                      # logo, iconos, imágenes de menú (gestionado con pathlib)
├── modelo/                       # M: acceso a datos, una función = una operación en la BD
│   ├── conexion.py                # config_db() + apertura/cierre de conexión MySQL
│   ├── usuario_modelo.py
│   ├── historial_modelo.py
│   ├── cliente_modelo.py
│   ├── reserva_modelo.py
│   ├── mesa_modelo.py
│   ├── grupo_mesa_modelo.py
│   ├── menu_modelo.py
│   ├── grupo_menu_modelo.py
│   ├── precio_menu_modelo.py
│   └── consumo_modelo.py
├── vista/                         # V: archivos .ui (Qt Designer) + clases de ventana
│   ├── login.ui / login_ventana.py
│   ├── principal.ui / principal_ventana.py
│   ├── usuarios/ (usuarios.ui, usuario_form.ui, usuarios_ventana.py)
│   ├── clientes/
│   ├── reservas/
│   ├── mesas/
│   ├── menu/
│   ├── consumo/
│   └── estadisticas/
├── controlador/                    # C: valida, orquesta modelo + vista, registra historial
│   ├── login_controlador.py
│   ├── usuarios_controlador.py
│   ├── clientes_controlador.py
│   ├── reservas_controlador.py
│   ├── mesas_controlador.py
│   ├── menu_controlador.py
│   ├── consumo_controlador.py
│   └── estadisticas_controlador.py
├── utilidades/                      # helpers transversales (no son "modelo" ni "vista")
│   ├── logger.py
│   ├── sesion.py                     # UserSession, adaptado de sistema_ejemplo
│   ├── seguridad.py                   # hash y verificación con bcrypt
│   └── validaciones.py                # validadores reutilizables (DNI, email, fechas, etc.)
└── logs/
```

**Responsabilidad de cada capa (para que quede claro en la defensa oral):**
- **Vista:** solo UI. Carga el `.ui`, conecta señales de botones a métodos del controlador, y muestra lo que el controlador le devuelve (incluyendo `QMessageBox` de error/éxito). No hace `SELECT`/`INSERT` directamente.
- **Controlador:** recibe el pedido de la vista, valida datos, llama al modelo, registra la acción en el historial si corresponde, y devuelve un resultado (dato u error) a la vista.
- **Modelo:** solo SQL. Cada función hace una operación puntual (`crear_cliente(datos)`, `obtener_cliente_por_id(id)`, `listar_reservas_por_cliente(id)`, etc.) y devuelve datos planos (dict, tupla, lista), nunca widgets.

## Reglas duras (no negociables, las pide la cátedra)

1. **Multiplataforma real:** nunca escribir rutas con `/` o `\` a mano. Siempre `pathlib.Path`. El proyecto se corre en macOS (Gabriel) y Windows (Mijail).
2. **Layouts, nunca posición fija:** en todo `.ui` usar `QVBoxLayout`/`QHBoxLayout`/`QGridLayout`. Cero `setGeometry` para armar pantallas (a diferencia del proyecto de Leandro, que sí lo usa — no copiar esa parte).
3. **Config externa:** host/user/password/port de MySQL viven en `config.ini` (no versionado). `config.ini.example` sí se versiona, sin credenciales reales.
4. **Contraseñas con hash:** `bcrypt`, nunca texto plano, ni en la base ni en logs.
5. **Widget correcto por tipo de dato:** `QDoubleSpinBox` para precios, `QDateEdit`/`QCalendarWidget` para fechas, `QTimeEdit` para horas, `QComboBox` para estados/grupos/roles, `QSpinBox` para enteros. Prohibido `QLineEdit` para eso.
6. **Fuente mínima 11pt**, formularios alineados, mismo estilo visual en todas las pantallas (ver `recursos/style.css`).
7. **`try/except` alrededor de toda consulta SQL y toda carga de archivo/imagen.** El programa no debe crashear nunca durante la demo. Mostrar el error al usuario con `QMessageBox`.
8. **Validación de formularios:** todo campo se valida antes de guardar; error inválido se muestra visualmente, nunca solo en consola.
9. **Los archivos `.ui` tienen que ser reales**, abribles y editables desde Qt Designer sin advertencias ni corrupción — ver sección siguiente.

## Archivos .ui — tienen que abrir bien en Qt Designer

Gabriel va a abrir estos `.ui` en Qt Designer para retocarlos a mano como parte del trabajo (edición de textos, ajustes visuales). Por eso:

- Generar XML válido de Qt Designer (`<ui version="4.0">`), con la misma estructura que ya usan `sistema_ejemplo/ui/*.ui` y `Practicas Leandro/.../ui/*.ui` como referencia de formato.
- Usar siempre `layout` (`QVBoxLayout`, `QHBoxLayout`, `QGridLayout`) como contenedor de los widgets — nunca dejar los widgets sueltos con `geometry` fija.
- **Nombres de objetos (`objectName`) en español**, siguiendo la convención que ya trae `sistema_ejemplo` (nombre de la clase del widget + guion bajo + descripción corta): `lineEdit_nombre`, `lineEdit_dni`, `pushButton_guardar`, `pushButton_cancelar`, `label_error_dni`, `comboBox_grupo`, `dateEdit_nacimiento`, `doubleSpinBox_precio`, `tableWidget_clientes`. Es la convención que Qt Designer sugiere por defecto al arrastrar un widget, así que es exactamente lo que un alumno produciría a mano.
- Textos visibles de botones, labels y placeholders siempre en español neutro/rioplatense simple: "Guardar", "Cancelar", "Eliminar", "Nuevo cliente", "Buscar por DNI", etc.
- No usar `<connections>` autogeneradas con nombres genéricos tipo `on_pushButton_clicked` — la conexión de señales se hace a mano en la clase de la vista (`self.pushButton_guardar.clicked.connect(self.controlador.guardar_cliente)`), como ya hace `sistema_ejemplo`.

## Estilos — `recursos/style.css`

Como enseñó el profesor: **una sola hoja de estilos (QSS) para todo el sistema**, no estilos sueltos por ventana.

- El archivo vive en `recursos/style.css` (se sigue llamando `.css` aunque la sintaxis sea Qt Style Sheets, que es lo que el profesor mostró en clase).
- Se carga una sola vez en `main.py`:
  ```python
  ruta_estilo = Path(__file__).resolve().parent / "recursos" / "style.css"
  app.setStyleSheet(ruta_estilo.read_text(encoding="utf-8"))
  ```
- Los selectores apuntan a clases de widget y, cuando hace falta algo puntual, al `objectName` (ej. `QPushButton#pushButton_eliminar { background-color: ... }`).
- Esto es lo que garantiza la "consistencia de diseño en todas las ventanas" que pide la cátedra, sin repetir `setStyleSheet(...)` en cada ventana.
- Paleta y tipografía: definir 3-4 colores (fondo, acento, texto, error) y una sola familia tipográfica, tamaño base 11pt, antes de tocar el primer `.ui` — así los 7 módulos salen iguales sin coordinar cada detalle a mano.

## Convenciones de código

- Nombres de variables, funciones, clases y módulos en **español**, sin excepción. Ej: `crear_cliente`, `validar_dni`, `obtener_reservas_por_cliente`. Nada de inglés ("create_client", "get_data", etc.) — es una de las señales más obvias de que algo no lo escribió un alumno.
- Comentarios breves explicando el *por qué*, no el *qué* (`# se guarda el precio ya calculado para no depender de cambios futuros en el grupo`, no `# esto guarda el precio`).
- Nada de docstrings exhaustivos tipo Google/NumPy en cada función chica — un comentario de una línea alcanza.
- No sobre-diseñar: nada de Repository/Factory/Dependency Injection genéricos. El nivel esperado es el de dos alumnos de Prácticas II, con una separación Modelo/Vista/Controlador simple y directa.
- Manejo de errores específico y con mensaje útil, no `except Exception: pass`.
- Evitar bloques de código idénticos copiados entre módulos — extraer a `utilidades/` cuando se repite (ej. `registrar_accion`, `config_db`, validadores comunes).

## Por qué importa esto para la entrega

El profesor evalúa explícitamente "uso correcto del lenguaje de la materia" y pide que el alumno demuestre conocimiento del código y de la base de datos en la defensa oral. Código en inglés, sobre-comentado, con patrones que ninguno de los dos puede explicar, o con `.ui` que no abren bien en Designer, es un riesgo real en la mesa. La meta es que cualquiera de los dos pueda abrir cualquier archivo del proyecto — incluyendo el `.ui` en Qt Designer — y mostrar que lo hicieron ellos, partiendo de lo que dio el profesor.

## Stack y entorno

- Python 3.11+, PyQt5, `mysql-connector-python`, `bcrypt`.
- MySQL 8 vía MySQL Workbench, base `restaurante_db` (ver `analisis/schema.sql`).
- Sin frameworks web, sin ORM — acceso a datos con SQL directo y `mysql-connector-python`, es lo que se vio en la cátedra.

## División de trabajo (ver `PLAN_4_DIAS.md` para el detalle día a día)

- **Gabriel:** Usuarios, Historial de acciones, Clientes, Reservas → archivos correspondientes en `modelo/`, `vista/`, `controlador/`.
- **Mijail:** Mesas + Grupos de mesa, Menú + Grupos de menú + Historial de precios, Consumo, Estadísticas → idem.
- Archivos compartidos (`modelo/conexion.py`, `utilidades/*.py`, `main.py`, `recursos/style.css`, `analisis/schema.sql`) se definen en la Fase 0-1 (ver `PLAN_4_DIAS.md`) y después no se tocan sin avisar al otro.

## Entorno

Antes de programar, correr `analisis/SETUP_ENTORNO.md` en ambas máquinas y confirmar con `python verificar_entorno.py` (en la raíz del repo) que Python, PyQt5, `mysql-connector-python`, `bcrypt` y la conexión a `restaurante_db` funcionan. Ese script no es parte del sistema final, es solo un chequeo de entorno.
