# Plan de desarrollo — fases y reparto

**No esta organizado por dia.** El orden de abajo es de dependencia (que necesita a que), no de tiempo — la idea es avanzar todo lo rapido que se pueda, aunque termine siendo 1-2 dias en vez de 4. No hay que "llenar" cuatro dias.

Contexto: Gabriel y Mijail trabajan juntos, en el mismo lugar, cada uno programando en su propia sesion de Claude Code. Todo se sube a git; Mijail lo baja en su Windows. MySQL Workbench en ambas maquinas, cada uno con su propia base local (usar `config.ini`, nunca hardcodear credenciales).

## Estructura de repo propuesta (MVC)

Ver el detalle completo y el porque de cada capa en `CLAUDE.md`. Resumen:

```
restaurante/
├── main.py                    # arranque de la app, carga style.css, muestra login
├── config.ini                 # credenciales MySQL locales (NO se sube a git, va en .gitignore)
├── config.ini.example         # plantilla sin credenciales reales, si se sube
├── requirements.txt
├── analisis/                  # este analisis + schema.sql + DER
├── recursos/
│   ├── style.css               # hoja de estilos global (QSS), un solo archivo para todo el sistema
│   └── img/                     # logo, iconos, imagenes de menu, gestionado con pathlib
├── modelo/                     # M: una funcion = una operacion SQL, sin PyQt adentro
├── vista/                      # V: .ui (Qt Designer) + clases de ventana, sin SQL adentro
├── controlador/                # C: valida, llama al modelo, registra historial
├── utilidades/
│   ├── logger.py
│   ├── sesion.py                # UserSession, adaptado de sistema_ejemplo
│   ├── seguridad.py              # hash/verificacion de contrasenas (bcrypt)
│   └── validaciones.py           # validadores reutilizables (DNI, email, fechas...)
└── logs/
```

Se parte de `sistema_ejemplo/` (login, `config_db()`, logger, `UserSession`) y de la organizacion de `Practicas Leandro/` como referencia, adaptando todo a esta estructura de tres capas y corrigiendo lo que la catedra pide evitar (posicion absoluta en los `.ui`).

## Reparto de modulos (para trabajar en paralelo sin pisarse)

**Gabriel:** Usuarios, Historial de acciones, Clientes, Reservas.
**Mijail:** Mesas + Grupos de mesa, Menu + Grupos de menu + Historial de precios, Consumo, Estadisticas.

Motivo del corte: Gabriel se queda con el circuito "usuario administra el sistema y a sus clientes", Mijail con el circuito "catalogo del restaurante y lo que se vende". Los unicos puntos de contacto entre ambos son `reservas` (Gabriel) y `mesas`/`menu_items` (Mijail) — se resuelven definiendo la estructura de esas tablas en la Fase 0 y no tocandola despues sin avisar.

Dentro de `modelo/`, `vista/` y `controlador/` cada uno toca solo los archivos de sus modulos (ej. Gabriel: `modelo/cliente_modelo.py`, `vista/clientes/*`, `controlador/clientes_controlador.py`; Mijail: `modelo/menu_modelo.py`, `vista/menu/*`, `controlador/menu_controlador.py`), asi que compartir las carpetas de primer nivel no genera conflictos de archivo.

**Archivos compartidos (se definen en la Fase 0-1 y despues no se tocan sin avisar):**
`analisis/schema.sql`, `modelo/conexion.py`, `utilidades/logger.py`, `utilidades/sesion.py`, `utilidades/seguridad.py`, `recursos/style.css`, `main.py`, `config.ini.example`.

## Flujo de git recomendado

- Rama `main` siempre funcional (se prueba antes de mergear).
- Cada uno trabaja en su propia rama: `gabriel/usuarios`, `gabriel/clientes`, `mijail/mesas`, `mijail/menu`, etc. — una rama corta por modulo, no una rama gigante por persona.
- Commits chicos y frecuentes — dado que estan en el mismo lugar, conviene mergear a `main` apenas un modulo compila y corre, para que el otro lo tenga disponible rapido.
- Antes de empezar un modulo nuevo: `git pull` sobre `main` para traer los cambios del otro.
- `.gitignore` debe incluir: `config.ini`, `__pycache__/`, `*.pyc`, `logs/*.log`, entorno virtual.

## Fases

### Fase 0 — Entorno (esto va primero, se hace una sola vez por maquina)
- Instalar Python, MySQL Server/Workbench y Qt Designer en ambas maquinas (ver `analisis/SETUP_ENTORNO.md`).
- Ejecutar `analisis/schema.sql` en MySQL Workbench en ambas maquinas y correr el script de verificacion (`verificar_entorno.py`) para confirmar que Python, las librerias y la conexion a MySQL funcionan antes de escribir codigo de la app.

### Fase 1 — Base comun y diseno
- Leer `sistema_ejemplo/` y `Practicas Leandro/` completos antes de escribir codigo nuevo.
- Armar estructura de carpetas MVC del repo, adaptando de `sistema_ejemplo`: `modelo/conexion.py` (a partir de `python_mysql_config.py`), `utilidades/logger.py`, `utilidades/sesion.py` (a partir de `UserSession`), `utilidades/seguridad.py` (bcrypt).
- Pantalla de login (`vista/login.ui` + `vista/login_ventana.py` + `controlador/login_controlador.py`) + ventana principal con navegacion a los modulos (aunque esten vacios).
- Definir el sistema de diseno en `recursos/style.css`: paleta de colores, tipografia (minimo 11pt), estilo de botones — un solo archivo para que los 8 modulos se vean consistentes.
- Punto de control: login funcionando contra la base real, con el estilo global aplicado, y la ventana principal navegando a modulos placeholder.

### Fase 2 — Modulos core (en paralelo)
- Gabriel: Usuarios (CRUD completo) + Historial de acciones (listado + filtros).
- Mijail: Mesas + Grupos de mesa (CRUD completo de ambos).
- Merge cruzado apenas cada uno termina, para detectar conflictos temprano.
- Punto de control: ambos modulos funcionando de punta a punta contra la base.

### Fase 3 — Modulos de negocio (en paralelo)
- Gabriel: Clientes (CRUD + validacion de baja + vista de reservas del cliente) y Reservas (CRUD + calculo de precio + estado de asistencia + bloqueo de reservas pasadas).
- Mijail: Menu + Grupos de menu (CRUD + imagen) y precios (historial + variacion porcentual + aviso de renovacion a 10 dias) y Consumo (alta de consumo con calculo de precio final).
- Punto de control: los 7 modulos funcionales existen, aunque falten filtros y estadisticas.

### Fase 4 — Estadisticas, pulido y ensayo de defensa
- Estadisticas (clientes, reservas, consumo por dia de semana) + filtros transversales en todos los listados (nombre, codigo, rango de fechas).
- Pasada de errores: probar cada modulo con datos invalidos, revisar que todos los `try/except` muestren `QMessageBox` claro, chequear tamanos de fuente y alineacion de formularios.
- Preparar entrega: imprimir el DER (se puede generar el diagrama desde MySQL Workbench: Database → Reverse Engineer), armar el ZIP `apellido_nombre-practicas_II.zip` con archivos .ui, .py y el .sql, y ensayar la demo de 20 minutos repartiendo que modulo explica cada uno.

## Antes de la mesa final

- Imprimir el diagrama de Modelo Relacional generado en MySQL Workbench (legible).
- Llevar la consigna impresa.
- Probar el sistema instalado en la maquina que van a usar en la mesa (no confiar en "anda en mi maquina").
- Repasar el "por que" de cada decision de diseno (snapshots de precio en reservas/consumo, hash de contrasenas, historial de precios) porque el tribunal pregunta sobre el proceso de desarrollo, no solo el resultado.
