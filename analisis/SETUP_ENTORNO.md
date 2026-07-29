# Setup de entorno — Fase 0

Esto se hace una vez por maquina, antes de tocar codigo de la app. Objetivo: tener Python, MySQL y Qt Designer instalados, la base creada con `analisis/schema.sql`, y confirmarlo corriendo `verificar_entorno.py`.

---

## macOS (Gabriel — MacBook Air M4)

### 1. Homebrew (si no lo tenes)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python
macOS ya trae `python3`, pero conviene una version reciente via Homebrew para no depender de la del sistema:
```bash
brew install python@3.12
python3 --version
```

### 3. MySQL Server + Workbench
```bash
brew install mysql
brew services start mysql
brew install --cask mysqlworkbench
```
Definir la contrasena de `root` (Homebrew lo instala sin password por defecto):
```bash
mysql_secure_installation
```
Segui el asistente y pone una contrasena para `root` (anotala, va en `config.ini`).

### 4. Qt Designer
```bash
pip install pyqt5-tools
```
Si no hay wheel disponible para tu Mac (pasa en algunos Apple Silicon), alternativa:
```bash
brew install --cask qt-creator
```
Qt Creator incluye Designer integrado (Tools → Form Editor), o se puede abrir el `Design` binario suelto desde `Qt Creator.app/Contents/Resources`.

### 5. Entorno virtual del proyecto
Parado en la carpeta del proyecto:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Crear la base de datos
Abri MySQL Workbench → conectate a `localhost` con `root` y tu password → `File > Open SQL Script` → selecciona `analisis/schema.sql` → ejecuta con el rayo (⚡) o `Cmd + Shift + Enter`.

### 7. Configurar credenciales
```bash
cp config.ini.example config.ini
```
Edita `config.ini` y completa la password real de MySQL.

### 8. Verificar
```bash
python3 verificar_entorno.py
```
Tiene que mostrar las 11 tablas con su cantidad de filas (los datos de prueba que ya vienen en `schema.sql`).

---

## Windows (Mijail)

### 1. Python
Descargar el instalador desde https://www.python.org/downloads/ (3.8 o superior). Durante la instalacion, tildar **"Add python.exe to PATH"**.
```powershell
py --version
```
La consigna no exige una version puntual de Python. El proyecto esta probado sobre **3.8.10** en Windows y no usa sintaxis posterior a esa version.

### 2. MySQL (XAMPP)
En Windows el proyecto corre sobre el **MySQL/MariaDB que trae XAMPP**, que es lo que ya esta instalado en la maquina de la defensa. Descargarlo de https://www.apachefriends.org/ y, desde el *XAMPP Control Panel*, arrancar el modulo **MySQL**.

Por defecto XAMPP deja el usuario `root` **sin contrasena**, y eso es lo que va en `config.ini`. La base se administra desde phpMyAdmin (`http://localhost/phpmyadmin`) o desde la consola:
```powershell
C:\xampp\mysql\bin\mysql.exe -u root
```

Alternativa (si se prefiere MySQL Server "oficial" + Workbench): instalarlos con el **MySQL Installer for Windows** desde https://dev.mysql.com/downloads/installer/, eligiendo "Custom" y marcando MySQL Server y MySQL Workbench. En ese caso el instalador pide definir la contrasena de `root` y hay que ponerla en `config.ini`. El `schema.sql` funciona igual en los dos motores.

### 3. Qt Designer
```powershell
pip install pyqt5-tools
```
En Windows suele venir con wheels oficiales sin problema. El ejecutable de Designer queda accesible corriendo:
```powershell
pyqt5-tools designer
```

### 4. Entorno virtual del proyecto
Parado en la carpeta del proyecto (despues de bajarlo con `git pull`):
```powershell
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Crear la base de datos
Con el modulo MySQL de XAMPP arrancado, desde la carpeta del proyecto:
```powershell
C:\xampp\mysql\bin\mysql.exe -u root < analisis\schema.sql
```
El script empieza con `DROP DATABASE IF EXISTS restaurante_db`, asi que es seguro volver a correrlo cuantas veces haga falta (por ejemplo para dejar los datos de prueba limpios antes de la defensa).

Tambien se puede hacer desde phpMyAdmin → pestana **Importar** → elegir `analisis\schema.sql` → *Continuar*; o desde MySQL Workbench si se usa el MySQL oficial.

### 6. Configurar credenciales
```powershell
copy config.ini.example config.ini
```
Edita `config.ini` y completa la password real de MySQL. Con XAMPP por defecto `root` no tiene contrasena, asi que la linea queda `password =` (vacia).

### 7. Verificar
```powershell
python verificar_entorno.py
```
Mismo resultado esperado que en macOS: las 11 tablas con filas cargadas.

---

## Notas

- `config.ini` **no se sube a git** (cada uno tiene su propia password local). Solo se versiona `config.ini.example`.
- Si `verificar_entorno.py` dice que faltan tablas, es porque `schema.sql` no se ejecuto (o fallo a mitad de camino) — volver a correrlo completo, el script empieza con `DROP DATABASE IF EXISTS` asi que es seguro reintentar.
- **Si `pip install` falla con `CERTIFICATE_VERIFY_FAILED`:** pasa en la maquina con Windows porque Avast Antivirus intercepta el trafico HTTPS ("Web Shield") y le presenta a pip un certificado propio que pip no conoce. La solucion que se uso fue exportar el certificado raiz de Avast desde el almacen de Windows, pegarlo al final del bundle de CAs publico y dejarlo configurado en `venv\pip.ini`:
  ```
  [global]
  cert = <ruta al proyecto>\venv\cacert-avast.pem
  ```
  La otra opcion es desactivar el escaneo HTTPS de Avast (Menu → Configuracion → Proteccion → Core Shields → Web Shield → destildar "Habilitar el escaneo HTTPS") mientras se instalan las dependencias. Como el `venv` no se versiona, esto hay que rehacerlo si se recrea el entorno.
- Una vez que este script da todo OK en ambas maquinas, recien ahi arranca el desarrollo de la app (Fase 1 en `PLAN_4_DIAS.md`).
