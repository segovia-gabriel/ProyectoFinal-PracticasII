-- ============================================================
-- Sistema de Gestion de Restaurante - Practicas II
-- Alumnos: Macko Mijail y Segovia Gabriel
-- Motor: MySQL 8.x (probado en MySQL Workbench, macOS/Windows)
-- ============================================================
-- Este script crea la base completa y carga datos de prueba
-- para poder probar todos los modulos (incluyendo reservas
-- pasadas, actuales y futuras, e historial de precios).
-- ============================================================

DROP DATABASE IF EXISTS restaurante_db;
CREATE DATABASE restaurante_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE restaurante_db;

-- ------------------------------------------------------------
-- 1. USUARIOS (administradores del sistema)
-- ------------------------------------------------------------
CREATE TABLE usuarios (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario      VARCHAR(50)  NOT NULL UNIQUE,
    contrasena_hash      VARCHAR(255) NOT NULL,          -- hash bcrypt, nunca texto plano
    fecha_creacion       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion   DATETIME     NULL,
    fecha_ultimo_acceso  DATETIME     NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 2. HISTORIAL DE ACCIONES (auditoria de usuarios)
-- ------------------------------------------------------------
CREATE TABLE historial_acciones (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT NOT NULL,
    accion      VARCHAR(255) NOT NULL,   -- ej: "Inicio de sesion", "Creo cliente #12"
    fecha_hora  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historial_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 3. CLIENTES
-- ------------------------------------------------------------
CREATE TABLE clientes (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    nombre            VARCHAR(50)  NOT NULL,
    apellido          VARCHAR(50)  NOT NULL,
    dni               VARCHAR(15)  NOT NULL UNIQUE,
    fecha_nacimiento  DATE         NOT NULL,
    direccion         VARCHAR(150),
    telefono          VARCHAR(30),
    fecha_registro    DATE         NOT NULL DEFAULT (CURRENT_DATE)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 4. GRUPOS DE MESA (ej: Simple, VIP, Terraza) + valor editable
-- ------------------------------------------------------------
CREATE TABLE grupos_mesa (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    nombre  VARCHAR(50) NOT NULL UNIQUE,
    valor   DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 5. MESAS
-- ------------------------------------------------------------
CREATE TABLE mesas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    numero_mesa     INT NOT NULL UNIQUE,
    numero_sillas   INT NOT NULL,
    piso            INT NOT NULL,             -- 0 = planta baja, 1 = primer piso, ...
    codigo          VARCHAR(10) NOT NULL UNIQUE, -- letra de piso + numero_mesa (ej: A5)
    grupo_mesa_id   INT NOT NULL,
    CONSTRAINT fk_mesa_grupo FOREIGN KEY (grupo_mesa_id) REFERENCES grupos_mesa(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 6. GRUPOS DE MENU (bebidas, picadas, pastas, exotico, etc.)
-- ------------------------------------------------------------
CREATE TABLE grupos_menu (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    nombre  VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 7. ITEMS DEL MENU
-- ------------------------------------------------------------
CREATE TABLE menu_items (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    descripcion     VARCHAR(255),
    imagen_path     VARCHAR(255),              -- ruta relativa, gestionada con pathlib en la app
    grupo_menu_id   INT NOT NULL,
    CONSTRAINT fk_item_grupo FOREIGN KEY (grupo_menu_id) REFERENCES grupos_menu(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 8. HISTORIAL DE PRECIOS DEL MENU
--    precio_lista: precio normal
--    precio_especial + medio_pago_especial: precio distinto segun
--    el medio de pago (efectivo o transferencia) vigente en ese periodo
-- ------------------------------------------------------------
CREATE TABLE historial_precios_menu (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    menu_item_id          INT NOT NULL,
    precio_lista          DECIMAL(10,2) NOT NULL,
    precio_especial       DECIMAL(10,2) NULL,
    medio_pago_especial   ENUM('efectivo','transferencia') NULL,
    fecha_inicio          DATE NOT NULL,
    fecha_fin             DATE NULL,          -- NULL = precio vigente actualmente
    CONSTRAINT fk_precio_item FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 9. RESERVAS
--    precio_mesa_aplicado guarda el valor ya calculado
--    (valor del grupo * 1.00 o * 1.25 segun duracion) al momento
--    de crear la reserva, para no depender de cambios futuros
--    en el valor del grupo de mesa.
-- ------------------------------------------------------------
CREATE TABLE reservas (
    id                     INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id             INT NOT NULL,
    mesa_id                INT NOT NULL,
    fecha                  DATE NOT NULL,
    hora_inicio            TIME NOT NULL,
    hora_fin               TIME NOT NULL,
    duracion_tipo          ENUM('2h','3h') NOT NULL,
    precio_mesa_aplicado   DECIMAL(10,2) NOT NULL,
    estado_asistencia      ENUM('en_espera','asistio','tardanza','falto') NOT NULL DEFAULT 'en_espera',
    consumo_vencido        TINYINT(1) NOT NULL DEFAULT 0,   -- 1 = asistio pero el consumo no se cargo y el dia ya cerro
    CONSTRAINT fk_reserva_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    CONSTRAINT fk_reserva_mesa    FOREIGN KEY (mesa_id) REFERENCES mesas(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 10. CONSUMOS (uno por reserva)
--    estado: 'abierta' mientras la mesa sigue consumiendo (se le pueden
--    agregar/editar items) y 'cerrada' cuando se consolida la cuenta y pasa
--    al historial de ventas. Solo los consumos cerrados cuentan como venta
--    (estadisticas e ingresos).
-- ------------------------------------------------------------
CREATE TABLE consumos (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    reserva_id     INT NOT NULL UNIQUE,
    fecha          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    medio_pago     ENUM('efectivo','transferencia') NOT NULL,
    precio_total   DECIMAL(10,2) NOT NULL DEFAULT 0,
    estado         ENUM('abierta','cerrada') NOT NULL DEFAULT 'abierta',
    CONSTRAINT fk_consumo_reserva FOREIGN KEY (reserva_id) REFERENCES reservas(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 11. DETALLE DE CONSUMO (items pedidos en cada consumo)
--     precio_unitario_aplicado guarda el precio real pagado
--     (ya resuelto segun medio de pago), para que el historial
--     de ventas no cambie si despues se modifica el precio del item.
-- ------------------------------------------------------------
CREATE TABLE consumo_detalle (
    id                          INT AUTO_INCREMENT PRIMARY KEY,
    consumo_id                  INT NOT NULL,
    menu_item_id                INT NOT NULL,
    cantidad                    INT NOT NULL DEFAULT 1,
    precio_unitario_aplicado    DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_detalle_consumo FOREIGN KEY (consumo_id) REFERENCES consumos(id),
    CONSTRAINT fk_detalle_item    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
) ENGINE=InnoDB;

