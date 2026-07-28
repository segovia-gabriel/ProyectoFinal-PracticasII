"""
Validadores reutilizables por varios modulos. Cada uno devuelve una tupla
(valido, mensaje): si valido es False, mensaje explica que corregir para
mostrarlo en pantalla. Se hacen con chequeos simples (len, isupper, isdigit)
en vez de expresiones regulares para poder explicarlos en la defensa.

Por ahora estan los de Usuarios; los de Clientes (DNI, telefono, fechas) se
agregan cuando se programe ese modulo, sin borrar estos.
"""


def validar_nombre_usuario(nombre):
    # Debe existir la persona en el sistema con un nombre corto y sin espacios,
    # porque se usa para loguear.
    if not nombre:
        return False, "El nombre de usuario no puede estar vacío."
    if " " in nombre:
        return False, "El nombre de usuario no puede tener espacios."
    if len(nombre) < 4 or len(nombre) > 30:
        return False, "El nombre de usuario debe tener entre 4 y 30 caracteres."
    return True, ""


def validar_contrasena(contrasena):
    # Mismo criterio que ya usaba sistema_ejemplo: 8+ caracteres, con al menos
    # una mayuscula y un numero, para que no sea trivial de adivinar.
    if len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not any(c.isupper() for c in contrasena):
        return False, "La contraseña debe tener al menos una mayúscula."
    if not any(c.isdigit() for c in contrasena):
        return False, "La contraseña debe tener al menos un número."
    return True, ""


# ---------- Validadores de Clientes ----------

def validar_texto_obligatorio(valor, etiqueta):
    # Generico: no vacio y de largo razonable.
    valor = valor.strip()
    if not valor:
        return False, f"El campo {etiqueta} no puede estar vacío."
    if len(valor) > 50:
        return False, f"El campo {etiqueta} es demasiado largo."
    return True, ""


def validar_nombre_persona(valor, etiqueta):
    # Nombre y apellido: obligatorios, sin numeros (un nombre no lleva digitos).
    valido, mensaje = validar_texto_obligatorio(valor, etiqueta)
    if not valido:
        return False, mensaje
    if any(c.isdigit() for c in valor):
        return False, f"El campo {etiqueta} no puede contener números."
    return True, ""


def validar_direccion(direccion):
    # La direccion tambien es obligatoria (ningun dato del cliente queda vacio).
    direccion = direccion.strip()
    if not direccion:
        return False, "La dirección no puede estar vacía."
    if len(direccion) > 150:
        return False, "La dirección es demasiado larga."
    return True, ""


def validar_dni(dni):
    # Argentina: solo numeros, 7 u 8 digitos.
    dni = dni.strip()
    if not dni.isdigit():
        return False, "El DNI debe contener solo números."
    if len(dni) < 7 or len(dni) > 8:
        return False, "El DNI debe tener 7 u 8 dígitos."
    return True, ""


def validar_telefono(telefono):
    # Obligatorio. Se aceptan numeros y separadores simples (-, +, espacio) y se
    # exige entre 6 y 20 digitos (formato telefonico razonable).
    telefono = telefono.strip()
    if not telefono:
        return False, "El teléfono no puede estar vacío."
    permitidos = "0123456789-+ "
    if any(c not in permitidos for c in telefono):
        return False, "El teléfono solo puede tener números, espacios, + o -."
    digitos = sum(1 for c in telefono if c.isdigit())
    if digitos < 6 or digitos > 20:
        return False, "El teléfono debe tener entre 6 y 20 dígitos."
    return True, ""


# ---------- Validador comun de filtros por rango de fechas ----------

def validar_rango_fechas(fecha_desde, fecha_hasta):
    # Usado por todos los listados con filtro Desde/Hasta: el "Desde" nunca puede
    # quedar despues del "Hasta".
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        return False, "La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'."
    return True, ""
