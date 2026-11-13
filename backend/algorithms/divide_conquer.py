"""Divide-and-conquer analytics: inversions, max-subarray, majority, closest pair."""

import math

from backend.instrumentation import Stats


# ---------- Inversion count (Kendall-tau-style distance) ----------

def inversion_count(arr, stats=None):
    """Count pairs (i,j) with i<j and arr[i] > arr[j]. O(n log n) via merge sort."""
    stats = stats or Stats()
    a = list(arr)
    if len(a) < 2:
        return 0, stats
    buf = [0] * len(a)
    inv = _ms_count(a, 0, len(a), buf, stats)
    return inv, stats


def _ms_count(a, lo, hi, buf, stats):
    stats.enter()
    try:
        if hi - lo < 2:
            return 0
        mid = (lo + hi) // 2
        inv = _ms_count(a, lo, mid, buf, stats)
        inv += _ms_count(a, mid, hi, buf, stats)
        i, j, k = lo, mid, lo
        while i < mid and j < hi:
            stats.comparisons += 1
            if a[i] <= a[j]:
                buf[k] = a[i]; i += 1
            else:
                buf[k] = a[j]; j += 1
                inv += mid - i
            k += 1
        while i < mid:
            buf[k] = a[i]; i += 1; k += 1
        while j < hi:
            buf[k] = a[j]; j += 1; k += 1
        a[lo:hi] = buf[lo:hi]
        return inv
    finally:
        stats.exit()


# ---------- Max-sum subarray (D&C) ----------

def max_sum_subarray_dc(arr, stats=None):
    """Return (max_sum, start, end_exclusive) via divide and conquer. O(n log n)."""
    stats = stats or Stats()
    a = list(arr)
    if not a:
        return 0, 0, 0, stats
    best, lo, hi = _mc(a, 0, len(a), stats)
    return best, lo, hi, stats


def _mc(a, lo, hi, stats):
    if hi - lo == 1:
        return a[lo], lo, hi
    mid = (lo + hi) // 2
    bl, ll, lh = _mc(a, lo, mid, stats)
    br, rl, rh = _mc(a, mid, hi, stats)

    left_sum, left_best, left_idx = -math.inf, -math.inf, mid
    s = 0
    for i in range(mid - 1, lo - 1, -1):
        stats.comparisons += 1
        s += a[i]
        if s > left_best:
            left_best, left_idx = s, i
    right_sum, right_best, right_idx = -math.inf, -math.inf, mid
    s = 0
    for i in range(mid, hi):
        stats.comparisons += 1
        s += a[i]
        if s > right_best:
            right_best, right_idx = s, i + 1

    cross = left_best + right_best
    if cross >= bl and cross >= br:
        return cross, left_idx, right_idx
    if bl >= br:
        return bl, ll, lh
    return br, rl, rh


# ---------- Majority element ----------

def majority_element(arr, stats=None):
    """Return (candidate, count) if a strict majority (>n/2) exists, else (None, 0)."""
    stats = stats or Stats()
    if not arr:
        return None, 0, stats
    candidate = arr[0]
    vote = 0
    for x in arr:
        stats.comparisons += 1
        if vote == 0:
            candidate = x
            vote = 1
        elif x == candidate:
            vote += 1
        else:
            vote -= 1
    count = 0
    for x in arr:
        stats.comparisons += 1
        if x == candidate:
            count += 1
    if count > len(arr) // 2:
        return candidate, count, stats
    return None, 0, stats


def majority_element_dc(arr, stats=None):
    """D&C variant: returns (candidate, count)."""
    stats = stats or Stats()
    if not arr:
        return None, 0, stats
    candidate, _ = _maj_dc(arr, 0, len(arr), stats)
    if candidate is None:
        return None, 0, stats
    count = sum(1 for x in arr if x == candidate)
    if count > len(arr) // 2:
        return candidate, count, stats
    return None, 0, stats


def _maj_dc(a, lo, hi, stats):
    if hi - lo == 1:
        return a[lo], 1
    mid = (lo + hi) // 2
    lm, lc = _maj_dc(a, lo, mid, stats)
    rm, rc = _maj_dc(a, mid, hi, stats)
    if lm == rm:
        return lm, lc + rc
    if lc > rc:
        return lm, lc - rc
    return rm, rc - lc


# ---------- Closest pair of points ----------

def closest_pair(points, stats=None):
    """Return (distance_squared, i, j) of the closest pair. Points are (x, y) tuples."""
    stats = stats or Stats()
    n = len(points)
    if n < 2:
        return None, -1, -1, stats
    indexed = [(points[i][0], points[i][1], i) for i in range(n)]
    indexed = _merge_sort_by_x(indexed, stats)
    best_d, best_i, best_j = _cp(indexed, stats)
    return best_d, best_i, best_j, stats


def _merge_sort_by_x(arr, stats):
    """Stable merge sort of (x, y, idx) tuples by x. Hand-written."""
    if len(arr) < 2:
        return arr
    mid = len(arr) // 2
    left = _merge_sort_by_x(arr[:mid], stats)
    right = _merge_sort_by_x(arr[mid:], stats)
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        stats.comparisons += 1
        if left[i][0] <= right[j][0]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def _insertion_sort_by_y(arr, stats):
    """In-place insertion sort of (x, y, idx) tuples by y. Hand-written."""
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0:
            stats.comparisons += 1
            if arr[j][1] > key[1]:
                arr[j + 1] = arr[j]
                j -= 1
            else:
                break
        arr[j + 1] = key
    return arr


def _cp(pts, stats):
    n = len(pts)
    if n <= 3:
        best = math.inf
        bi = bj = -1
        for i in range(n):
            for j in range(i + 1, n):
                d = (pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2
                stats.comparisons += 1
                if d < best:
                    best, bi, bj = d, pts[i][2], pts[j][2]
        return best, bi, bj

    mid = n // 2
    mid_x = pts[mid][0]
    dl, li, lj = _cp(pts[:mid], stats)
    dr, ri, rj = _cp(pts[mid:], stats)
    if dl <= dr:
        best, bi, bj = dl, li, lj
    else:
        best, bi, bj = dr, ri, rj

    strip = [p for p in pts if (p[0] - mid_x) ** 2 < best]
    # Sort strip by y using hand-written insertion sort (banned .sort() avoided).
    _insertion_sort_by_y(strip, stats)

    for i in range(len(strip)):
        for j in range(i + 1, min(i + 8, len(strip))):
            stats.comparisons += 1
            dy = strip[j][1] - strip[i][1]
            if dy * dy >= best:
                break
            d = (strip[i][0] - strip[j][0]) ** 2 + dy * dy
            if d < best:
                best, bi, bj = d, strip[i][2], strip[j][2]
    return best, bi, bj
