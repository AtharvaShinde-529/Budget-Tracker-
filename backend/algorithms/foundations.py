"""Foundations: adversary lower bound, master theorem, coverage helpers.

Hand-written ? no itertools, no sorted() on data (only on integer counters
for reporting, which the AST guard allows via math.factorial logic below).
"""

import math

from backend.algorithms import sorting


def _permutations(items):
    """Hand-written permutation generator (Heap's algorithm). No itertools."""
    a = list(items)
    n = len(a)
    c = [0] * n
    yield tuple(a)
    i = 0
    while i < n:
        if c[i] < i:
            if i % 2 == 0:
                a[0], a[i] = a[i], a[0]
            else:
                a[c[i]], a[i] = a[i], a[c[i]]
            yield tuple(a)
            c[i] += 1
            i = 0
        else:
            c[i] = 0
            i += 1


def adversary_sorting_lab(n):
    """Empirically demonstrate the comparison-sorting lower bound.

    For every permutation of n distinct items, run merge_sort with a
    comparison counter. The minimum comparisons any comparison-sort family
    can use worst-case is ?log?(n!)?. merge_sort's worst case will be near
    that bound for small n.
    """
    counts = []
    for perm in _permutations(range(n)):
        data = list(perm)
        _, stats = sorting.merge_sort(data)
        counts.append(stats.comparisons)

    n_fact = math.factorial(n)
    log2_nfact = math.log2(n_fact) if n_fact > 0 else 0.0
    lower_bound = math.ceil(log2_nfact) if log2_nfact > 0 else 0

    # Report sorted counters (integer sort is fine ? guard bans sorted on
    # ALGORITHM data, not on results we build here for the report).
    counts_sorted = _msort_ints(counts)
    mean = sum(counts) / len(counts) if counts else 0

    return {
        "n": n,
        "n_factorial": n_fact,
        "log2_n_factorial": round(log2_nfact, 4),
        "lower_bound_ceil": lower_bound,
        "min_comparisons": counts_sorted[0] if counts_sorted else 0,
        "mean_comparisons": round(mean, 2),
        "median_comparisons": counts_sorted[len(counts_sorted) // 2] if counts_sorted else 0,
        "max_comparisons": counts_sorted[-1] if counts_sorted else 0,
        "ratio_mean_over_bound": round(mean / lower_bound, 4) if lower_bound else None,
        "permutation_count": len(counts),
    }


def _msort_ints(xs):
    """Tiny local integer merge sort to avoid tripping the banned-sorted guard."""
    if len(xs) < 2:
        return list(xs)
    mid = len(xs) // 2
    left = _msort_ints(xs[:mid])
    right = _msort_ints(xs[mid:])
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def master_theorem(a, b, d):
    """Solve T(n) = a?T(n/b) + ?(n^d) via the Master theorem."""
    if a <= 0 or b <= 1:
        raise ValueError("require a > 0 and b > 1")

    log_b_a = math.log(a, b)

    if abs(log_b_a - d) < 1e-9:
        case = 2
        teta = f"?(n^{d} ? log n)" if d != 0 else "?(log n)"
        expl = (f"log_b(a) = log_{b}({a}) = {log_b_a:.4f} = d, "
                f"so the tree is balanced and a log factor appears.")
    elif log_b_a > d:
        case = 1
        teta = f"?(n^{log_b_a:.4f})"
        expl = (f"log_b(a) = {log_b_a:.4f} > d = {d}, "
                f"recursion dominates ? leaves drive the total cost.")
    else:
        case = 3
        teta = f"?(n^{d})"
        expl = (f"log_b(a) = {log_b_a:.4f} < d = {d}, "
                f"combine step dominates ? recursion is cheap.")

    return {
        "a": a, "b": b, "d": d,
        "log_b_a": round(log_b_a, 6),
        "case": case,
        "teta": teta,
        "explanation": expl,
    }


PRESET_RECURRENCES = [
    {"name": "Merge sort",     "a": 2, "b": 2, "d": 1, "formula": "T(n) = 2T(n/2) + ?(n)"},
    {"name": "Binary search",  "a": 1, "b": 2, "d": 0, "formula": "T(n) = T(n/2) + ?(1)"},
    {"name": "Karatsuba",      "a": 3, "b": 2, "d": 1, "formula": "T(n) = 3T(n/2) + ?(n)"},
    {"name": "Strassen",       "a": 7, "b": 2, "d": 2, "formula": "T(n) = 7T(n/2) + ?(n?)"},
    {"name": "Closest pair",   "a": 2, "b": 2, "d": 1, "formula": "T(n) = 2T(n/2) + ?(n)"},
    {"name": "Naive matrix",   "a": 8, "b": 2, "d": 2, "formula": "T(n) = 8T(n/2) + ?(n?)"},
]
