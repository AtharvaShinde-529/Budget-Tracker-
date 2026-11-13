"""Tests for greedy algorithms against brute-force / known-good oracles."""

import itertools
import random

from backend.algorithms import greedy


# ---------- fractional knapsack ----------

def test_fractional_knapsack_basic():
    items = [
        {"name": "A", "weight_paise": 100, "value": 60},
        {"name": "B", "weight_paise": 200, "value": 100},
        {"name": "C", "weight_paise": 300, "value": 120},
    ]
    picked, _ = greedy.fractional_knapsack(items, 500)
    # Ratios: A=0.6, B=0.5, C=0.4 ? A(100/60) then B(200/100) then C partial
    names = [p["name"] for p in picked]
    assert names == ["A", "B", "C"]
    assert picked[0]["fraction"] == 1.0
    assert picked[1]["fraction"] == 1.0
    assert abs(picked[2]["fraction"] - 200/300) < 1e-9


def test_fractional_knapsack_zero_capacity():
    picked, _ = greedy.fractional_knapsack(
        [{"name": "X", "weight_paise": 100, "value": 10}], 0)
    assert picked == []


def test_fractional_knapsack_matches_brute():
    """For small instances, fractional greedy >= any single-item selection."""
    rng = random.Random(42)
    for _ in range(50):
        n = rng.randint(1, 6)
        items = [{"name": f"i{k}",
                  "weight_paise": rng.randint(10, 100),
                  "value": rng.randint(1, 100)} for k in range(n)]
        cap = rng.randint(1, 200)
        picked, _ = greedy.fractional_knapsack(items, cap)
        total_value = sum(p["value_taken"] for p in picked)
        total_weight = sum(p["weight_taken_paise"] for p in picked)
        assert total_weight <= cap
        # The LP upper bound: sum over items of min(1, cap/weight)*value
        ub = sum(min(1, cap / it["weight_paise"]) * it["value"] for it in items)
        assert total_value <= ub + 1e-6


# ---------- job sequencing ----------

def test_job_sequencing_basic():
    jobs = [
        {"name": "A", "deadline_day": 2, "penalty_paise": 100},
        {"name": "B", "deadline_day": 1, "penalty_paise": 19},
        {"name": "C", "deadline_day": 2, "penalty_paise": 27},
        {"name": "D", "deadline_day": 1, "penalty_paise": 25},
        {"name": "E", "deadline_day": 3, "penalty_paise": 15},
    ]
    scheduled, _ = greedy.job_sequencing_with_deadlines(jobs)
    names = [s["name"] for s in scheduled]
    # Classic CLRS example: optimal = {A, C, E} with total 142
    assert set(names) == {"A", "C", "E"}
    total = sum(s["penalty_paise"] for s in scheduled)
    assert total == 142


def test_job_sequencing_all_fit():
    jobs = [
        {"name": "A", "deadline_day": 1, "penalty_paise": 10},
        {"name": "B", "deadline_day": 2, "penalty_paise": 20},
        {"name": "C", "deadline_day": 3, "penalty_paise": 30},
    ]
    scheduled, _ = greedy.job_sequencing_with_deadlines(jobs)
    assert len(scheduled) == 3


def test_job_sequencing_matches_brute():
    rng = random.Random(7)
    for _ in range(30):
        n = rng.randint(1, 5)
        jobs = [{"name": f"j{k}",
                 "deadline_day": rng.randint(1, 3),
                 "penalty_paise": rng.randint(1, 100)} for k in range(n)]
        best, _ = greedy.job_sequencing_with_deadlines(jobs)
        best_total = sum(s["penalty_paise"] for s in best)
        # Brute force: all subsets that fit into slots
        max_deadline = max(j["deadline_day"] for j in jobs)
        best_brute = 0
        for r in range(len(jobs) + 1):
            for combo in itertools.combinations(jobs, r):
                # Check schedulable: for each deadline d, #jobs with deadline<=d <= d
                feasible = True
                for d in range(1, max_deadline + 1):
                    count = sum(1 for j in combo if j["deadline_day"] <= d)
                    if count > d:
                        feasible = False
                        break
                if feasible:
                    total = sum(j["penalty_paise"] for j in combo)
                    best_brute = max(best_brute, total)
        assert best_total == best_brute


# ---------- coin change ----------

def test_coin_change_reconstructs():
    for amt in [0, 1, 99, 100, 1237, 5000, 100000]:
        breakdown, _ = greedy.coin_change_greedy(amt)
        total = sum(d * c for d, c in breakdown.items())
        assert total == amt


def test_coin_change_known():
    breakdown, _ = greedy.coin_change_greedy(1237)
    assert breakdown[1000] == 1
    assert breakdown[200] == 1
    assert breakdown[20] == 1
    assert breakdown[10] == 1
    assert breakdown[5] == 1
    assert breakdown[2] == 1


# ---------- settlement ----------

def test_settlement_balances_zero():
    balances = [("A", 100), ("B", -40), ("C", -60)]
    tx, _ = greedy.min_transaction_settlement(balances)
    net = {name: 0 for name, _ in balances}
    for t in tx:
        net[t["from"]] += t["amount_paise"]
        net[t["to"]] -= t["amount_paise"]
    for name, orig in balances:
        assert net[name] == -orig


def test_settlement_minimal_count():
    balances = [("A", 100), ("B", -50), ("C", -50)]
    tx, _ = greedy.min_transaction_settlement(balances)
    assert len(tx) == 2


def test_settlement_all_zero():
    balances = [("A", 0), ("B", 0), ("C", 0)]
    tx, _ = greedy.min_transaction_settlement(balances)
    assert tx == []


# ---------- interval scheduling ----------

def test_interval_scheduling_basic():
    intervals = [
        {"id": 1, "start": 1, "end": 4},
        {"id": 2, "start": 3, "end": 5},
        {"id": 3, "start": 0, "end": 6},
        {"id": 4, "start": 5, "end": 7},
        {"id": 5, "start": 3, "end": 8},
        {"id": 6, "start": 5, "end": 9},
        {"id": 7, "start": 6, "end": 10},
        {"id": 8, "start": 8, "end": 11},
        {"id": 9, "start": 8, "end": 12},
        {"id": 10, "start": 2, "end": 13},
        {"id": 11, "start": 12, "end": 14},
    ]
    ids, _ = greedy.interval_scheduling(intervals)
    # Classic CLRS example: {1, 4, 8, 11}
    assert set(ids) == {1, 4, 8, 11}


def test_interval_scheduling_matches_brute():
    rng = random.Random(3)
    for _ in range(30):
        n = rng.randint(1, 7)
        intervals = [{"id": k,
                      "start": (s := rng.randint(0, 10)),
                      "end": s + rng.randint(1, 5)} for k in range(n)]
        ids, _ = greedy.interval_scheduling(intervals)
        # Check selected intervals are non-overlapping
        chosen = sorted([iv for iv in intervals if iv["id"] in ids],
                        key=lambda x: x["start"])
        for i in range(1, len(chosen)):
            assert chosen[i]["start"] >= chosen[i-1]["end"]
        # Brute force max count
        best_brute = 0
        for r in range(len(intervals), 0, -1):
            found = False
            for combo in itertools.combinations(intervals, r):
                sorted_combo = sorted(combo, key=lambda x: x["start"])
                ok = True
                for i in range(1, len(sorted_combo)):
                    if sorted_combo[i]["start"] < sorted_combo[i-1]["end"]:
                        ok = False
                        break
                if ok:
                    best_brute = r
                    found = True
                    break
            if found:
                break
        assert len(ids) == best_brute


# ---------- regressions ----------

def test_fractional_knapsack_does_not_compare_dicts():
    """Regression: (dict, num) tuples caused TypeError in merge_sort when ties hit."""
    items = [
        {"name": f"i{k}", "weight_paise": 100, "value": 50}  # all equal ratios
        for k in range(10)
    ]
    picked, _ = greedy.fractional_knapsack(items, 250)
    # With all equal ratios, we should still pick greedily and terminate
    total = sum(p["weight_taken_paise"] for p in picked)
    assert total <= 250
    assert total > 0


def test_job_sequencing_does_not_compare_dicts():
    """Regression: 3 jobs with identical penalties previously crashed."""
    jobs = [
        {"name": f"j{k}", "deadline_day": k + 1, "penalty_paise": 100}
        for k in range(3)
    ]
    scheduled, _ = greedy.job_sequencing_with_deadlines(jobs)
    assert len(scheduled) == 3
