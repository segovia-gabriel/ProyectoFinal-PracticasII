-- ============================================================
-- Migracion: agregar el estado abierta/cerrada a los consumos.
-- Correr UNA vez sobre una base restaurante_db ya existente (no borra datos).
-- Si en cambio volves a importar schema.sql completo, NO hace falta esto:
-- el schema ya trae la columna y marca los consumos de prueba como 'cerrada'.
-- ============================================================
USE restaurante_db;

-- 1. Nueva columna. Los consumos nuevos que cargue la app nacen 'abierta'.
ALTER TABLE consumos
    ADD COLUMN estado ENUM('abierta','cerrada') NOT NULL DEFAULT 'abierta';

-- 2. Todo lo que ya estaba cargado son ventas ya ocurridas: se marcan cerradas.
UPDATE consumos SET estado = 'cerrada';
