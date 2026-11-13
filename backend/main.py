"""FastAPI entrypoint. Wires CRUD routes to ExpenseService, serves the UI shell."""

from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend import registry
from backend.db import get_conn, init_schema, is_empty
from backend.models import (
    CategoryOut, ExpenseCreate, ExpenseUpdate, ExpenseOut,
    MutationResult, SearchResult, SortResult, UndoRedoStatus,
)
from backend.seed import seed
from backend.services.expense_service import ExpenseService

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

app = FastAPI(title="BudgetTracker - DAA Project", version="0.2.0")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.on_event("startup")
def _startup():
    init_schema()
    if is_empty():
        n = seed(force=True)
        print(f"[startup] seeded {n} expenses")


@contextmanager
def service():
    conn = get_conn()
    try:
        svc = ExpenseService(conn)
        yield svc
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------- meta ----------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/registry")
def get_registry():
    return registry.REGISTRY


# ---------- categories ----------

@app.get("/categories", response_model=list[CategoryOut])
def list_categories():
    with service() as svc:
        return svc.list_categories()


# ---------- expenses: list + sort ----------

@app.get("/expenses", response_model=SortResult)
def list_expenses(
    field: str = "date",
    order: str = "asc",
    algo: str = "merge_sort",
):
    if field not in {"date", "amount_paise", "category_name", "description"}:
        raise HTTPException(400, f"bad field: {field}")
    if order not in {"asc", "desc"}:
        raise HTTPException(400, f"bad order: {order}")
    try:
        with service() as svc:
            rows, stats, f, o = svc.list_sorted(field, order, algo)
            return {"rows": rows, "stats": stats, "field": f, "order": o}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---------- expenses: range search ----------

@app.get("/expenses/search", response_model=SearchResult)
def search_expenses(from_date: str | None = None, to_date: str | None = None, q: str = ""):
    with service() as svc:
        rows, cmp_count = svc.search_range(from_date, to_date, q)
        return {
            "rows": rows,
            "binary_search_comparisons": cmp_count,
            "total_count": len(rows),
        }


# ---------- expenses: create / update / delete ----------

@app.post("/expenses", response_model=MutationResult)
def create_expense(payload: ExpenseCreate):
    with service() as svc:
        new_id = svc.create(payload.model_dump())
        return {
            "id": new_id,
            "status": "created",
            "undo_redo": svc.undo_redo_status(),
        }


@app.patch("/expenses/{expense_id}", response_model=MutationResult)
def update_expense(expense_id: int, payload: ExpenseUpdate):
    with service() as svc:
        try:
            svc.update(expense_id, payload.model_dump(exclude_none=True))
        except ValueError as e:
            raise HTTPException(404, str(e))
        return {"id": expense_id, "status": "updated", "undo_redo": svc.undo_redo_status()}


@app.delete("/expenses/{expense_id}", response_model=MutationResult)
def delete_expense(expense_id: int):
    with service() as svc:
        try:
            svc.delete(expense_id)
        except ValueError as e:
            raise HTTPException(404, str(e))
        return {"id": expense_id, "status": "deleted", "undo_redo": svc.undo_redo_status()}


# ---------- undo / redo ----------

@app.post("/undo", response_model=UndoRedoStatus)
def undo():
    with service() as svc:
        try:
            svc.undo()
        except ValueError as e:
            raise HTTPException(400, str(e))
        return svc.undo_redo_status()


@app.post("/redo", response_model=UndoRedoStatus)
def redo():
    with service() as svc:
        try:
            svc.redo()
        except ValueError as e:
            raise HTTPException(400, str(e))
        return svc.undo_redo_status()


@app.get("/undo-redo-status", response_model=UndoRedoStatus)
def undo_redo_status():
    with service() as svc:
        return svc.undo_redo_status()


# ---------- autocomplete ----------

@app.get("/autocomplete")
def autocomplete(q: str = "", limit: int = 8):
    if not q:
        return {"suggestions": []}
    with service() as svc:
        return {"suggestions": svc.autocomplete(q, limit=limit)}


# ---------- UI ----------

@app.get("/favicon.ico")
def favicon():
    return FileResponse(str(FRONTEND_DIR / "assets" / "favicon.ico")) if (FRONTEND_DIR / "assets" / "favicon.ico").exists() else FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/")
def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

# ---------- analytics (D&C + order statistics) ----------

from backend.services.analytics_service import AnalyticsService


@contextmanager
def analytics():
    conn = get_conn()
    try:
        svc = AnalyticsService(conn)
        yield svc
        conn.commit()
    finally:
        conn.close()


@app.get("/analytics/summary")
def analytics_summary():
    with analytics() as s:
        return s.summary()


@app.get("/analytics/median")
def analytics_median():
    with analytics() as s:
        return s.median_expense()


@app.get("/analytics/percentile")
def analytics_percentile(p: float = 90.0):
    with analytics() as s:
        return s.percentile(p)


@app.get("/analytics/top-k")
def analytics_top_k(k: int = 5):
    with analytics() as s:
        return s.top_k(k)


@app.get("/analytics/outliers")
def analytics_outliers():
    with analytics() as s:
        return s.outliers()


@app.get("/analytics/streak")
def analytics_streak():
    with analytics() as s:
        return s.worst_streak()


@app.get("/analytics/inversions")
def analytics_inversions():
    with analytics() as s:
        return s.inversions()


@app.get("/analytics/dominant-category")
def analytics_dominant_category():
    with analytics() as s:
        return s.dominant_category()


@app.get("/analytics/duplicates")
def analytics_duplicates():
    with analytics() as s:
        return s.duplicates()


@app.get("/analytics/category-totals")
def analytics_category_totals():
    with analytics() as s:
        return s.category_totals()


@app.get("/analytics/daily-spend")
def analytics_daily_spend(days: int = 30):
    with analytics() as s:
        return s.daily_spend(days)


# ---------- optimiser (greedy + huffman) ----------

from backend.services import budget_service, settlement_service


@app.post("/optimize/goals")
def optimize_goals(body: dict):
    try:
        amount = int(body.get("monthly_savings_paise", 0))
    except (TypeError, ValueError):
        raise HTTPException(400, "monthly_savings_paise must be an integer")
    return budget_service.optimize_goals(amount)


@app.get("/optimize/bills")
def optimize_bills():
    return budget_service.schedule_bills()


@app.post("/optimize/change")
def optimize_change(body: dict):
    try:
        amount = int(body.get("amount_paise", 0))
    except (TypeError, ValueError):
        raise HTTPException(400, "amount_paise must be an integer")
    if amount < 0:
        raise HTTPException(400, "amount_paise must be non-negative")
    return budget_service.breakdown_cash(amount)


@app.get("/optimize/shifts")
def optimize_shifts():
    return budget_service.schedule_shifts()


@app.get("/settle")
def settle():
    return settlement_service.settle()


@app.get("/compress/huffman")
def compress_huffman():
    conn = get_conn()
    try:
        return budget_service.compress_expense_log(conn)
    finally:
        conn.close()
