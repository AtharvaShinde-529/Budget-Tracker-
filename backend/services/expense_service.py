"""Expense service: CRUD + hand-written sort + binary range search + undo/redo.

Business rules enforced here (not in routes, not in algorithms):
  - Money always integer paise.
  - Every mutation pushes a (do, undo) pair onto the undo stack.
  - Undo applies the "undo" op, redo applies the "do" op. No ambiguity.
  - New actions clear the redo stack.
  - Sorting goes through backend.algorithms.sorting, never Python's sorted().
  - Range search uses lower_bound / upper_bound after sorting by date.
"""

from datetime import datetime

from backend.algorithms import searching, sorting
from backend.algorithms.structures import Stack


SORT_FUNCS = {
    "insertion_sort": sorting.insertion_sort,
    "selection_sort": sorting.selection_sort,
    "bubble_sort":    sorting.bubble_sort,
    "merge_sort":     sorting.merge_sort,
    "quick_sort":     sorting.quick_sort,
    "heap_sort":      sorting.heap_sort,
    "counting_sort":  sorting.counting_sort,
    "radix_sort":     sorting.radix_sort,
}
# Non-comparison sorts (counting, radix) need raw integer keys, not tuples.
NON_COMPARISON_SORTS = {"counting_sort", "radix_sort"}


class _Rev:
    """Reverse-comparison wrapper used to sort descending while preserving stability."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __lt__(self, o):  return self.v > o.v
    def __gt__(self, o):  return self.v < o.v
    def __le__(self, o):  return self.v >= o.v
    def __ge__(self, o):  return self.v <= o.v
    def __eq__(self, o):  return self.v == o.v
    def __hash__(self):   return hash(("_Rev", self.v))


class ExpenseService:
    FIELDS = ("amount_paise", "date", "category_id", "description", "payment_mode")

    def __init__(self, conn):
        self.conn = conn
        self.undo_stack = Stack()
        self.redo_stack = Stack()

    # ---------- reads ----------

    def list_categories(self):
        rows = self.conn.execute(
            "SELECT id, name, color, monthly_limit_paise FROM categories ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    def _fetch_all(self):
        sql = """
        SELECT e.id, e.amount_paise, e.date, e.category_id,
               c.name AS category_name, c.color AS category_color,
               e.description, e.payment_mode, e.created_at
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        """
        return [dict(r) for r in self.conn.execute(sql).fetchall()]

    def list_sorted(self, field="date", order="asc", algorithm="merge_sort"):
        rows = self._fetch_all()

        fn = SORT_FUNCS.get(algorithm)
        if fn is None:
            raise ValueError(f"unknown algorithm: {algorithm}")

        descending = order == "desc"

        # Non-comparison sorts (counting, radix) need raw integer keys.
        # Only amount_paise qualifies; reject other fields with a clear message.
        if algorithm in NON_COMPARISON_SORTS:
            if field != "amount_paise":
                raise ValueError(
                    f"{algorithm} sorts integer keys only; use field='amount_paise' "
                    f"(got field='{field}'). For strings/dates use a comparison sort."
                )
            amounts = [r["amount_paise"] for r in rows]
            sorted_amounts, stats = fn(amounts)
            if descending:
                sorted_amounts = sorted_amounts[::-1]
            by_amount = {}
            for r in rows:
                by_amount.setdefault(r["amount_paise"], []).append(r)
            out_rows = [by_amount[amt].pop() for amt in sorted_amounts]
            return out_rows, {
                "algorithm": algorithm,
                "comparisons": stats.comparisons,
                "swaps": stats.swaps,
                "calls": stats.calls,
                "max_depth": stats.max_depth,
            }, field, order

        # Comparison sorts: (key, index, row) tuples preserve stability.
        key_fn = {
            "date":          lambda r: r["date"],
            "amount_paise":  lambda r: r["amount_paise"],
            "category_name": lambda r: r["category_name"],
            "description":   lambda r: r["description"].lower(),
        }[field]

        keyed = [
            ((_Rev(key_fn(r)) if descending else key_fn(r)), i, r)
            for i, r in enumerate(rows)
        ]
        sorted_keyed, stats = fn(keyed)
        out_rows = [t[2] for t in sorted_keyed]

        return out_rows, {
            "algorithm": algorithm,
            "comparisons": stats.comparisons,
            "swaps": stats.swaps,
            "calls": stats.calls,
            "max_depth": stats.max_depth,
        }, field, order

    def search_range(self, from_date=None, to_date=None, keyword=""):
        rows = self._fetch_all()
        rows_by_date, _ = sorting.merge_sort(
            [(r["date"], i, r) for i, r in enumerate(rows)]
        )
        sorted_dates = [t[0] for t in rows_by_date]
        sorted_rows = [t[2] for t in rows_by_date]

        total_cmp = 0
        lo = 0
        hi = len(sorted_dates)
        if from_date:
            lo, s = searching.lower_bound(sorted_dates, from_date)
            total_cmp += s.comparisons
        if to_date:
            hi, s = searching.lower_bound(sorted_dates, to_date + "\uffff")
            total_cmp += s.comparisons

        window = sorted_rows[lo:hi]
        if keyword:
            kw = keyword.lower()
            window = [
                r for r in window
                if kw in r["description"].lower() or kw in r["category_name"].lower()
            ]
        return window, total_cmp

    def autocomplete(self, prefix, limit=8):
        from backend.algorithms.structures import Trie
        trie = Trie()
        for row in self.conn.execute("SELECT description FROM expenses").fetchall():
            if row["description"]:
                trie.insert(row["description"])
        return trie.startswith(prefix, limit=limit)

    # ---------- internal helpers ----------

    def _row_fields(self, expense_id):
        row = self.conn.execute(
            "SELECT amount_paise, date, category_id, description, payment_mode "
            "FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
        return dict(row) if row else None

    def _apply_op(self, op):
        """Apply one primitive operation. op is one of:
          - {"op": "delete",         "expense_id": int}
          - {"op": "restore",        "expense_id": int, "fields": {...}}
          - {"op": "insert_with_id", "id": int,         "fields": {...}}
        """
        kind = op["op"]
        if kind == "delete":
            self.conn.execute("DELETE FROM expenses WHERE id = ?", (op["expense_id"],))
        elif kind == "restore":
            sets = ", ".join(f"{k} = ?" for k in op["fields"])
            self.conn.execute(
                f"UPDATE expenses SET {sets} WHERE id = ?",
                list(op["fields"].values()) + [op["expense_id"]],
            )
        elif kind == "insert_with_id":
            f = op["fields"]
            self.conn.execute(
                "INSERT INTO expenses "
                "(id, amount_paise, date, category_id, description, payment_mode, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (op["id"], f["amount_paise"], f["date"], f["category_id"],
                 f["description"], f["payment_mode"],
                 datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
            )
        else:
            raise ValueError(f"unknown op {kind}")

    def _push_action(self, do, undo):
        self.undo_stack.push({"do": do, "undo": undo})
        while self.redo_stack:
            self.redo_stack.pop()

    # ---------- mutations ----------

    def create(self, payload):
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        cur = self.conn.execute(
            "INSERT INTO expenses "
            "(amount_paise, date, category_id, description, payment_mode, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (payload["amount_paise"], payload["date"], payload["category_id"],
             payload.get("description", ""), payload.get("payment_mode", "cash"), now),
        )
        new_id = cur.lastrowid
        fields = self._row_fields(new_id)
        self._push_action(
            do={"op": "insert_with_id", "id": new_id, "fields": fields},
            undo={"op": "delete", "expense_id": new_id},
        )
        return new_id

    def update(self, expense_id, payload):
        old_fields = self._row_fields(expense_id)
        if old_fields is None:
            raise ValueError(f"expense {expense_id} not found")

        sets, values = [], []
        for k in self.FIELDS:
            if payload.get(k) is not None:
                sets.append(f"{k} = ?")
                values.append(payload[k])
        if not sets:
            return

        values.append(expense_id)
        self.conn.execute(f"UPDATE expenses SET {', '.join(sets)} WHERE id = ?", values)

        new_fields = self._row_fields(expense_id)
        self._push_action(
            do={"op": "restore", "expense_id": expense_id, "fields": new_fields},
            undo={"op": "restore", "expense_id": expense_id, "fields": old_fields},
        )

    def delete(self, expense_id):
        old_fields = self._row_fields(expense_id)
        if old_fields is None:
            raise ValueError(f"expense {expense_id} not found")
        self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        self._push_action(
            do={"op": "delete", "expense_id": expense_id},
            undo={"op": "insert_with_id", "id": expense_id, "fields": old_fields},
        )

    # ---------- undo / redo ----------

    def undo(self):
        if not self.undo_stack:
            raise ValueError("nothing to undo")
        entry = self.undo_stack.pop()
        self._apply_op(entry["undo"])
        self.redo_stack.push(entry)

    def redo(self):
        if not self.redo_stack:
            raise ValueError("nothing to redo")
        entry = self.redo_stack.pop()
        self._apply_op(entry["do"])
        self.undo_stack.push(entry)

    def undo_redo_status(self):
        return {
            "undo_depth": len(self.undo_stack),
            "redo_depth": len(self.redo_stack),
            "undo_available": bool(self.undo_stack),
            "redo_available": bool(self.redo_stack),
        }

