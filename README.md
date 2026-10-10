# Control de inventario – Almacén de pollos asados

Base de datos SQLite + servidor MCP para que el dueño maneje el inventario hablando con Claude.

    db/schema.sql        estructura de la base (se crea sola al primer uso)
    db/seed.sql          datos de ejemplo (productos, menú y recetas) – reemplazar por los reales
    db/consultas.sql     consultas útiles si se abre la base con DB Browser for SQLite
    mcp_server/server.py servidor MCP (14 herramientas)

## Cómo funciona
- **Productos**: lo que se compra y se guarda (pollo crudo, papas, carbón, bolsas...), con stock mínimo y costo.
- **Platos + recetas**: lo que se vende. Ej.: *1/4 de pollo* = 0.25 pollo + 0.01 kg especias + 1 bolsa;
  *1/4 con papas fritas* suma 0.30 kg de papas y 0.03 l de salsa. Al vender, el stock se descuenta solo.
- **Movimientos**: todo queda en un historial (COMPRA, VENTA, CONSUMO, MERMA, AJUSTE). El stock es la suma
  de los movimientos, y la base no permite dejar el stock en negativo.
- Si una venta no se puede completar (falta un ingrediente), no se registra nada.

## Instalar el MCP (computador del dueño)
1. Instalar Python 3.10+ y las dependencias: `pip install -r mcp_server/requirements.txt`
2. (Opcional) cargar datos de ejemplo: `python -c "import sqlite3;c=sqlite3.connect('db/pollos.db');c.executescript(open('db/schema.sql').read());c.executescript(open('db/seed.sql').read())"`
   Si no, la base vacía se crea sola al primer uso y se llena pidiéndole a Claude `crear_producto` / `crear_plato`.
3. En Claude Desktop → Configuración → Desarrollador → Editar configuración (`claude_desktop_config.json`):

       {
         "mcpServers": {
           "inventario-pollos": {
             "command": "python",
             "args": ["C:/ruta/a/pollo/mcp_server/server.py"],
             "env": { "POLLOS_DB": "C:/ruta/a/pollo/db/pollos.db" }
           }
         }
       }

   (En Mac/Linux, usa rutas como `/Users/.../pollo/...` y `python3`.) Reiniciar Claude Desktop.

## Ejemplos de uso (en el chat)
- "Vendí 3 cuartos con papas y 2 gaseosas"
- "Llegaron 30 pollos a 3.60 cada uno"
- "Se me cayó un pollo, anótalo como merma"
- "¿Qué me falta comprar?" · "¿Cuánto vendí esta semana?" · "Conté 18 kg de papas, ajusta el stock"
- "Sube el 1/4 con papas a 6.00"

## Pruebas
    python -I mcp_server/test_server.py

## Respaldo
Todo el negocio está en el archivo `db/pollos.db`: copiarlo a un pendrive o a la nube cada día.
