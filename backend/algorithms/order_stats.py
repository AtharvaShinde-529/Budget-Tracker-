"""Order statistics: quickselect, median of medians, percentiles, IQR outliers.

Rule: no built-in sort, no heapq. Every function returns (result, Stats).
"""

import random

from backend.instrumentation import Stats


def randomized_quickselect(arr, k, stats=None, rng=None):
    """Return the k-th smallest element (0-indexed). Expected O(n)."""
    stats = stats or Stats()
    rng = rng or random.Random()
    a = list(arr)
    if not 0 <= k < len(a):
        raise IndexError(f"k={k} out of range for length {len(a)}")
    lo, hi = 0, len(a) - 1
    while lo < hi:
        stats.calls += 1
        p = rng.randint(lo, hi)
        pivot = a[p]
        # 3-way partition
        lt, i, gt = lo, lo, hi
        while i <= gt:
            stats.comparisons += 1
            if a[i] < pivot:
                a[lt], a[i] = a[i], a[lt]; lt += 1; i += 1
            elif a[i] > pivot:
                a[i], a[gt] = a[gt], a[i]; gt -= 1
            else:
                i += 1
        if k < lt:
            hi = lt - 1
        elif k > gt:
            lo = gt + 1
        else:
            return a[k], stats
    return a[lo], stats


def median_of_medians(arr, k, stats=None):
    """Deterministic O(n) selection. Groups of 5."""
    stats = stats or Stats()
    a = list(arr)
    if not 0 <= k < len(a):
        raise IndexError(f"k={k} out of range for length {len(a)}")
    return _mom(a, 0, len(a) - 1, k, stats)


def _mom(a, lo, hi, k, stats):
    stats.enter()
    try:
        while lo < hi:
            # 1. Find median of each group of 5
            n_groups = (hi - lo + 1 + 4) // 5
            medians = []
            for g in range(n_groups):
                g_lo = lo + g * 5
                g_hi = min(g_lo + 5, hi + 1)
                group = a[g_lo:g_hi]
                # insertion sort the 5-element group
                for i in range(1, len(group)):
                    key = group[i]
                    j = i - 1
                    while j >= 0:
                        stats.comparisons += 1
                        if group[j] > key:
                            group[j + 1] = group[j]; j -= 1
                        else:
                            break
                    group[j + 1] = key
                medians.append(group[len(group) // 2])

            # 2. Recursively find median of the medians
            mom, _ = _mom(medians, 0, len(medians) - 1, len(medians) // 2, stats)

            # 3. Partition around mom
            lt, i, gt = lo, lo, hi
            while i <= gt:
                stats.comparisons += 1
                if a[i] < mom:
                    a[lt], a[i] = a[i], a[lt]; lt += 1; i += 1
                elif a[i] > mom:
                    a[i], a[gt] = a[gt], a[i]; gt -= 1
                else:
                    i += 1

            if k < lt:
                hi = lt - 1
            elif k > gt:
                lo = gt + 1
            else:
                return a[k], stats
        return a[lo], stats
    finally:
        stats.exit()


def median(arr, stats=None, method="randomized"):
    """Median of an array. Method: 'randomized' (quickselect) or 'mom' (MoM)."""
    stats = stats or Stats()
    n = len(arr)
    if n == 0:
        raise ValueError("median of empty array")
    if n % 2 == 1:
        fn = randomized_quickselect if method == "randomized" else median_of_medians
        return fn(arr, n // 2, stats)[0], stats
    fn = randomized_quickselect if method == "randomized" else median_of_medians
    a, _ = fn(arr, n // 2 - 1, stats)
    b, _ = fn(arr, n // 2, stats)
    return (a + b) / 2.0, stats


def percentile(arr, p, stats=None, method="randomized"):
    """Linear-interpolation percentile. p in [0, 100]."""
    stats = stats or Stats()
    n = len(arr)
    if n == 0:
        raise ValueError("percentile of empty array")
    if not 0 <= p <= 100:
        raise ValueError(f"p must be in [0,100], got {p}")
    # rank = p/100 * (n - 1)
    rank = (p / 100.0) * (n - 1)
    lo_rank = int(rank)
    hi_rank = min(lo_rank + 1, n - 1)
    fn = randomized_quickselect if method == "randomized" else median_of_medians
    lo_val, _ = fn(arr, lo_rank, stats)
    hi_val, _ = fn(arr, hi_rank, stats)
    frac = rank - lo_rank
    return lo_val + (hi_val - lo_val) * frac, stats


def quartiles(arr, stats=None, method="randomized"):
    """Return (Q1, Q2, Q3) as (25th, 50th, 75th percentile)."""
    stats = stats or Stats()
    q1, _ = percentile(arr, 25, stats, method)
    q2, _ = percentile(arr, 50, stats, method)
    q3, _ = percentile(arr, 75, stats, method)
    return (q1, q2, q3), stats


def iqr_outliers(arr, factor=1.5, stats=None):
    """Return list of (index, value) for values outside Q1-factor*IQR, Q3+factor*IQR."""
    stats = stats or Stats()
    if len(arr) < 4:
        return [], stats
    (q1, _, q3), _ = quartiles(arr, stats)
    iqr = q3 - q1
    low = q1 - factor * iqr
    high = q3 + factor * iqr
    outliers = [(i, v) for i, v in enumerate(arr) if v < low or v > high]
    stats.extra = {"q1": q1, "q3": q3, "iqr": iqr, "fence_low": low, "fence_high": high}
    return outliers, stats


def top_k(arr, k, stats=None):
    """Top k largest values, in descending order, via repeated quickselect."""
    stats = stats or Stats()
    if k <= 0 or k > len(arr):
        k = min(max(k, 0), len(arr))
    a = list(arr)
    n = len(a)
    result = []
    for j in range(k):
        v, _ = randomized_quickselect(a, n - 1 - j, stats)
        result.append(v)
    return result, stats
