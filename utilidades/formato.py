"""
Helpers de presentacion compartidos por varios modulos (Clientes, Reservas,
Consumo). Traducen los valores tecnicos de la base a texto lindo para la UI, en
un solo lugar para no repetir los mismos diccionarios en cada modulo.
"""

# Estados de asistencia en orden (etiqueta visible, clave en la base). Es la
# unica fuente: los combos de Reservas y del panel usan la lista, y las tablas
# la traducen con estado_asistencia(). Antes esta lista estaba repetida en cada
# formulario que arma el combo de estado.
ESTADOS_ASISTENCIA = [
    ("En espera", "en_espera"),
    ("Asistio", "asistio"),
    ("Tardanza", "tardanza"),
    ("Falto", "falto"),
]
_ESTADOS = {clave: etiqueta for etiqueta, clave in ESTADOS_ASISTENCIA}

# Duraciones de reserva (etiqueta visible, clave en la base). Misma idea: unica
# fuente para el combo del formulario y para mostrar la duracion en la tabla.
DURACIONES = [("2 horas", "2h"), ("3 horas", "3h")]
_DURACIONES = {clave: etiqueta for etiqueta, clave in DURACIONES}

_MEDIOS_PAGO = {
    "efectivo": "Efectivo",
    "transferencia": "Transferencia",
}


def estado_asistencia(clave):
    return _ESTADOS.get(clave, clave)


def duracion(clave):
    return _DURACIONES.get(clave, clave)


def medio_pago(clave):
    return _MEDIOS_PAGO.get(clave, clave)


def hora(valor):
    # MySQL devuelve las columnas TIME como timedelta; lo pasamos a "HH:MM".
    if valor is None:
        return ""
    total = int(valor.total_seconds())
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}"


def moneda(valor):
    # Importes con formato argentino: punto para los miles y coma para los
    # decimales ($ 37.900,00). Se hace en un solo lugar porque los precios se
    # muestran en Mesas, Menu, Reservas, Consumo y Estadisticas, y antes estaba
    # el mismo f-string repetido en cada pantalla.
    if valor is None:
        return "—"
    # se formatea al estilo ingles (1,234.56) y despues se dan vuelta los
    # separadores, que es la forma mas corta de no depender de locale (locale
    # varia entre la Mac y la maquina con Windows).
    texto = f"{float(valor):,.2f}"
    return "$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


# DAYNAME de MySQL viene en ingles; lo pasamos a espanol y damos el orden natural
# de la semana para poder ordenar las filas de estadisticas.
_DIAS = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miercoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sabado", "Sunday": "Domingo",
}
ORDEN_DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

_MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def dia_semana(nombre_ingles):
    return _DIAS.get(nombre_ingles, nombre_ingles)


def nombre_mes(numero):
    return _MESES[numero] if 1 <= numero <= 12 else str(numero)
