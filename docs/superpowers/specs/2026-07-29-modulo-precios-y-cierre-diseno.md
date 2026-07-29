# Diseno — Modulo Precios, Notificaciones y Cierre de mesas

Fecha: 2026-07-29
Autor: Gabriel

## Contexto

Ajustes al modulo de precios del menu y al panel de Inicio, mas el cierre
automatico de mesas. Nace de 7 observaciones de Gabriel sobre la consigna del
profesor (precio de lista/especial, historial con variacion, aviso 10 dias antes
del vencimiento).

Estado actual relevante:
- `historial_precios_menu`: cada cambio de precio inserta una fila nueva
  (`fecha_inicio = hoy`, `fecha_fin = NULL`) y cierra la anterior. El vigente es
  el que arranco y no cerro.
- El precio especial hoy es **opcional y manual** (checkbox + valor + combo medio).
- El consumo ya resuelve el precio segun el medio de pago: usa `precio_especial`
  si `medio_pago_especial == medio_pago`, si no el de lista
  ([consumo_controlador.py:78](../../../controlador/consumo_controlador.py)).
- El panel de Inicio ("Pendientes") mezcla dos avisos: precios por vencer y
  reservas asistidas sin consumo.

## Objetivos (los 7 puntos)

### 1. Precio especial automatico
Cargar **solo el precio de lista**. El especial se calcula solo.

- `precio_lista` = precio para transferencia (y cualquier medio = efectivo).
- Efectivo = `precio_lista × (1 − DESCUENTO_EFECTIVO)`, guardado como
  `precio_especial` con `medio_pago_especial = 'efectivo'`.
- `DESCUENTO_EFECTIVO = 0.10` como constante en `menu_controlador`, un solo lugar.
- No se toca el modulo Consumo: al cobrar en efectivo, el −10% ya se aplica solo.

Form (`precio_form`): se quitan checkbox especial, spin del especial y combo de
medio. Queda: precio de lista + fecha de fin opcional.

### 2. "Pendientes" → "Notificaciones"
Renombrar el subtitulo del panel de Inicio. Solo texto
([principal_ventana.py:157](../../../vista/principal_ventana.py) y :165, y el `.ui`).

### 3. Que falta de la consigna
La consigna se cumple casi entera. Huecos a cubrir con este diseno:
- No se puede corregir un precio mal cargado (punto 4).
- El especial pasa a estar atado al medio de pago de forma automatica (punto 1).
Todo lo demas (fecha inicio/fin, aviso 10 dias antes, historial con variacion
porcentual) ya esta implementado y se conserva.

### 4. Editar el precio vigente
Boton **"Editar vigente"** en la ventana de Precios. Abre el form precargado con
el precio actual y actualiza esa misma fila (no inserta una nueva). Al guardar se
recalculan el especial y la variacion. No se permite eliminar (decision de Gabriel).

### 5. Bug: precio renovado sigue en Notificaciones
Causa raiz en `crear_precio` ([precio_menu_modelo.py:87](../../../modelo/precio_menu_modelo.py)):
el `UPDATE` que cierra el precio viejo filtra por `fecha_fin IS NULL`, pero un
precio *por vencer* tiene `fecha_fin` puesta, asi que no se cierra y queda pisado
con el nuevo → sigue matcheando la query de notificaciones.

Fix: cerrar el precio **activo real**, no solo el indefinido:
```sql
UPDATE historial_precios_menu SET fecha_fin = %s
WHERE menu_item_id = %s AND (fecha_fin IS NULL OR fecha_fin >= %s)
```
donde el segundo `%s` es la `fecha_inicio` del nuevo precio.

### 6. Sacar boton "Actualizar"
El panel ya se recarga en `showEvent`, al volver a Inicio y tras cada accion. Se
quita `pushButton_actualizar`. Se verifica que cada modulo recargue su tabla
despues de guardar (la mayoria ya lo hace; se corrige el que no). No se agrega un
event-bus global (seria sobre-diseno para el nivel del proyecto).

### 7. Cierre automatico de mesas
Dos mecanismos que comparten la misma logica, parametrizada por fecha limite:

- **Barrido al iniciar sesion**: cierra lo que quedo de dias **anteriores**.
- **Boton "Cerrar dia"** (ocupa el lugar del viejo "Actualizar" en el panel):
  cierra el dia actual (incluye hoy).

Que hace el cierre para una fecha limite dada:
1. **Mesas abiertas con items** (`consumos.estado = 'abierta'` y `precio_total > 0`)
   → pasan a `'cerrada'` (cuentan como venta).
2. **Mesas abiertas vacias** (`precio_total = 0`, sin detalle) → se descartan
   (DELETE del consumo). Se abrieron por error y no representan una venta.
3. **Reservas asistidas sin consumo** (`estado_asistencia IN ('asistio','tardanza')`,
   sin fila en `consumos`) → se marcan como vencidas (`consumo_vencido = 1`) y
   desaparecen de las notificaciones. Decision de Gabriel: "vencerlas al cerrar el dia".

## Cambio de esquema

Nueva columna en `reservas`:
```sql
ALTER TABLE reservas
    ADD COLUMN consumo_vencido TINYINT(1) NOT NULL DEFAULT 0;
```
Marca las reservas cuyo consumo nunca se cargo y el dia ya cerro. Se agrega a
`analisis/schema.sql` y se crea `analisis/migracion_consumo_vencido.sql`
(mismo patron que `migracion_consumo_estado.sql`).

La query de notificaciones (`panel_modelo.reservas_cumplidas_sin_consumo`) y el
combo de Nuevo consumo suman `AND r.consumo_vencido = 0`, para que lo vencido no
se pueda cargar ni aparezca como pendiente.

## Archivos afectados

**Modelo**
- `precio_menu_modelo.py`: fix `crear_precio`; nuevo `actualizar_vigente(precio_id, precio_lista, precio_especial, fecha_fin)`.
- `consumo_modelo.py`: `cerrar_abiertas_con_items(fecha_limite)`, `eliminar_abiertas_vacias(fecha_limite)`.
- `reserva_modelo.py`: `vencer_consumos_pendientes(fecha_limite)`.
- `panel_modelo.py`: filtro `consumo_vencido = 0` en `reservas_cumplidas_sin_consumo`.

**Controlador**
- `menu_controlador.py`: constante `DESCUENTO_EFECTIVO`; simplificar `guardar_precio(item_id, precio_lista, fecha_fin=None)`; nuevo `editar_precio_vigente(item_id, precio_lista, fecha_fin=None)`.
- `cierre_controlador.py` (nuevo): `cerrar_dia()` (incluye hoy) y `barrido_inicial()` (solo dias anteriores). Orquesta consumo + reservas y registra la accion en el historial.
- `consumo_controlador.py`: sumar `AND r.consumo_vencido = 0` en el combo de reservas sin consumo (si aplica).

**Vista**
- `precio_form.ui` + `precio_form_ventana.py`: quitar campos del especial; soportar modo edicion (precargado).
- `precios.ui` + `precios_ventana.py`: boton "Editar vigente"; columna medio siempre "Efectivo".
- `principal.ui` + `principal_ventana.py`: "Pendientes" → "Notificaciones"; quitar `pushButton_actualizar`, agregar `pushButton_cerrarDia`; llamar `barrido_inicial()` una vez al abrir la ventana; recargar panel tras "Cerrar dia".

## Consideraciones

- **Multiplataforma**: sin rutas a mano, todo con `pathlib` (ya se cumple).
- **try/except** alrededor de cada consulta SQL (patron ya vigente en los modelos).
- **Historial intacto**: `crear_precio` sigue sin editar filas viejas; solo
  `editar_precio_vigente` toca la fila vigente (la ultima), sin romper la cadena.
- **Registro de acciones**: cada cierre de dia y cada edicion de precio se
  registran en `historial_acciones` con el usuario de la sesion.
- **Nivel del proyecto**: sin patrones genericos (Repository/Factory/event-bus).
  Separacion Modelo/Vista/Controlador directa, nombres y comentarios en espanol.

## Fuera de alcance

- No se redisena la UI del modulo de precios mas alla de los campos indicados.
- No se agrega historial de precios editable fila por fila (solo el vigente).
- No se cambia como Consumo resuelve el precio (ya funciona con el especial).
