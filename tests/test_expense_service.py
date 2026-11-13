"""End-to-end tests for ExpenseService against an in-memory SQLite DB."""

import os
import tempfile
from pathlib import Path

import pytest

# Force a fresh temp DB before importing backend.db
_TMP_DIR = tempfile.mkdtemp(prefix="bt_test_")
_TMP_DB = Path(_TMP_DIR) / "test.db"
os.environ["BUDGETTRACKER_DB"] = str(_TMP_DB)

from backend import db as db_module
db_module.DB_PATH = _TMP_DB
db_module.init_schema()

from backend.seed import seed
from backend.services.expense_service import ExpenseService


@pytest.fixture
def svc():
    db_module.init_schema()
    conn = db_module.get_conn()
    conn.execute("DELETE FROM expenses")
    conn.execute("DELETE FROM categories")
    conn.commit()
    seed(force=True)
    s = ExpenseService(conn)
    yield s
    conn.close()


def _any_category_id(svc):
    """Grab a real category id ? never hardcode, AUTOINCREMENT shifts across runs."""
    row = svc.conn.execute("SELECT MIN(id) AS cid FROM categories").fetchone()
    assert row["cid"] is not None
    return row["cid"]


def test_seed_creates_200_plus_expenses(svc):
    rows = svc._fetch_all()
    assert len(rows) >= 200


def test_list_sorted_by_amount_with_merge(svc):
    rows, stats, _, _ = svc.list_sorted("amount_paise", "asc", "merge_sort")
    amounts = [r["amount_paise"] for r in rows]
    assert amounts == sorted(amounts)
    assert stats["comparisons"] > 0


def test_list_sorted_by_amount_desc(svc):
    rows, _, _, _ = svc.list_sorted("amount_paise", "desc", "quick_sort")
    amounts = [r["amount_paise"] for r in rows]
    assert amounts == sorted(amounts, reverse=True)


def test_sort_stability_for_ties(svc):
    """Sorting by category should preserve original order within a category."""
    rows, _, _, _ = svc.list_sorted("category_name", "asc", "merge_sort")
    i = 0
    while i < len(rows):
        j = i
        while j < len(rows) and rows[j]["category_name"] == rows[i]["category_name"]:
            j += 1
        ids = [rows[k]["id"] for k in range(i, j)]
        assert ids == sorted(ids)
        i = j


def test_range_search(svc):
    rows, _ = svc.search_range()
    if not rows:
        pytest.skip("no rows")
    mid_date = rows[len(rows) // 2]["date"]
    hi, _ = svc.search_range(from_date=mid_date)
    assert all(r["date"] >= mid_date for r in hi)
    assert len(hi) <= len(rows)


def test_undo_redo_cycle(svc):
    before = len(svc._fetch_all())
    svc.create({
        "amount_paise": 12345,
        "date": "2026-01-15",
        "category_id": _any_category_id(svc),   # ? use a real id
        "description": "test",
        "payment_mode": "cash",
    })
    assert len(svc._fetch_all()) == before + 1
    svc.undo()
    assert len(svc._fetch_all()) == before
    svc.redo()
    assert len(svc._fetch_all()) == before + 1


def test_update_undo(svc):
    rows = svc._fetch_all()
    target = rows[0]
    original_amount = target["amount_paise"]
    svc.update(target["id"], {"amount_paise": 99999})
    after = svc._fetch_all()
    updated = [r for r in after if r["id"] == target["id"]][0]
    assert updated["amount_paise"] == 99999
    svc.undo()
    after_undo = [r for r in svc._fetch_all() if r["id"] == target["id"]][0]
    assert after_undo["amount_paise"] == original_amount


def test_delete_undo(svc):
    rows = svc._fetch_all()
    target_id = rows[0]["id"]
    before = len(rows)
    svc.delete(target_id)
    assert len(svc._fetch_all()) == before - 1
    svc.undo()
    assert len(svc._fetch_all()) == before


def test_delete_then_redo_deletes_again(svc):
    """Redo of a delete must delete again, not re-insert. Regression for the old bug."""
    rows = svc._fetch_all()
    target_id = rows[0]["id"]
    before = len(rows)
    svc.delete(target_id)
    assert len(svc._fetch_all()) == before - 1
    svc.undo()
    assert len(svc._fetch_all()) == before
    svc.redo()
    assert len(svc._fetch_all()) == before - 1


def test_multiple_operations_undo_redo(svc):
    """Stack both creates, undo both, redo both, in order."""
    before = len(svc._fetch_all())
    cat = _any_category_id(svc)
    svc.create({"amount_paise": 100, "date": "2026-01-15",
                "category_id": cat, "description": "a", "payment_mode": "cash"})
    svc.create({"amount_paise": 200, "date": "2026-01-16",
                "category_id": cat, "description": "b", "payment_mode": "cash"})
    assert len(svc._fetch_all()) == before + 2
    svc.undo()
    assert len(svc._fetch_all()) == before + 1
    svc.undo()
    assert len(svc._fetch_all()) == before
    svc.redo()
    assert len(svc._fetch_all()) == before + 1
    svc.redo()
    assert len(svc._fetch_all()) == before + 2


def test_new_action_clears_redo(svc):
    cat = _any_category_id(svc)
    svc.create({"amount_paise": 100, "date": "2026-01-15",
                "category_id": cat, "description": "x", "payment_mode": "cash"})
    svc.undo()
    assert svc.undo_redo_status()["redo_available"]
    svc.create({"amount_paise": 200, "date": "2026-01-16",
                "category_id": cat, "description": "y", "payment_mode": "cash"})
    assert not svc.undo_redo_status()["redo_available"]
