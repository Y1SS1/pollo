# Control de inventario – Almacén de pollos asados

Base de datos SQLite (`db/`). Crear la base:

    cd db
    sqlite3 pollos.db < schema.sql      # o con Python: sqlite3.connect(...).executescript(...)
    sqlite3 pollos.db < seed.sql        # datos de ejemplo (opcional)

Se puede abrir `pollos.db` con **DB Browser for SQLite** (gratis, con interfaz visual).

## Cómo funciona
- `producto`: todo lo que se controla (pollo, papas, carbón, bolsas, bebidas...), con stock mínimo, costo y precio.
- `movimiento`: cada entrada/salida (COMPRA, VENTA, CONSUMO, MERMA, AJUSTE). El stock se calcula sumando movimientos.
- No deja sacar más stock del que existe.
- Vistas: `v_stock`, `v_por_reponer`, `v_resumen_diario`. Ejemplos en `db/consultas.sql`.
