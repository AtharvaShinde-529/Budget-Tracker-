"""Seed 200 realistic Indian student expenses with planted duplicates and outliers.

Run explicitly:   python -m backend.seed
Or auto-run:      app startup calls seed_if_empty()

Duplicates: 3 pairs of identical amount+category+day (as if logged twice).
Outliers:   2 large one-off purchases (?8,500, ?6,200) that stand out from the
            median of ~?40-?1200 typical expenses, so order-statistics and
            DAA duplicate-detection algorithms have something real to find.
"""

import random
from datetime import datetime, timedelta

from backend.db import get_conn, init_schema, is_empty

CATEGORIES = [
    # (name, color)
    ("Mess",           "#f59e0b"),
    ("Canteen",        "#f97316"),
    ("Chai",           "#eab308"),
    ("Snacks",         "#ef4444"),
    ("Auto",           "#06b6d4"),
    ("Metro",          "#0ea5e9"),
    ("Bus",            "#3b82f6"),
    ("Stationery",     "#8b5cf6"),
    ("Printouts",      "#a855f7"),
    ("Books",          "#d946ef"),
    ("Recharge",       "#10b981"),
    ("Subscriptions",  "#22c55e"),
    ("Health",         "#84cc16"),
    ("Outing",         "#ec4899"),
    ("Misc",           "#94a3b8"),
]

# (description, category_name, min_paise, max_paise, payment_modes, weight)
TEMPLATES = [
    ("Monthly mess bill",        "Mess",           250000, 400000, ["upi"],                         5),
    ("Mess extra",               "Mess",            50000, 100000, ["cash", "upi"],                 3),
    ("Canteen lunch",            "Canteen",         40000, 120000, ["upi", "cash"],                 20),
    ("Canteen breakfast",        "Canteen",         20000,  60000, ["upi", "cash"],                 12),
    ("Chai",                     "Chai",             1000,   3000, ["cash", "upi"],                 40),
    ("Chai with friends",        "Chai",             2000,   6000, ["cash"],                         8),
    ("Samosa",                   "Snacks",           1500,   3000, ["cash"],                        10),
    ("Biscuits",                 "Snacks",           2000,   5000, ["cash", "upi"],                  6),
    ("Puffs",                    "Snacks",           3000,   6000, ["cash"],                         4),
    ("Auto to college",          "Auto",             5000,  15000, ["cash", "upi"],                 15),
    ("Auto to station",          "Auto",            12000,  25000, ["cash", "upi"],                  4),
    ("Metro recharge",           "Metro",           20000,  60000, ["upi"],                         10),
    ("Bus ticket",               "Bus",              1000,   3000, ["cash"],                         8),
    ("Notebook",                 "Stationery",       4000,  15000, ["cash", "upi"],                  5),
    ("Pen refill",               "Stationery",       1000,   3000, ["cash"],                         4),
    ("Printouts",                "Printouts",         500,   3000, ["cash", "upi"],                  8),
    ("Lab manual print",         "Printouts",        5000,  15000, ["cash", "upi"],                  3),
    ("Reference book",           "Books",            20000, 150000, ["card", "upi"],                  3),
    ("Mobile recharge",          "Recharge",         20000,  40000, ["upi", "wallet"],                4),
    ("Spotify subscription",     "Subscriptions",    11900,  11900, ["card"],                          2),
    ("Netflix share",            "Subscriptions",    16600,  16600, ["upi"],                           2),
    ("Netflix full",             "Subscriptions",    49900,  49900, ["card"],                          1),
    ("Cough syrup",              "Health",           5000,  15000, ["cash", "upi"],                  2),
    ("Vitamin D tablets",        "Health",           15000, 40000, ["upi"],                           1),
    ("Movie ticket",             "Outing",           15000, 35000, ["upi", "card"],                  4),
    ("Outing snacks",            "Outing",           10000, 30000, ["cash", "upi"],                  5),
    ("Laundry",                  "Misc",             5000,  15000, ["cash", "upi"],                  3),
    ("Photocopy ID card",        "Printouts",        1000,   3000, ["cash"],                         2),
    ("Room misc",                "Misc",             2000,  10000, ["cash"],                         4),
]


def _weighted_choice(rng):
    total = sum(t[5] for t in TEMPLATES)
    r = rng.uniform(0, total)
    upto = 0
    for t in TEMPLATES:
        upto += t[5]
        if r <= upto:
            return t
    return TEMPLATES[-1]


def _insert_categories(conn):
    for name, color in CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)",
            (name, color),
        )
    name_to_id = {
        row["name"]: row["id"]
        for row in conn.execute("SELECT id, name FROM categories").fetchall()
    }
    return name_to_id


def _build_expenses(rng, name_to_id, n=200, days_back=90):
    """Return list of dicts to insert. Includes planted duplicates & outliers."""
    now = datetime.now()
    start = now - timedelta(days=days_back)

    rows = []
    for _ in range(n):
        desc, cat, lo, hi, modes, _ = _weighted_choice(rng)
        # Bias amounts toward the lower end so a few big spends stand out
        amount = rng.randint(lo, hi)
        if rng.random() < 0.15:
            amount = rng.randint(lo, (lo + hi) // 2)  # more cheap days

        # Random day in the window, biased toward recent
        offset = int(days_back * (rng.random() ** 0.7))
        day = start + timedelta(days=offset)
        # College hours
        hour = rng.randint(8, 22)
        minute = rng.randint(0, 59)
        when = day.replace(hour=hour, minute=minute, second=rng.randint(0, 59))
        iso = when.strftime("%Y-%m-%d")

        rows.append({
            "amount_paise": amount,
            "date": iso,
            "category_id": name_to_id[cat],
            "description": desc,
            "payment_mode": rng.choice(modes),
            "created_at": when.strftime("%Y-%m-%dT%H:%M:%S"),
        })

    # --- Plant 3 duplicate pairs (same amount, same cat, same day) ---
    duplicate_source_idx = [10, 55, 120]
    for i, idx in enumerate(duplicate_source_idx):
        src = dict(rows[idx])
        # Same amount, same category, same day ? clearly a double-entry
        rows.append({
            "amount_paise": src["amount_paise"],
            "date": src["date"],
            "category_id": src["category_id"],
            "description": src["description"] + " (possibly duplicate)",
            "payment_mode": src["payment_mode"],
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        })

    # --- Plant 2 outliers (much larger than typical) ---
    outlier_today = (now - timedelta(days=5)).strftime("%Y-%m-%d")
    rows.append({
        "amount_paise": 850000,  # ?8,500
        "date": outlier_today,
        "category_id": name_to_id["Misc"],
        "description": "Replaced broken laptop charger",
        "payment_mode": "card",
        "created_at": outlier_today + "T16:30:00",
    })
    rows.append({
        "amount_paise": 620000,  # ?6,200
        "date": (now - timedelta(days=18)).strftime("%Y-%m-%d"),
        "category_id": name_to_id["Health"],
        "description": "Dental treatment",
        "payment_mode": "upi",
        "created_at": (now - timedelta(days=18)).strftime("%Y-%m-%dT11:00:00"),
    })

    return rows


def seed(force: bool = False) -> int:
    """Insert seed data. If force=False, only seeds when the table is empty.

    Returns number of expense rows inserted.
    """
    init_schema()
    if not force and not is_empty():
        return 0

    rng = random.Random(20260214)
    with get_conn() as conn:
        if force:
            conn.execute("DELETE FROM expenses")
            conn.execute("DELETE FROM categories")
            conn.execute("DELETE FROM action_log")
        name_to_id = _insert_categories(conn)
        rows = _build_expenses(rng, name_to_id, n=200, days_back=90)
        conn.executemany(
            "INSERT INTO expenses (amount_paise, date, category_id, description, payment_mode, created_at) "
            "VALUES (:amount_paise, :date, :category_id, :description, :payment_mode, :created_at)",
            rows,
        )
    return len(rows)


def main():
    n = seed(force=True)
    print(f"Seeded {n} expenses.")


if __name__ == "__main__":
    main()
