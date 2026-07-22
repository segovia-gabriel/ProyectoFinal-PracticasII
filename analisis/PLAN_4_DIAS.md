# Plan de desarrollo — fases y reparto

**No está organizado por día.** El orden de abajo es de dependencia (qué necesita a qué), no de tiempo — la idea es avanzar todo lo rápido que se pueda, aunque termine siendo 1-2 días en vez de 4. No hay que "llenar" cuatro días.

Contexto: Gabriel y Mijail trabajan juntos, en el mismo lugar, cada uno programando en su propia sesión de Claude Code. Todo se sube a git; Mijail lo baja en su Windows. MySQL Workbench en ambas máquinas, cada uno con su propia base local (usar `config.ini`, nunca hardcodear credenciales).

## Estructura de repo propuesta (MVC)

Ver el detalle completo y el porqué de cada capa en `CLAUDE.md`. Resumen:

```
restaurante/
├── main.py                    # arranque de la app, carga style.css, muestra login
├── config.ini                 # credenciales MySQL locales (NO se sube a git, va en .gitignore)
├── config.ini.example         # plantilla sin credenciales reales, sí se sube
├── requirements.txt
├── analisis/                  # este análisis + schema.sql + DER
├── recursos/
│   ├── style.css               # hoja de estilos global (QSS), un solo archivo para todo el sistema
│   └── img/                     # logo, iconos, imágenes de menú, gestionado con pathlib
├── modelo/                     # M: una función = una operación SQL, sin PyQt adentro
├── vista/                      # V: .ui (Qt Designer) + clases de ventana, sin SQL adentro
├── controlador/                # C: valida, llama al modelo, registra historial
├── utilidades/
│   ├── logger.py
│   ├── sesion.py                # UserSession, adaptado de sistema_ejemplo
│   ├── seguridad.py              # hash/verificación de contraseñas (bcrypt)
│   └── validaciones.py           # validadores reutilizables (DNI, email, fechas...)
└── logs/
```

Se parte de `sistema_ejemplo/` (login, `config_db()`, logger, `UserSession`) y de la organización de `Practicas Leandro/` como referencia, adaptando todo a esta estructura de tres capas y corrigiendo lo que la cátedra pide evitar (posición absoluta en los `.ui`).

## Reparto de módulos (para trabajar en paralelo sin pisarse)

**Gabriel:** Usuarios, Historial de acciones, Clientes, Reservas.
**Mijail:** Mesas + Grupos de mesa, Menú + Grupos de menú + Historial de precios, Consumo, Estadísticas.

Motivo del corte: Gabriel se queda con el circuito "usuario administra el sistema y a sus clientes", Mijail con el circuito "catálogo del restaurante y lo que se vende". Los únicos puntos de contacto entre ambos son `reservas` (Gabriel) y `mesas`/`menu_items` (Mijail) — se resuelven definiendo la estructura de esas tablas en la Fase 0 y no tocándola después sin avisar.

Dentro de `modelo/`, `vista/` y `controlador/` cada uno toca solo los archivos de sus módulos (ej. Gabriel: `modelo/cliente_modelo.py`, `vista/clientes/*`, `controlador/clientes_controlador.py`; Mijail: `modelo/menu_modelo.py`, `vista/menu/*`, `controlador/menu_controlador.py`), así que compartir las carpetas de primer nivel no genera conflictos de archivo.

**Archivos compartidos (se definen en la Fase 0-1 y después no se tocan sin avisar):**
`analisis/schema.sql`, `modelo/conexion.py`, `utilidades/logger.py`, `utilidades/sesion.py`, `utilidades/seguridad.py`, `recursos/style.css`, `main.py`, `config.ini.example`.

## Flujo de git recomendado

- Rama `main` siempre funcional (se prueba antes de mergear).
- Cada uno trabaja en su propia rama: `gabriel/usuarios`, `gabriel/clientes`, `mijail/mesas`, `mijail/menu`, etc. — una rama corta por módulo, no una rama gigante por persona.
- Commits chicos y frecuentes — dado que están en el mismo lugar, conviene mergear a `main` apenas un módulo compila y corre, para que el otro lo tenga disponible rápido.
- Antes de empezar un módulo nuevo: `git pull` sobre `main` para traer los cambios del otro.
- `.gitignore` debe incluir: `config.ini`, `__pycache__/`, `*.pyc`, `logs/*.log`, entorno virtual.

## Fases

### Fase 0 — Entorno (esto va primero, se hace una sola vez por máquina)
- Instalar Python, MySQL Server/Workbench y Qt Designer en ambas máquinas (ver `analisis/SETUP_ENTORNO.md`).
- Ejecutar `analisis/schema.sql` en MySQL Workbench en ambas máquinas y correr el script de verificación (`verificar_entorno.py`) para confirmar que Python, las librerías y la conexión a MySQL funcionan antes de escribir código de la app.

### Fase 1 — Base común y diseño
- Leer `sistema_ejemplo/` y `Practicas Leandro/` completos antes de escribir código nuevo.
- Armar estructura de carpetas MVC del repo, adaptando de `sistema_ejemplo`: `modelo/conexion.py` (a partir de `python_mysql_config.py`), `utilidades/logger.py`, `utilidades/sesion.py` (a partir de `UserSession`), `utilidades/seguridad.py` (bcrypt).
- Pantalla de login (`vista/login.ui` + `vista/login_ventana.py` + `controlador/login_controlador.py`) + ventana principal con navegación a los módulos (aunque estén vacíos).
- Definir el sistema de diseño en `recursos/style.css`: paleta de colores, tipografía (mínimo 11pt), estilo de botones — un solo archivo para que los 8 módulos se vean consistentes.
- Punto de control: login funcionando contra la base real, con el estilo global aplicado, y la ventana principal navegando a módulos placeholder.

### Fase 2 — Módulos core (en paralelo)
- Gabriel: Usuarios (CRUD completo) + Historial de acciones (listado + filtros).
- Mijail: Mesas + Grupos de mesa (CRUD completo de ambos).
- Merge cruzado apenas cada uno termina, para detectar conflictos temprano.
- Punto de control: ambos módulos funcionando de punta a punta contra la base.

### Fase 3 — Módulos de negocio (en paralelo)
- Gabriel: Clientes (CRUD + validación de baja + vista de reservas del cliente) y Reservas (CRUD + cálculo de precio + estado de asistencia + bloqueo de reservas pasadas).
- Mijail: Menú + Grupos de menú (CRUD + imagen) y precios (historial + variación porcentual + aviso de renovación a 10 días) y Consumo (alta de consumo con cálculo de precio final).
- Punto de control: los 7 módulos funcionales existen, aunque falten filtros y estadísticas.

### Fase 4 — Estadísticas, pulido y ensayo de defensa
- Estadísticas (clientes, reservas, consumo por día de semana) + filtros transversales en todos los listados (nombre, código, rango de fechas).
- Pasada de errores: probar cada módulo con datos inválidos, revisar que todos los `try/except` muestren `QMessageBox` claro, chequear tamaños de fuente y alineación de formularios.
- Preparar entrega: imprimir el DER (se puede generar el diagrama desde MySQL Workbench: Database → Reverse Engineer), armar el ZIP `apellido_nombre-practicas_II.zip` con archivos .ui, .py y el .sql, y ensayar la demo de 20 minutos repartiendo qué módulo explica cada uno.

## Antes de la mesa final

- Imprimir el diagrama de Modelo Relacional generado en MySQL Workbench (legible).
- Llevar la consigna impresa.
- Probar el sistema instalado en la máquina que van a usar en la mesa (no confiar en "anda en mi máquina").
- Repasar el "por qué" de cada decisión de diseño (snapshots de precio en reservas/consumo, hash de contraseñas, historial de precios) porque el tribunal pregunta sobre el proceso de desarrollo, no solo el resultado.
