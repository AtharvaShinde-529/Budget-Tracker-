"""Roommate settlement service: minimum transactions to zero out net balances."""

from backend.algorithms import greedy


DEMO_PEOPLE = [
    {"name": "Alice", "net_balance_paise":  100000},
    {"name": "Bob",   "net_balance_paise":  -60000},
    {"name": "Carol", "net_balance_paise":  -40000},
    {"name": "Dave",  "net_balance_paise":   50000},
    {"name": "Evan",  "net_balance_paise":  -50000},
]


def settle():
    balances = [(p["name"], p["net_balance_paise"]) for p in DEMO_PEOPLE]
    transactions, stats = greedy.min_transaction_settlement(balances)
    total_amount = sum(abs(p["net_balance_paise"]) for p in DEMO_PEOPLE) // 2
    return {
        "balances": DEMO_PEOPLE,
        "transactions": transactions,
        "transaction_count": len(transactions),
        "total_money_moved_paise": total_amount,
        "stats": stats.as_dict(),
    }
