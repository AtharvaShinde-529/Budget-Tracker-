"""All sorting algorithms, hand-written.

Rule: no sorted(), no .sort(), no heapq, no itertools, no bisect in this file.
Every function returns (result_list, Stats) and never mutates its input.
"""

import random

from backend.instrumentation import Stats


# ---------- O(n^2) baselines ----------

def insertion_sort(arr, stats=None):
    stats = stats or Stats()
    a = list(arr)
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0:
            stats.comparisons += 1
            if a[j] > key:
                a[j + 1] = a[j]
                stats.swaps += 1
                j -= 1
            else:
                break
        a[j + 1] = key
    return a, stats


def selection_sort(arr, stats=None):
    stats = stats or Stats()
    a = list(arr)
    n = len(a)
    for i in range(n - 1):
        m = i
        for j in range(i + 1, n):
            stats.comparisons += 1
            if a[j] < a[m]:
                m = j
        if m != i:
            a[i], a[m] = a[m], a[i]
            stats.swaps += 1
    return a, stats


def bubble_sort(arr, stats=None):
    stats = stats or Stats()
    a = list(arr)
    n = len(a)
    for end in range(n - 1, 0, -1):
        swapped = False
        for j in range(end):
            stats.comparisons += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                stats.swaps += 1
                swapped = True
        if not swapped:
            break
    return a, stats


# ---------- Divide and conquer ----------

def merge_sort(arr, stats=None):
    """Stable merge sort. T(n) = 2T(n/2) + O(n)."""
    stats = stats or Stats()
    a = list(arr)
    if len(a) < 2:
        return a, stats
    buf = [None] * len(a)
    _ms(a, 0, len(a), buf, stats, 0)
    return a, stats


def _ms(a, lo, hi, buf, stats, depth):
    stats.enter()
    if depth > stats.max_depth:
        stats.max_depth = depth
    if hi - lo >= 2:
        mid = (lo + hi) // 2
        _ms(a, lo, mid, buf, stats, depth + 1)
        _ms(a, mid, hi, buf, stats, depth + 1)
        i, j, k = lo, mid, lo
        while i < mid and j < hi:
            stats.comparisons += 1
            if a[i] <= a[j]:          # <= preserves stability
                buf[k] = a[i]; i += 1
            else:
                buf[k] = a[j]; j += 1
            k += 1
        while i < mid:
            buf[k] = a[i]; i += 1; k += 1
        while j < hi:
            buf[k] = a[j]; j += 1; k += 1
        a[lo:hi] = buf[lo:hi]
    stats.exit()


def quick_sort(arr, stats=None, rng=None):
    """Randomized quick sort with 3-way (Dutch national flag) partition."""
    stats = stats or Stats()
    rng = rng or random.Random()
    a = list(arr)
    _qs(a, 0, len(a) - 1, stats, rng, 0)
    return a, stats


def _qs(a, lo, hi, stats, rng, depth):
    stats.enter()
    if depth > stats.max_depth:
        stats.max_depth = depth
    if lo < hi:
        p = rng.randint(lo, hi)
        pivot = a[p]
        lt, i, gt = lo, lo, hi
        while i <= gt:
            stats.comparisons += 1
            if a[i] < pivot:
                a[lt], a[i] = a[i], a[lt]
                stats.swaps += 1
                lt += 1; i += 1
            elif a[i] > pivot:
                a[i], a[gt] = a[gt], a[i]
                stats.swaps += 1
                gt -= 1
            else:
                i += 1
        # recurse on the smaller side first to keep the stack shallow
        if (lt - 1 - lo) < (hi - (gt + 1)):
            _qs(a, lo, lt - 1, stats, rng, depth + 1)
            _qs(a, gt + 1, hi, stats, rng, depth + 1)
        else:
            _qs(a, gt + 1, hi, stats, rng, depth + 1)
            _qs(a, lo, lt - 1, stats, rng, depth + 1)
    stats.exit()


def heap_sort(arr, stats=None):
    """In-place, O(1) extra space, not stable."""
    stats = stats or Stats()
    a = list(arr)
    n = len(a)

    def sift(i, size):
        while True:
            l, r, big = 2 * i + 1, 2 * i + 2, i
            if l < size:
                stats.comparisons += 1
                if a[l] > a[big]:
                    big = l
            if r < size:
                stats.comparisons += 1
                if a[r] > a[big]:
                    big = r
            if big == i:
                return
            a[i], a[big] = a[big], a[i]
            stats.swaps += 1
            i = big

    for i in range(n // 2 - 1, -1, -1):
        sift(i, n)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        stats.swaps += 1
        sift(0, end)
    return a, stats


# ---------- Linear-time sorts for restricted keys ----------

def counting_sort(arr, stats=None):
    """O(n + k) for integer keys where k = max - min + 1 is small."""
    stats = stats or Stats()
    a = list(arr)
    if not a:
        return a, stats

    lo = hi = a[0]
    for x in a:
        stats.comparisons += 2
        if x < lo:
            lo = x
        if x > hi:
            hi = x

    k = hi - lo + 1
    count = [0] * k
    for x in a:
        count[x - lo] += 1

    out = []
    for idx, c in enumerate(count):
        if c:
            out.extend([idx + lo] * c)
    return out, stats


def radix_sort(arr, stats=None, base=256):
    """LSD radix sort. Handles negatives by sorting the absolute value."""
    stats = stats or Stats()
    a = list(arr)
    if not a:
        return a, stats

    pos = [x for x in a if x >= 0]
    neg = [-x for x in a if x < 0]

    pos = _radix_pos(pos, base, stats)
    neg = _radix_pos(neg, base, stats)

    neg_sorted = [-x for x in reversed(neg)]
    return neg_sorted + pos, stats


def _radix_pos(a, base, stats):
    if not a:
        return a
    hi = a[0]
    for x in a:
        stats.comparisons += 1
        if x > hi:
            hi = x
    exp = 1
    while hi // exp > 0:
        buckets = [[] for _ in range(base)]
        for x in a:
            buckets[(x // exp) % base].append(x)
        a = [x for b in buckets for x in b]
        exp *= base
    return a
