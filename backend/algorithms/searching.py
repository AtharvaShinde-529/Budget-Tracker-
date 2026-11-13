"""All searching algorithms, hand-written. No bisect."""

from backend.instrumentation import Stats


def linear_search(arr, target, stats=None):
    stats = stats or Stats()
    for i, x in enumerate(arr):
        stats.comparisons += 1
        if x == target:
            return i, stats
    return -1, stats


def lower_bound(arr, target, stats=None):
    """First index with arr[i] >= target. Requires arr sorted ascending."""
    stats = stats or Stats()
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        stats.comparisons += 1
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo, stats


def upper_bound(arr, target, stats=None):
    """First index with arr[i] > target."""
    stats = stats or Stats()
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        stats.comparisons += 1
        if arr[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo, stats


def binary_search(arr, target, stats=None):
    stats = stats or Stats()
    idx, stats = lower_bound(arr, target, stats)
    if idx < len(arr):
        stats.comparisons += 1
        if arr[idx] == target:
            return idx, stats
    return -1, stats


def range_indices(arr, lo_val, hi_val, stats=None):
    """Half-open interval [lo_val, hi_val) over sorted arr. O(log n) to locate."""
    stats = stats or Stats()
    left, stats = lower_bound(arr, lo_val, stats)
    right, stats = lower_bound(arr, hi_val, stats)
    return left, right, stats
