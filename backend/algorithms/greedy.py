"""Greedy algorithms. Hand-written sorts and heaps only.

All functions return (result, Stats).
"""

from backend.algorithms.sorting import merge_sort
from backend.algorithms.structures import MinHeap
from backend.instrumentation import Stats


INDIAN_DENOMINATIONS_PAISE = [
    50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100,
    50, 20, 10, 5, 2, 1,
]


def fractional_knapsack(items, capacity_paise, stats=None):
    """Fractional knapsack. Items: {name, weight_paise, value}.
    Sort key is (-value/weight, index) so ties never compare dicts.
    """
    stats = stats or Stats()
    if capacity_paise <= 0 or not items:
        return [], stats

    decorated = []
    for i, it in enumerate(items):
        w = it["weight_paise"]
        ratio = it["value"] / w if w > 0 else float("inf")
        decorated.append((-ratio, i, it))

    sorted_items, s = merge_sort(decorated)
    stats.comparisons += s.comparisons
    stats.swaps += s.swaps
    stats.calls += s.calls

    remaining = capacity_paise
    picked = []
    for _, _, it in sorted_items:
        if remaining <= 0:
            break
        w = it["weight_paise"]
        v = it["value"]
        if w <= remaining:
            picked.append({"name": it["name"],
                           "weight_taken_paise": w,
                           "value_taken": v,
                           "fraction": 1.0})
            remaining -= w
        else:
            frac = remaining / w
            picked.append({"name": it["name"],
                           "weight_taken_paise": remaining,
                           "value_taken": v * frac,
                           "fraction": frac})
            remaining = 0
    return picked, stats


def job_sequencing_with_deadlines(jobs, stats=None):
    """Job sequencing with deadlines. Sort by (-penalty, index)."""
    stats = stats or Stats()
    if not jobs:
        return [], stats

    decorated = [(-j["penalty_paise"], i, j) for i, j in enumerate(jobs)]
    sorted_jobs, s = merge_sort(decorated)
    stats.comparisons += s.comparisons

    max_deadline = max(j["deadline_day"] for j in jobs)
    if max_deadline <= 0:
        return [], stats

    parent = list(range(max_deadline + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    scheduled = []
    for _, _, j in sorted_jobs:
        d = min(j["deadline_day"], max_deadline)
        slot = find(d)
        if slot != 0:
            scheduled.append({"slot": slot,
                              "name": j["name"],
                              "deadline_day": j["deadline_day"],
                              "penalty_paise": j["penalty_paise"]})
            parent[slot] = find(slot - 1)

    # Final sort by (slot, index) ? index breaks ties on the int side.
    decorated_sched = [(s["slot"], i, s) for i, s in enumerate(scheduled)]
    sorted_sched, _ = merge_sort(decorated_sched)
    return [t[2] for t in sorted_sched], stats


def coin_change_greedy(amount_paise, denominations=None, stats=None):
    """Greedy coin/note change. Correct for canonical systems (e.g. INR)."""
    stats = stats or Stats()
    denominations = denominations or INDIAN_DENOMINATIONS_PAISE
    if amount_paise < 0:
        raise ValueError("amount must be non-negative")

    decorated = [(-d, i, d) for i, d in enumerate(denominations)]
    sorted_denoms, _ = merge_sort(decorated)
    denoms = [t[2] for t in sorted_denoms]

    remaining = amount_paise
    breakdown = {}
    for d in denoms:
        if remaining <= 0:
            break
        count = remaining // d
        if count > 0:
            breakdown[d] = count
            remaining -= count * d
            stats.comparisons += 1
    return breakdown, stats


def min_transaction_settlement(balances, stats=None):
    """Minimum-transaction settlement using two MaxHeaps."""
    stats = stats or Stats()
    creditors = MinHeap(key=lambda x: -x[0])
    debtors = MinHeap(key=lambda x: -x[0])
    for name, net in balances:
        stats.comparisons += 1
        if net > 0:
            creditors.push((net, name))
        elif net < 0:
            debtors.push((-net, name))

    transactions = []
    while len(creditors) and len(debtors):
        c_amt, c_name = creditors.pop()
        d_amt, d_name = debtors.pop()
        transfer = c_amt if c_amt < d_amt else d_amt
        transactions.append({"from": d_name, "to": c_name, "amount_paise": transfer})
        stats.swaps += 1
        rem_c = c_amt - transfer
        rem_d = d_amt - transfer
        if rem_c > 0:
            creditors.push((rem_c, c_name))
        if rem_d > 0:
            debtors.push((rem_d, d_name))
    return transactions, stats


def interval_scheduling(intervals, stats=None):
    """Maximum-count non-overlapping intervals. Sort by (end, start, id)."""
    stats = stats or Stats()
    if not intervals:
        return [], stats

    decorated = [(iv["end"], iv["start"], iv["id"]) for iv in intervals]
    sorted_ivs, s = merge_sort(decorated)
    stats.comparisons += s.comparisons

    selected = []
    last_end = None
    for end, start, iv_id in sorted_ivs:
        stats.comparisons += 1
        if last_end is None or start >= last_end:
            selected.append(iv_id)
            last_end = end
    return selected, stats
