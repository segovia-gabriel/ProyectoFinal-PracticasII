
ESTADOS_ASISTENCIA = [
    ("En espera", "en_espera"),
    ("Asistio", "asistio"),
    ("Tardanza", "tardanza"),
    ("Falto", "falto"),
]
_ESTADOS = {clave: etiqueta for etiqueta, clave in ESTADOS_ASISTENCIA}

# Lo mismo para las duraciones de reserva (etiqueta visible, clave en la base).
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
    # MySQL me devuelve las columnas TIME como timedelta, asi que lo paso a "HH:MM".
    if valor is None:
        return ""
    total = int(valor.total_seconds())
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}"


def moneda(valor):
    # Formato argentino: punto para los miles y coma para los decimales ($ 37.900,00).
    if valor is None:
        return "—"
    # Lo formateo al estilo ingles (1,234.56) y despues doy vuelta los separadores.
    # Asi no dependo del locale, que cambia de una maquina a otra.
    texto = f"{float(valor):,.2f}"
    return "$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


# El DAYNAME de MySQL viene en ingles: lo traduzco y fijo el orden de la semana
# para poder ordenar las filas en estadisticas.
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
