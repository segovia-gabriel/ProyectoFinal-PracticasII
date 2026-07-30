"""
Hash y verificacion de contrasenas con bcrypt.
En la base solo va el hash (columna contrasena_hash), nunca el texto plano.
Lo centralizo aca para que ningun modulo llame a bcrypt por su cuenta y todos
usen el mismo criterio.
"""

import bcrypt


def hashear_contrasena(contrasena):
    # bcrypt labura con bytes, asi que devuelvo texto para meterlo en un VARCHAR.
    # El salt se genera solo adentro de hashpw, no lo tengo que guardar aparte.
    hash_bytes = bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_contrasena(contrasena, hash_guardado):
    # Compara lo que tipeo el usuario contra el hash de la base. bcrypt saca el
    # salt del propio hash y lo vuelve a aplicar, por eso con esto alcanza.
    return bcrypt.checkpw(contrasena.encode("utf-8"), hash_guardado.encode("utf-8"))
