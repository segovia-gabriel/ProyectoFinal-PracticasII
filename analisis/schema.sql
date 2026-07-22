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
    CONSTRAINT fk_reserva_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    CONSTRAINT fk_reserva_mesa    FOREIGN KEY (mesa_id) REFERENCES mesas(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 10. CONSUMOS (uno por reserva)
-- ------------------------------------------------------------
CREATE TABLE consumos (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    reserva_id     INT NOT NULL UNIQUE,
    fecha          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    medio_pago     ENUM('efectivo','transferencia') NOT NULL,
    precio_total   DECIMAL(10,2) NOT NULL DEFAULT 0,
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


-- ============================================================
-- DATOS DE PRUEBA
-- (fechas relativas a julio 2026 para tener reservas pasadas,
-- actuales y futuras al momento de la defensa)
-- ============================================================

-- Usuarios (contrasenas en texto plano de referencia, ya hasheadas con bcrypt abajo)
-- gsegovia / Admin123!      -- mmacko / Mijail2026!
INSERT INTO usuarios (nombre_usuario, contrasena_hash, fecha_creacion, fecha_ultimo_acceso) VALUES
('gsegovia', '$2b$12$2Rlx/vrLaxzP2qRgBYZlm..nYJpeXhWxGPIkNNxLG4FX.2zWiG9BG', '2026-07-01 09:00:00', '2026-07-13 08:30:00'),
('mmacko',   '$2b$12$lDsTLyC.ZoKM.hmYljnItuDysUVtvcf./XBWbOTMdLZCsME9q7mjG', '2026-07-01 09:05:00', '2026-07-12 20:15:00');

INSERT INTO historial_acciones (usuario_id, accion, fecha_hora) VALUES
(1, 'Inicio de sesion', '2026-07-13 08:30:00'),
(1, 'Alta de cliente: Perez, Juan',  '2026-07-13 08:45:00'),
(2, 'Inicio de sesion', '2026-07-12 20:15:00'),
(2, 'Modifico precio de item de menu: Milanesa Napolitana', '2026-07-12 20:20:00');

-- Clientes
INSERT INTO clientes (nombre, apellido, dni, fecha_nacimiento, direccion, telefono, fecha_registro) VALUES
('Juan',    'Perez',    '30111222', '1988-03-14', 'San Martin 450, Cordoba',   '351-555-1010', '2026-01-10'),
('Maria',   'Gomez',    '32444555', '1990-07-22', 'Belgrano 120, Cordoba',     '351-555-2020', '2026-02-05'),
('Carlos',  'Lopez',    '28999888', '1985-11-02', 'Av. Colon 900, Cordoba',    '351-555-3030', '2026-03-18'),
('Lucia',   'Fernandez','35123456', '1995-05-30', 'Sucre 233, Cordoba',        '351-555-4040', '2026-04-01'),
('Sofia',   'Diaz',     '33222111', '1992-09-09', 'Rivadavia 78, Cordoba',     '351-555-5050', '2026-05-20');

-- Grupos de mesa
INSERT INTO grupos_mesa (nombre, valor) VALUES
('Simple', 1000.00),
('VIP',    2500.00),
('Terraza',1800.00);

-- Mesas (codigo = letra de piso + numero_mesa; A=planta baja, B=primer piso)
INSERT INTO mesas (numero_mesa, numero_sillas, piso, codigo, grupo_mesa_id) VALUES
(1, 2, 0, 'A1', 1),
(2, 4, 0, 'A2', 1),
(3, 6, 0, 'A3', 2),
(4, 4, 1, 'B4', 3),
(5, 2, 1, 'B5', 1);

-- Grupos de menu
INSERT INTO grupos_menu (nombre) VALUES
('Bebidas'), ('Picadas'), ('Pastas'), ('Exotico');

-- Items de menu
INSERT INTO menu_items (nombre, descripcion, imagen_path, grupo_menu_id) VALUES
('Agua con gas',           'Botella 500ml',                         'img/menu/agua.jpg',       1),
('Picada para 2',          'Fiambres, quesos y pan casero',         'img/menu/picada.jpg',     2),
('Milanesa Napolitana',    'Con papas fritas',                      'img/menu/milanesa.jpg',   3),
('Sushi Exotico x8',       'Roll de salmon y palta',                'img/menu/sushi.jpg',      4);

-- Historial de precios (el mas reciente de cada item tiene fecha_fin = NULL, vigente)
INSERT INTO historial_precios_menu (menu_item_id, precio_lista, precio_especial, medio_pago_especial, fecha_inicio, fecha_fin) VALUES
(1, 1500.00, NULL,     NULL,           '2026-01-01', '2026-04-30'),
(1, 1800.00, 1600.00,  'efectivo',     '2026-05-01', NULL),
(2, 6000.00, NULL,     NULL,           '2026-01-01', '2026-06-30'),
(2, 7000.00, 6500.00,  'transferencia','2026-07-01', NULL),
(3, 8500.00, NULL,     NULL,           '2026-01-01', '2026-06-30'),
(3, 9200.00, 8700.00,  'efectivo',     '2026-07-01', NULL),
(4, 12000.00,11000.00, 'transferencia','2026-06-01', NULL);

-- Reservas: pasadas, actuales (hoy = 2026-07-13) y futuras
INSERT INTO reservas (cliente_id, mesa_id, fecha, hora_inicio, hora_fin, duracion_tipo, precio_mesa_aplicado, estado_asistencia) VALUES
(1, 1, '2026-06-20', '20:00:00', '22:00:00', '2h', 1000.00, 'asistio'),   -- pasada
(2, 3, '2026-07-01', '21:00:00', '23:00:00', '2h', 2500.00, 'asistio'),   -- pasada
(3, 2, '2026-07-13', '13:00:00', '15:00:00', '2h', 1000.00, 'en_espera'), -- hoy
(4, 4, '2026-07-15', '20:00:00', '23:00:00', '3h', 2250.00, 'en_espera'), -- futura
(5, 5, '2026-07-20', '21:00:00', '23:00:00', '2h', 1000.00, 'en_espera'); -- futura

-- Consumos (solo de las reservas pasadas ya completadas)
INSERT INTO consumos (reserva_id, fecha, medio_pago, precio_total) VALUES
(1, '2026-06-20 22:05:00', 'efectivo',      1600.00),
(2, '2026-07-01 23:10:00', 'transferencia', 6500.00);

-- Detalle de consumo
INSERT INTO consumo_detalle (consumo_id, menu_item_id, cantidad, precio_unitario_aplicado) VALUES
(1, 1, 1, 1600.00),           -- Juan tomo agua con gas (precio especial efectivo)
(2, 2, 1, 6500.00);           -- Maria pidio picada para 2 (precio especial transferencia)
