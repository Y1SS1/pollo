"""Servidor MCP para el inventario del almacén de pollos asados.

El dueño habla con Claude en lenguaje normal ("vendí 3 cuartos con papas",
"llegaron 20 pollos") y Claude usa estas herramientas sobre la base SQLite.
No hay herramienta de SQL libre: solo operaciones seguras y acotadas.
"""
import os
import sqlite3
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

RAIZ = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("POLLOS_DB", RAIZ / "db" / "pollos.db"))
SCHEMA = RAIZ / "db" / "schema.sql"

mcp = MCPServer(
    "inventario-pollos",
    instructions=(
        "Inventario de un almacén de pollos asados. Se venden platos (1/4, 1/4 con papas, etc.) "
        "y cada venta descuenta sus ingredientes automáticamente. Usa registrar_venta para ventas, "
        "registrar_compra cuando llega mercadería, registrar_merma para pérdidas y ajustar_stock "
        "tras contar físicamente. Si el dueño no precisa una cantidad, pregúntala antes de registrar."
    ),
)


def conectar() -> sqlite3.Connection:
    nuevo = not DB_PATH.exists()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    if nuevo:
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
    return con


def _buscar(con, tabla: str, texto: str, extra: str = ""):
    """Busca por nombre: exacto primero, luego coincidencia parcial única."""
    t = texto.strip()
    filas = con.execute(f"SELECT * FROM {tabla} WHERE lower(nombre)=lower(?) {extra}", (t,)).fetchall()
    if not filas:
        filas = con.execute(
            f"SELECT * FROM {tabla} WHERE lower(nombre) LIKE lower(?) {extra}", (f"%{t}%",)
        ).fetchall()
    if not filas:
        raise ToolError(f"No encuentro «{texto}» en {tabla}. Revisa el nombre.")
    if len(filas) > 1:
        opciones = ", ".join(f["nombre"] for f in filas)
        raise ToolError(f"«{texto}» es ambiguo, puede ser: {opciones}. Indica cuál.")
    return filas[0]


def _producto(con, nombre):
    return _buscar(con, "producto", nombre, "AND activo=1")


def _plato(con, nombre):
    return _buscar(con, "plato", nombre, "AND activo=1")


def _stock(con, producto_id) -> float:
    return con.execute(
        "SELECT COALESCE(SUM(cantidad),0) FROM movimiento WHERE producto_id=?", (producto_id,)
    ).fetchone()[0]


def _positivo(valor, campo):
    if valor <= 0:
        raise ToolError(f"{campo} debe ser mayor que 0.")


def _mov(con, producto, tipo, cantidad, nota=None, costo=None, venta_id=None):
    try:
        con.execute(
            "INSERT INTO movimiento(producto_id,tipo,cantidad,costo_unitario,venta_id,nota) VALUES (?,?,?,?,?,?)",
            (producto["id"], tipo, cantidad, costo, venta_id, nota),
        )
    except sqlite3.IntegrityError as e:
        raise ToolError(f"No se pudo registrar para «{producto['nombre']}»: {e}") from e


# ---------------------------------------------------------------- consultas

@mcp.tool()
def ver_stock(buscar: str | None = None, categoria: str | None = None) -> list[dict]:
    """Muestra el stock actual (y si está OK / BAJO / AGOTADO). Filtra por nombre o categoría."""
    con = conectar()
    sql, args = "SELECT nombre,categoria,unidad,stock_actual,stock_minimo,estado FROM v_stock WHERE 1=1", []
    if buscar:
        sql += " AND lower(nombre) LIKE lower(?)"; args.append(f"%{buscar}%")
    if categoria:
        sql += " AND lower(categoria) LIKE lower(?)"; args.append(f"%{categoria}%")
    return [dict(r) for r in con.execute(sql + " ORDER BY categoria,nombre", args)]


@mcp.tool()
def productos_por_reponer() -> list[dict]:
    """Lista lo que está bajo el mínimo o agotado, con el proveedor y su teléfono."""
    return [dict(r) for r in conectar().execute("SELECT * FROM v_por_reponer")]


@mcp.tool()
def valor_inventario() -> dict:
    """Dinero total invertido en el inventario actual (stock × último costo)."""
    r = conectar().execute("SELECT ROUND(COALESCE(SUM(valor_inventario),0),2) FROM v_stock").fetchone()
    return {"valor_total": r[0]}


@mcp.tool()
def ver_menu() -> list[dict]:
    """Muestra los platos a la venta con su precio e ingredientes."""
    con = conectar()
    out = []
    for p in con.execute("SELECT * FROM plato WHERE activo=1 ORDER BY nombre"):
        ing = con.execute(
            "SELECT pr.nombre, r.cantidad, pr.unidad FROM receta r JOIN producto pr ON pr.id=r.producto_id WHERE r.plato_id=?",
            (p["id"],),
        ).fetchall()
        out.append({"plato": p["nombre"], "precio": p["precio"], "ingredientes": [dict(i) for i in ing]})
    return out


@mcp.tool()
def resumen_ventas(dias: int = 7) -> list[dict]:
    """Ventas, ganancia estimada y pérdida por merma de los últimos N días."""
    return [dict(r) for r in conectar().execute(
        "SELECT * FROM v_resumen_diario WHERE dia >= date('now','localtime',?) ORDER BY dia DESC",
        (f"-{max(dias,1)-1} days",),
    )]


@mcp.tool()
def historial(producto: str | None = None, limite: int = 20) -> list[dict]:
    """Últimos movimientos de inventario (todos, o de un producto)."""
    con = conectar()
    sql = ("SELECT m.fecha, p.nombre AS producto, m.tipo, m.cantidad, m.nota "
           "FROM movimiento m JOIN producto p ON p.id=m.producto_id")
    args: list = []
    if producto:
        sql += " WHERE p.id=?"; args.append(_producto(con, producto)["id"])
    sql += " ORDER BY m.id DESC LIMIT ?"; args.append(min(max(limite, 1), 200))
    return [dict(r) for r in con.execute(sql, args)]


# ---------------------------------------------------------------- operaciones

@mcp.tool()
def registrar_venta(plato: str, cantidad: int = 1) -> dict:
    """Registra la venta de N unidades de un plato y descuenta sus ingredientes del stock.
    Si falta algún ingrediente, no registra nada y explica qué falta."""
    _positivo(cantidad, "cantidad")
    con = conectar()
    with con:
        p = _plato(con, plato)
        ings = con.execute(
            "SELECT pr.*, r.cantidad AS por_unidad FROM receta r JOIN producto pr ON pr.id=r.producto_id WHERE r.plato_id=?",
            (p["id"],),
        ).fetchall()
        if not ings:
            raise ToolError(f"«{p['nombre']}» no tiene receta; no se puede descontar inventario.")
        faltan = []
        for i in ings:
            necesita, hay = i["por_unidad"] * cantidad, _stock(con, i["id"])
            if necesita > hay + 1e-6:
                faltan.append(f"{i['nombre']}: necesita {necesita:g} {i['unidad']}, hay {hay:g}")
        if faltan:
            raise ToolError("Stock insuficiente, no se registró la venta. " + "; ".join(faltan))
        vid = con.execute(
            "INSERT INTO venta(plato_id,cantidad,precio_unitario) VALUES (?,?,?)",
            (p["id"], cantidad, p["precio"]),
        ).lastrowid
        for i in ings:
            _mov(con, i, "VENTA", -i["por_unidad"] * cantidad, f"Venta: {cantidad} × {p['nombre']}", venta_id=vid)
    alertas = [dict(r) for r in conectar().execute(
        "SELECT nombre,stock_actual,unidad,estado FROM v_stock WHERE estado<>'OK' AND id IN (%s)"
        % ",".join(str(i["id"]) for i in ings))]
    return {"ok": True, "plato": p["nombre"], "cantidad": cantidad,
            "total": round(cantidad * p["precio"], 2), "alertas_de_stock": alertas}


@mcp.tool()
def registrar_compra(producto: str, cantidad: float, costo_unitario: float | None = None,
                     nota: str | None = None) -> dict:
    """Registra mercadería que llegó (suma al stock). costo_unitario actualiza el costo del producto."""
    _positivo(cantidad, "cantidad")
    con = conectar()
    with con:
        p = _producto(con, producto)
        _mov(con, p, "COMPRA", cantidad, nota, costo_unitario)
        return {"ok": True, "producto": p["nombre"], "stock_actual": _stock(con, p["id"]), "unidad": p["unidad"]}


@mcp.tool()
def registrar_merma(producto: str, cantidad: float, nota: str | None = None) -> dict:
    """Registra producto perdido (dañado, caído, vencido). Resta del stock."""
    _positivo(cantidad, "cantidad")
    con = conectar()
    with con:
        p = _producto(con, producto)
        _mov(con, p, "MERMA", -cantidad, nota)
        return {"ok": True, "producto": p["nombre"], "stock_actual": _stock(con, p["id"]), "unidad": p["unidad"]}


@mcp.tool()
def registrar_consumo(producto: str, cantidad: float, nota: str | None = None) -> dict:
    """Registra uso interno que no es una venta (p. ej. carbón gastado, comida del personal)."""
    _positivo(cantidad, "cantidad")
    con = conectar()
    with con:
        p = _producto(con, producto)
        _mov(con, p, "CONSUMO", -cantidad, nota)
        return {"ok": True, "producto": p["nombre"], "stock_actual": _stock(con, p["id"]), "unidad": p["unidad"]}


@mcp.tool()
def ajustar_stock(producto: str, stock_real: float, nota: str | None = None) -> dict:
    """Corrige el stock después de contar físicamente: deja el stock en el valor contado."""
    if stock_real < 0:
        raise ToolError("stock_real no puede ser negativo.")
    con = conectar()
    with con:
        p = _producto(con, producto)
        antes = _stock(con, p["id"])
        dif = round(stock_real - antes, 6)
        if dif != 0:
            _mov(con, p, "AJUSTE", dif, nota or "Conteo físico")
        return {"ok": True, "producto": p["nombre"], "stock_antes": antes, "stock_ahora": stock_real, "unidad": p["unidad"]}


# ---------------------------------------------------------------- catálogo

@mcp.tool()
def crear_producto(nombre: str, unidad: str, categoria: str, stock_minimo: float = 0,
                   costo_unitario: float = 0, proveedor: str | None = None) -> dict:
    """Agrega un producto nuevo al inventario (categoría/proveedor se crean si no existen)."""
    con = conectar()
    with con:
        con.execute("INSERT OR IGNORE INTO categoria(nombre) VALUES (?)", (categoria.strip(),))
        cat = con.execute("SELECT id FROM categoria WHERE lower(nombre)=lower(?)", (categoria.strip(),)).fetchone()[0]
        prov = None
        if proveedor:
            f = con.execute("SELECT id FROM proveedor WHERE lower(nombre)=lower(?)", (proveedor.strip(),)).fetchone()
            prov = f[0] if f else con.execute("INSERT INTO proveedor(nombre) VALUES (?)", (proveedor.strip(),)).lastrowid
        try:
            con.execute("INSERT INTO producto(nombre,categoria_id,proveedor_id,unidad,stock_minimo,costo_unitario) "
                        "VALUES (?,?,?,?,?,?)", (nombre.strip(), cat, prov, unidad, stock_minimo, costo_unitario))
        except sqlite3.IntegrityError as e:
            raise ToolError(f"No se pudo crear «{nombre}»: {e}") from e
    return {"ok": True, "producto": nombre}


@mcp.tool()
def crear_plato(nombre: str, precio: float, ingredientes: list[dict]) -> dict:
    """Crea un plato del menú. ingredientes = [{"producto": "Papas", "cantidad": 0.3}, ...]
    donde cantidad es lo que gasta UNA unidad del plato (ej. 0.25 pollo para un cuarto)."""
    if not ingredientes:
        raise ToolError("Indica al menos un ingrediente.")
    con = conectar()
    with con:
        try:
            pid = con.execute("INSERT INTO plato(nombre,precio) VALUES (?,?)", (nombre.strip(), precio)).lastrowid
        except sqlite3.IntegrityError as e:
            raise ToolError(f"No se pudo crear «{nombre}»: {e}") from e
        for ing in ingredientes:
            prod = _producto(con, ing["producto"])
            _positivo(float(ing["cantidad"]), "cantidad del ingrediente")
            con.execute("INSERT OR REPLACE INTO receta(plato_id,producto_id,cantidad) VALUES (?,?,?)",
                        (pid, prod["id"], float(ing["cantidad"])))
    return {"ok": True, "plato": nombre, "precio": precio}


@mcp.tool()
def cambiar_precio_plato(plato: str, nuevo_precio: float) -> dict:
    """Cambia el precio de un plato (las ventas ya registradas conservan su precio)."""
    if nuevo_precio < 0:
        raise ToolError("El precio no puede ser negativo.")
    con = conectar()
    with con:
        p = _plato(con, plato)
        con.execute("UPDATE plato SET precio=? WHERE id=?", (nuevo_precio, p["id"]))
    return {"ok": True, "plato": p["nombre"], "precio_anterior": p["precio"], "precio_nuevo": nuevo_precio}


if __name__ == "__main__":
    mcp.run()
