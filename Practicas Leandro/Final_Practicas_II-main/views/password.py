import hashlib
import os

def generar_password(password):
    """Genera un hash para la contraseña usando SHA-256 con una sal."""
    salt = os.urandom(16)  # Genera una sal aleatoria de 16 bytes
    password_salted = salt + password.encode('utf-8')  # Combina la sal con la contraseña
    hashed = hashlib.sha256(password_salted).hexdigest()  # Aplica SHA-256
    return salt.hex() + hashed  # Devuelve la sal + hash en formato hexadecimal

def verifica_password(password, stored_password):
    """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
    salt = bytes.fromhex(stored_password[:32])  # Extrae la sal (primeros 32 caracteres hexadecimales)
    stored_hash = stored_password[32:]  # Extrae el hash almacenado (resto de los caracteres)
    password_salted = salt + password.encode('utf-8')  # Combina la sal con la contraseña ingresada
    hashed_password = hashlib.sha256(password_salted).hexdigest()  # Aplica SHA-256
    return hashed_password == stored_hash  # Compara el hash generado con el almacenado


# # Crear el hash de una nueva contraseña
# hashed_password = generar_password('mi_secreta_password')
# print(f"Contraseña almacenada (hash): {hashed_password}")

# # Verificar si una contraseña es correcta
# is_valid = verifica_password('mi_secreta_password', hashed_password)
# print(f"¿La contraseña es válida? {is_valid}")