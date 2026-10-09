from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db, service

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Banco novo (sem regras nem transações) já nasce com as regras padrão."""
    conn = db.connect()
    try:
        empty = not conn.execute("SELECT 1 FROM rules UNION ALL SELECT 1 FROM transactions LIMIT 1").fetchone()
        if empty:
            service.seed_default_rules(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="Finanças", lifespan=lifespan)


def get_conn():
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


class RuleIn(BaseModel):
    pattern: str
    category: str
    priority: int = 0


@app.post("/import")
async def import_csv(file: UploadFile, conn=Depends(get_conn)):
    try:
        return service.import_csv(conn, await file.read())
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/rules")
def add_rule(rule: RuleIn, conn=Depends(get_conn)):
    conn.execute("INSERT INTO rules (household_id, pattern, category, priority) VALUES (?,?,?,?)",
                 (service.HOUSEHOLD, rule.pattern, rule.category, rule.priority))
    conn.commit()
    return {"recategorizadas": service.recategorize(conn)}


@app.post("/rules/seed")
def seed_rules(conn=Depends(get_conn)):
    return service.seed_default_rules(conn)


@app.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, conn=Depends(get_conn)):
    if not service.delete_rule(conn, rule_id):
        raise HTTPException(404, "Regra não encontrada")
    return {"ok": True}


@app.get("/rules")
def list_rules(conn=Depends(get_conn)):
    return service.get_rules(conn)


@app.put("/own-names/{name}")
def add_own_name(name: str, conn=Depends(get_conn)):
    """Nome (como aparece no Pix) de contas suas: vira 'transfer' e não conta como gasto."""
    conn.execute("INSERT OR IGNORE INTO own_names (household_id, name) VALUES (?,?)",
                 (service.HOUSEHOLD, " ".join(name.split()).upper()))
    conn.commit()
    service.reclassify(conn)
    return {"nomes": sorted(service.get_own_names(conn))}


@app.get("/reports/monthly")
def monthly(month: str, conn=Depends(get_conn)):
    return service.monthly_report(conn, month)


class CategoryIn(BaseModel):
    category: str
    remember: bool = False


@app.patch("/transactions/{tx_id}")
def set_category(tx_id: int, body: CategoryIn, conn=Depends(get_conn)):
    category = body.category.strip()
    if not category:
        raise HTTPException(422, "Categoria vazia")
    res = service.set_category(conn, tx_id, category, body.remember)
    if res is None:
        raise HTTPException(404, "Transação não encontrada")
    return res


@app.get("/categories")
def categories(conn=Depends(get_conn)):
    return service.list_categories(conn)


@app.get("/reports/daily")
def daily(month: str, conn=Depends(get_conn)):
    return service.daily_report(conn, month)


@app.get("/transactions")
def transactions(month: str, category: str | None = None, kind: str | None = None,
                 kinds: str | None = None, q: str | None = None, desc: bool = False, conn=Depends(get_conn)):
    """kind=expense ou kinds=income,expense; q busca na descrição/contraparte; desc=true: mais novas primeiro."""
    sql = "SELECT * FROM transactions WHERE household_id=? AND date LIKE ?"
    args: list = [service.HOUSEHOLD, f"{month}-%"]
    if category:
        sql += " AND category=?"
        args.append(category)
    wanted = [k for k in (kinds.split(",") if kinds else [kind] if kind else []) if k]
    if wanted:
        sql += f" AND kind IN ({','.join('?' * len(wanted))})"
        args += wanted
    if q and q.strip():
        like = f"%{q.strip().lower()}%"
        sql += " AND (lower(description) LIKE ? OR lower(counterparty) LIKE ?)"
        args += [like, like]
    order = "DESC" if desc else "ASC"
    return [dict(r) for r in conn.execute(f"{sql} ORDER BY date {order}, id {order}", args)]


STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(STATIC / "manifest.webmanifest", media_type="application/manifest+json")
