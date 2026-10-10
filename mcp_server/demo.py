"""Demo con datos falsos: simula un día de trabajo en una base temporal.
Uso: python -I mcp_server/demo.py     (no toca db/pollos.db)"""
import asyncio, json, os, sys, tempfile
from pathlib import Path

os.environ["POLLOS_DB"] = str(Path(tempfile.mkdtemp()) / "demo.db")
sys.path.insert(0, str(Path(__file__).parent))
import server  # noqa: E402

server.conectar().executescript((Path(__file__).parent.parent / "db" / "seed.sql").read_text(encoding="utf-8"))


async def paso(titulo, tool, **args):
    print(f"\n>>> {titulo}")
    try:
        r = await server.mcp.call_tool(tool, args)
        datos = json.loads(r.content[0].text) if r.content else []
        for fila in (datos if isinstance(datos, list) else [datos]):
            print("   ", "  |  ".join(f"{k}: {v}" for k, v in fila.items()))
        if not datos:
            print("    (nada que mostrar)")
    except Exception as e:
        print("    ❌", str(e).replace("Error executing tool " + tool + ": ", ""))


async def main():
    await paso("Dueño: ¿qué tengo en carnes y acompañantes?", "ver_stock", categoria="carnes")
    await paso("Dueño: vendí 8 cuartos con papas", "registrar_venta", plato="1/4 de pollo con papas fritas", cantidad=8)
    await paso("Dueño: vendí 5 cuartos solos y 3 gaseosas", "registrar_venta", plato="1/4 de pollo", cantidad=5)
    await paso("   (gaseosas)", "registrar_venta", plato="gaseosa", cantidad=3)
    await paso("Dueño: vendí 1/4 (ambiguo, Claude preguntaría)", "registrar_venta", plato="1/4")
    await paso("Dueño: vendí 200 pollos enteros (más de lo que hay)", "registrar_venta", plato="pollo entero", cantidad=200)
    await paso("Dueño: se cayó un pollo", "registrar_merma", producto="pollo crudo", cantidad=1, nota="se cayó")
    await paso("Dueño: gastamos 6 sacos de carbón", "registrar_consumo", producto="carbón", cantidad=6)
    await paso("Dueño: conté 10 kg de papas", "ajustar_stock", producto="papas", stock_real=10)
    await paso("Dueño: ¿qué me falta comprar?", "productos_por_reponer")
    await paso("Dueño: llegaron 30 pollos a 3.60", "registrar_compra", producto="pollo crudo", cantidad=30, costo_unitario=3.6)
    await paso("Dueño: ¿cuánto vendí hoy?", "resumen_ventas", dias=1)
    await paso("Dueño: ¿cuánto vale mi inventario?", "valor_inventario")


asyncio.run(main())
