"""
Controlador de Menu: items, grupos de menu y precios. Resuelve el precio vigente
de cada item, calcula la variacion porcentual del historial, avisa cuando un
precio esta por vencer, y copia la imagen elegida a la carpeta del proyecto.
"""

import shutil
from datetime import date, timedelta
from pathlib import Path

from mysql.connector import Error

from modelo import grupo_menu_modelo, menu_modelo, precio_menu_modelo
from modelo.historial_modelo import registrar_accion
from utilidades.logger import registrar
from utilidades.sesion import Sesion

# Raiz del proyecto, para resolver rutas de imagenes con pathlib (multiplataforma).
RAIZ = Path(__file__).resolve().parent.parent
DIAS_AVISO_RENOVACION = 10


class MenuControlador:

    # ---------------- Items ----------------

    def listar_items(self, filtro_nombre=None):
        try:
            items = menu_modelo.listar(filtro_nombre)
            # a cada item le agregamos su precio de lista vigente para mostrarlo
            for item in items:
                vigente = precio_menu_modelo.obtener_vigente(item["id"])
                item["precio_vigente"] = float(vigente["precio_lista"]) if vigente else None
            return True, items
        except Error:
            return False, "No se pudieron cargar los ítems del menú."

    def obtener_item(self, item_id):
        try:
            return True, menu_modelo.obtener_por_id(item_id)
        except Error:
            return False, "No se pudo obtener el ítem."

    def listar_grupos_combo(self):
        try:
            grupos = grupo_menu_modelo.listar()
            return True, [(g["id"], g["nombre"]) for g in grupos]
        except Error:
            return False, "No se pudieron cargar los grupos."

    def _copiar_imagen(self, origen):
        # Copia la imagen elegida a recursos/img/menu/ con un nombre unico y
        # devuelve la ruta relativa a guardar en la base. Si algo falla, avisa.
        try:
            origen = Path(origen)
            destino_dir = RAIZ / "recursos" / "img" / "menu"
            destino_dir.mkdir(parents=True, exist_ok=True)
            # se antepone un timestamp para no pisar imagenes de igual nombre
            marca = date.today().strftime("%Y%m%d") + "_" + str(abs(hash(origen.name)) % 100000)
            destino = destino_dir / f"{marca}_{origen.name}"
            shutil.copy(origen, destino)
            # ruta relativa con / (as_posix) para que sirva en Mac y Windows
            return (Path("recursos") / "img" / "menu" / destino.name).as_posix()
        except OSError as error:
            registrar(error, "error")
            return None

    def guardar_item(self, item_id, nombre, descripcion, grupo_menu_id, imagen_origen, imagen_actual):
        nombre = nombre.strip()
        if not nombre:
            return False, "El nombre del ítem no puede estar vacío."
        if grupo_menu_id is None:
            return False, "Seleccioná un grupo de menú."

        # imagen_origen: ruta nueva elegida por el usuario (o None si no cambio).
        # imagen_actual: la que ya tenia el item (se conserva si no eligio otra).
        imagen_path = imagen_actual
        if imagen_origen:
            copiada = self._copiar_imagen(imagen_origen)
            if copiada is None:
                return False, "No se pudo copiar la imagen elegida."
            imagen_path = copiada

        descripcion = descripcion.strip() or None
        try:
            if item_id is None:
                menu_modelo.crear(nombre, descripcion, imagen_path, grupo_menu_id)
                registrar_accion(Sesion().usuario_id, f"Creó ítem de menú: {nombre}")
                return True, "Ítem creado correctamente. Cargale un precio desde 'Precios'."
            else:
                menu_modelo.modificar(item_id, nombre, descripcion, imagen_path, grupo_menu_id)
                registrar_accion(Sesion().usuario_id, f"Modificó ítem de menú: {nombre}")
                return True, "Ítem modificado correctamente."
        except Error:
            return False, "No se pudo guardar el ítem."

    def eliminar_item(self, item_id):
        try:
            if menu_modelo.contar_consumos(item_id) > 0:
                return False, "No se puede eliminar el ítem porque ya fue consumido en ventas."
            item = menu_modelo.obtener_por_id(item_id)
            if item is None:
                return False, "El ítem ya no existe."
            # primero su historial de precios (clave foranea), despues el item
            precio_menu_modelo.eliminar_por_item(item_id)
            menu_modelo.eliminar(item_id)
            registrar_accion(Sesion().usuario_id, f"Eliminó ítem de menú: {item['nombre']}")
            return True, "Ítem eliminado correctamente."
        except Error:
            return False, "No se pudo eliminar el ítem."

    # ---------------- Grupos de menu ----------------

    def listar_grupos(self, filtro_nombre=None):
        try:
            return True, grupo_menu_modelo.listar(filtro_nombre)
        except Error:
            return False, "No se pudieron cargar los grupos."

    def obtener_grupo(self, grupo_id):
        try:
            return True, grupo_menu_modelo.obtener_por_id(grupo_id)
        except Error:
            return False, "No se pudo obtener el grupo."

    def guardar_grupo(self, grupo_id, nombre):
        nombre = nombre.strip()
        if not nombre:
            return False, "El nombre del grupo no puede estar vacío."
        try:
            if grupo_menu_modelo.existe_nombre(nombre, excluir_id=grupo_id):
                return False, "Ya existe un grupo con ese nombre."
        except Error:
            return False, "No se pudo verificar el nombre del grupo."
        try:
            if grupo_id is None:
                grupo_menu_modelo.crear(nombre)
                registrar_accion(Sesion().usuario_id, f"Creó grupo de menú: {nombre}")
                return True, "Grupo creado correctamente."
            else:
                grupo_menu_modelo.modificar(grupo_id, nombre)
                registrar_accion(Sesion().usuario_id, f"Modificó grupo de menú: {nombre}")
                return True, "Grupo modificado correctamente."
        except Error:
            return False, "No se pudo guardar el grupo."

    def eliminar_grupo(self, grupo_id):
        try:
            if grupo_menu_modelo.contar_items(grupo_id) > 0:
                return False, "No se puede eliminar el grupo porque tiene ítems asignados."
            grupo = grupo_menu_modelo.obtener_por_id(grupo_id)
            if grupo is None:
                return False, "El grupo ya no existe."
            grupo_menu_modelo.eliminar(grupo_id)
            registrar_accion(Sesion().usuario_id, f"Eliminó grupo de menú: {grupo['nombre']}")
            return True, "Grupo eliminado correctamente."
        except Error:
            return False, "No se pudo eliminar el grupo."

    # ---------------- Precios ----------------

    def historial_precios(self, item_id):
        # Devuelve el historial con la variacion porcentual respecto al precio
        # de lista anterior, calculada en Python al recorrer las filas.
        try:
            filas = precio_menu_modelo.listar_historial(item_id)
        except Error:
            return False, "No se pudo cargar el historial de precios."

        anterior = None
        for fila in filas:
            actual = float(fila["precio_lista"])
            if anterior is None or anterior == 0:
                fila["variacion"] = None   # el primer precio no tiene con que compararse
            else:
                fila["variacion"] = (actual - anterior) / anterior * 100
            anterior = actual
        return True, filas

    def aviso_renovacion(self, item_id):
        # Si el precio vigente tiene fecha_fin definida y faltan 10 dias o menos,
        # devuelve un texto de aviso; si no, None.
        try:
            vigente = precio_menu_modelo.obtener_vigente(item_id)
        except Error:
            return None
        if not vigente or vigente["fecha_fin"] is None:
            return None
        dias = (vigente["fecha_fin"] - date.today()).days
        if 0 <= dias <= DIAS_AVISO_RENOVACION:
            return f"El precio vigente vence en {dias} día(s) ({vigente['fecha_fin'].strftime('%d/%m/%Y')})."
        return None

    def guardar_precio(self, item_id, precio_lista, tiene_especial, precio_especial,
                       medio_pago_especial, fecha_fin=None):
        if precio_lista <= 0:
            return False, "El precio de lista debe ser mayor a cero."
        if tiene_especial:
            if precio_especial <= 0:
                return False, "El precio especial debe ser mayor a cero."
            if medio_pago_especial not in ("efectivo", "transferencia"):
                return False, "Elegí el medio de pago del precio especial."
        else:
            precio_especial = None
            medio_pago_especial = None

        # El precio arranca hoy; si se define un fin de vigencia, no puede quedar
        # antes de esa fecha de inicio.
        hoy = date.today()
        if fecha_fin is not None and fecha_fin < hoy:
            return False, "La fecha de fin de vigencia no puede ser anterior a hoy."

        try:
            precio_menu_modelo.crear_precio(
                item_id, precio_lista, precio_especial, medio_pago_especial, hoy, fecha_fin
            )
            item = menu_modelo.obtener_por_id(item_id)
            nombre = item["nombre"] if item else f"#{item_id}"
            registrar_accion(Sesion().usuario_id, f"Actualizó precio de ítem de menú: {nombre}")
            return True, "Precio actualizado correctamente."
        except Error:
            return False, "No se pudo guardar el precio."
