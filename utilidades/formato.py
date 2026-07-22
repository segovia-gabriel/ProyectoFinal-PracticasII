"""
Helpers de presentacion compartidos por varios modulos (Clientes, Reservas,
Consumo). Traducen los valores tecnicos de la base a texto lindo para la UI, en
un solo lugar para no repetir los mismos diccionarios en cada modulo.
"""

_ESTADOS = {
    "en_espera": "En espera",
    "asistio": "Asistió",
    "tardanza": "Tardanza",
    "falto": "Faltó",
}

_MEDIOS_PAGO = {
    "efectivo": "Efectivo",
    "transferencia": "Transferencia",
}


def estado_asistencia(clave):
    return _ESTADOS.get(clave, clave)


def medio_pago(clave):
    return _MEDIOS_PAGO.get(clave, clave)


def hora(valor):
    # MySQL devuelve las columnas TIME como timedelta; lo pasamos a "HH:MM".
    if valor is None:
        return ""
    total = int(valor.total_seconds())
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}"


# DAYNAME de MySQL viene en ingles; lo pasamos a espanol y damos el orden natural
# de la semana para poder ordenar las filas de estadisticas.
_DIAS = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo",
}
ORDEN_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

_MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def dia_semana(nombre_ingles):
    return _DIAS.get(nombre_ingles, nombre_ingles)


def nombre_mes(numero):
    return _MESES[numero] if 1 <= numero <= 12 else str(numero)
