-- Control de inventario - Almacén de pollos asados
-- Motor: SQLite 3
PRAGMA foreign_keys = ON;

CREATE TABLE categoria (
    id      INTEGER PRIMARY KEY,
    nombre  TEXT NOT NULL UNIQUE          -- Ej: Carnes, Insumos, Bebidas, Empaques
);

CREATE TABLE proveedor (
    id        INTEGER PRIMARY KEY,
    nombre    TEXT NOT NULL,
    telefono  TEXT,
    notas     TEXT
);

-- Todo lo que el almacén necesita controlar: pollo crudo, carbón, bolsas, papas, bebidas...
CREATE TABLE producto (
    id            INTEGER PRIMARY KEY,
    nombre        TEXT NOT NULL UNIQUE,
    categoria_id  INTEGER NOT NULL REFERENCES categoria(id),
    proveedor_id  INTEGER REFERENCES proveedor(id),
    unidad        TEXT NOT NULL,                       -- unidad, kg, litro, bolsa, saco...
    stock_minimo  REAL NOT NULL DEFAULT 0 CHECK (stock_minimo >= 0),  -- debajo de esto = alerta
    costo_unitario REAL NOT NULL DEFAULT 0 CHECK (costo_unitario >= 0),
    precio_venta  REAL CHECK (precio_venta >= 0),      -- NULL si no se vende directamente
    perecedero    INTEGER NOT NULL DEFAULT 0 CHECK (perecedero IN (0,1)),
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1))
);

-- Cada cambio de inventario es un movimiento. El stock se calcula sumándolos,
-- así nunca se desajusta y siempre hay historial de qué pasó.
CREATE TABLE movimiento (
    id           INTEGER PRIMARY KEY,
    producto_id  INTEGER NOT NULL REFERENCES producto(id),
    fecha        TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    tipo         TEXT NOT NULL CHECK (tipo IN ('COMPRA','VENTA','CONSUMO','MERMA','AJUSTE')),
    cantidad     REAL NOT NULL CHECK (cantidad <> 0),
        -- positiva = entra (COMPRA, AJUSTE+); negativa = sale (VENTA, CONSUMO, MERMA, AJUSTE-)
    costo_unitario REAL CHECK (costo_unitario >= 0),   -- precio pagado en las COMPRA
    nota         TEXT,
    CHECK ( (tipo = 'COMPRA' AND cantidad > 0)
         OR (tipo IN ('VENTA','CONSUMO','MERMA') AND cantidad < 0)
         OR  tipo = 'AJUSTE')
);
CREATE INDEX idx_mov_producto_fecha ON movimiento(producto_id, fecha);

-- No permitir sacar más de lo que hay en stock
CREATE TRIGGER trg_no_stock_negativo
BEFORE INSERT ON movimiento
WHEN NEW.cantidad < 0 AND
     (SELECT COALESCE(SUM(cantidad),0) FROM movimiento WHERE producto_id = NEW.producto_id) + NEW.cantidad < 0
BEGIN
    SELECT RAISE(ABORT, 'Stock insuficiente para este movimiento');
END;

-- Al comprar, actualiza el costo del producto al último precio pagado
CREATE TRIGGER trg_actualiza_costo
AFTER INSERT ON movimiento
WHEN NEW.tipo = 'COMPRA' AND NEW.costo_unitario IS NOT NULL
BEGIN
    UPDATE producto SET costo_unitario = NEW.costo_unitario WHERE id = NEW.producto_id;
END;

-- ===== Vistas de consulta =====

-- Stock actual de cada producto
CREATE VIEW v_stock AS
SELECT p.id, p.nombre, c.nombre AS categoria, p.unidad,
       COALESCE(SUM(m.cantidad),0)                      AS stock_actual,
       p.stock_minimo,
       ROUND(COALESCE(SUM(m.cantidad),0) * p.costo_unitario, 2) AS valor_inventario,
       CASE WHEN COALESCE(SUM(m.cantidad),0) <= 0              THEN 'AGOTADO'
            WHEN COALESCE(SUM(m.cantidad),0) <= p.stock_minimo THEN 'BAJO'
            ELSE 'OK' END                               AS estado
FROM producto p
JOIN categoria c ON c.id = p.categoria_id
LEFT JOIN movimiento m ON m.producto_id = p.id
WHERE p.activo = 1
GROUP BY p.id;

-- Lo que hay que comprar ya
CREATE VIEW v_por_reponer AS
SELECT s.nombre, s.categoria, s.unidad, s.stock_actual, s.stock_minimo, s.estado,
       pr.nombre AS proveedor, pr.telefono
FROM v_stock s
JOIN producto p ON p.id = s.id
LEFT JOIN proveedor pr ON pr.id = p.proveedor_id
WHERE s.estado <> 'OK'
ORDER BY s.estado, s.nombre;

-- Resumen diario de ventas y mermas (pérdidas)
CREATE VIEW v_resumen_diario AS
SELECT date(m.fecha) AS dia,
       ROUND(SUM(CASE WHEN m.tipo='VENTA' THEN -m.cantidad * COALESCE(p.precio_venta,0) END),2) AS ventas,
       ROUND(SUM(CASE WHEN m.tipo='MERMA' THEN -m.cantidad * p.costo_unitario END),2)           AS perdida_por_merma
FROM movimiento m JOIN producto p ON p.id = m.producto_id
GROUP BY date(m.fecha);
