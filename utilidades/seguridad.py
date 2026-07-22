"""
Hash y verificacion de contrasenas con bcrypt.
La base guarda solo el hash (columna contrasena_hash), nunca el texto plano.
Se centraliza aca para que ningun modulo llame directo a bcrypt y todos usen
el mismo criterio.
"""

import bcrypt


def hashear_contrasena(contrasena):
    # bcrypt trabaja con bytes; devolvemos texto para guardarlo en un VARCHAR.
    # El salt se genera adentro de hashpw, no hace falta guardarlo aparte.
    hash_bytes = bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_contrasena(contrasena, hash_guardado):
    # Compara la contrasena tipeada contra el hash de la base. bcrypt vuelve a
    # aplicar el salt que viene dentro del propio hash, por eso alcanza con esto.
    return bcrypt.checkpw(contrasena.encode("utf-8"), hash_guardado.encode("utf-8"))
