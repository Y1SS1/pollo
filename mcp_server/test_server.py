"""Prueba de humo: python -I mcp_server/test_server.py"""
import asyncio, os, sys, tempfile
from pathlib import Path

tmp = Path(tempfile.mkdtemp()) / "t.db"
os.environ["POLLOS_DB"] = str(tmp)
sys.path.insert(0, str(Path(__file__).parent))
import server  # noqa: E402

seed = (Path(__file__).parent.parent / "db" / "seed.sql").read_text(encoding="utf-8")
server.conectar().executescript(seed)


async def call(name, **args):
    r = await server.mcp.call_tool(name, args)
    return r


async def main():
    tools = await server.mcp.list_tools()
    print(len(tools), "herramientas:", [t.name for t in tools])
    print(await call("registrar_venta", plato="1/4 de pollo con papas", cantidad=3))
    print(await call("registrar_venta", plato="gaseosa", cantidad=2))
    print(await call("registrar_merma", producto="pollo crudo", cantidad=1, nota="se cayó"))
    print(await call("registrar_compra", producto="Carbón", cantidad=2, costo_unitario=6.5))
    print(await call("ajustar_stock", producto="Papas", stock_real=20))
    print(await call("ver_stock", categoria="carnes"))
    print(await call("resumen_ventas", dias=1))
    print(await call("productos_por_reponer"))
    for bad in [dict(plato="pollo entero", cantidad=500), dict(plato="xyz"), dict(plato="1/4", cantidad=1)]:
        try:
            print("¡NO falló!", await call("registrar_venta", **bad))
        except Exception as e:
            print("Error esperado:", str(e)[:140])
    n = server.conectar().execute("SELECT COUNT(*) FROM venta").fetchone()[0]
    print("ventas registradas (debe ser 2):", n)

asyncio.run(main())
