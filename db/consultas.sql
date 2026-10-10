SELECT * FROM v_stock ORDER BY categoria, nombre;                    -- ¿Qué tengo?
SELECT * FROM v_por_reponer;                                         -- ¿Qué debo comprar?
SELECT ROUND(SUM(valor_inventario),2) AS valor_total FROM v_stock;   -- ¿Cuánto vale el inventario?
SELECT * FROM v_resumen_diario ORDER BY dia DESC;                    -- Ventas, ganancia y mermas por día
-- Las ventas, compras y mermas se registran desde Claude con el servidor MCP (ver README).
