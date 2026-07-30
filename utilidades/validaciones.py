def validar_nombre_usuario(nombre):
    # Con esto se loguea, asi que lo quiero corto, sin espacios y que no venga vacio.
    if not nombre:
        return False, "El nombre de usuario no puede estar vacio."
    if " " in nombre:
        return False, "El nombre de usuario no puede tener espacios."
    if len(nombre) < 4 or len(nombre) > 30:
        return False, "El nombre de usuario debe tener entre 4 y 30 caracteres."
    return True, ""


def validar_contrasena(contrasena):
    # Minimo 8 caracteres, con una mayuscula y un numero, para que no sea facil de adivinar.
    if len(contrasena) < 8:
        return False, "La contrasena debe tener al menos 8 caracteres."
    if not any(c.isupper() for c in contrasena):
        return False, "La contrasena debe tener al menos una mayuscula."
    if not any(c.isdigit() for c in contrasena):
        return False, "La contrasena debe tener al menos un numero."
    return True, ""


# ---------- Validadores de Clientes ----------

def validar_texto_obligatorio(valor, etiqueta):
    # El generico: que no venga vacio y que no se pase de largo.
    valor = valor.strip()
    if not valor:
        return False, f"El campo {etiqueta} no puede estar vacio."
    if len(valor) > 50:
        return False, f"El campo {etiqueta} es demasiado largo."
    return True, ""


def validar_nombre_persona(valor, etiqueta):
    # Nombre y apellido: obligatorios y sin numeros, obvio que un nombre no lleva digitos.
    valido, mensaje = validar_texto_obligatorio(valor, etiqueta)
    if not valido:
        return False, mensaje
    if any(c.isdigit() for c in valor):
        return False, f"El campo {etiqueta} no puede contener numeros."
    return True, ""


def validar_direccion(direccion):
    # La direccion tambien va si o si, no dejo ningun dato del cliente vacio.
    direccion = direccion.strip()
    if not direccion:
        return False, "La direccion no puede estar vacia."
    if len(direccion) > 150:
        return False, "La direccion es demasiado larga."
    return True, ""


def validar_dni(dni):
    # DNI argentino: solo numeros, 7 u 8 digitos.
    dni = dni.strip()
    if not dni.isdigit():
        return False, "El DNI debe contener solo numeros."
    if len(dni) < 7 or len(dni) > 8:
        return False, "El DNI debe tener 7 u 8 digitos."
    return True, ""


def validar_telefono(telefono):
    # Obligatorio. Acepto numeros y separadores comunes (-, +, espacio), y pido
    # entre 6 y 20 digitos para que sea un telefono de verdad.
    telefono = telefono.strip()
    if not telefono:
        return False, "El telefono no puede estar vacio."
    permitidos = "0123456789-+ "
    if any(c not in permitidos for c in telefono):
        return False, "El telefono solo puede tener numeros, espacios, + o -."
    digitos = sum(1 for c in telefono if c.isdigit())
    if digitos < 6 or digitos > 20:
        return False, "El telefono debe tener entre 6 y 20 digitos."
    return True, ""


# ---------- Validador comun de filtros por rango de fechas ----------

def validar_rango_fechas(fecha_desde, fecha_hasta):
    # Lo usan todos los listados con filtro Desde/Hasta: el "Desde" nunca puede
    # quedar despues del "Hasta".
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        return False, "La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'."
    return True, ""
