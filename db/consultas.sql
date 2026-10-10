-- Consultas de uso diario
SELECT * FROM v_stock ORDER BY categoria, nombre;       -- ¿Qué tengo?
SELECT * FROM v_por_reponer;                            -- ¿Qué debo comprar?
SELECT ROUND(SUM(valor_inventario),2) AS valor_total FROM v_stock;  -- ¿Cuánto vale mi inventario?
SELECT * FROM v_resumen_diario ORDER BY dia DESC;       -- Ventas y pérdidas por día

-- Registrar una compra:
-- INSERT INTO movimiento(producto_id,tipo,cantidad,costo_unitario) VALUES (1,'COMPRA',30,3.60);
-- Registrar una merma (pollo dañado):
-- INSERT INTO movimiento(producto_id,tipo,cantidad,nota) VALUES (1,'MERMA',-2,'Se echó a perder');
