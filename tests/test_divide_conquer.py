"""Tests for D&C: inversions, max subarray, majority, closest pair."""

import itertools
import math
import random

from backend.algorithms import divide_conquer as dc


def brute_inversions(arr):
    n = len(arr)
    return sum(1 for i in range(n) for j in range(i+1, n) if arr[i] > arr[j])


def test_inversion_count_matches_brute():
    rng = random.Random(11)
    for _ in range(100):
        n = rng.randint(0, 15)
        data = [rng.randint(-10, 10) for _ in range(n)]
        got, _ = dc.inversion_count(data)
        assert got == brute_inversions(data)


def test_inversion_count_sorted_and_reversed():
    assert dc.inversion_count(list(range(10)))[0] == 0
    assert dc.inversion_count(list(range(10, 0, -1)))[0] == 45


def test_max_sum_subarray():
    assert dc.max_sum_subarray_dc([-2, 1, -3, 4, -1, 2, 1, -5, 4])[0] == 6
    assert dc.max_sum_subarray_dc([1, 2, 3])[0] == 6
    assert dc.max_sum_subarray_dc([-1, -2, -3])[0] == -1


def test_max_sum_subarray_matches_kadane():
    def kadane(a):
        best = cur = a[0]
        for x in a[1:]:
            cur = max(x, cur + x)
            best = max(best, cur)
        return best
    rng = random.Random(3)
    for _ in range(50):
        n = rng.randint(1, 20)
        data = [rng.randint(-20, 20) for _ in range(n)]
        assert dc.max_sum_subarray_dc(data)[0] == kadane(data)


def test_majority_element():
    assert dc.majority_element([1, 1, 2, 1, 3])[0] == 1
    assert dc.majority_element([1, 2, 3, 4])[0] is None
    # D&C variant agrees
    assert dc.majority_element_dc([1, 1, 2, 1, 3])[0] == 1
    assert dc.majority_element_dc([1, 2, 3, 4])[0] is None


def test_closest_pair_matches_brute():
    def brute(pts):
        n = len(pts)
        best = math.inf
        bi = bj = -1
        for i in range(n):
            for j in range(i+1, n):
                d = (pts[i][0] - pts[j][0])**2 + (pts[i][1] - pts[j][1])**2
                if d < best:
                    best, bi, bj = d, i, j
        return best
    rng = random.Random(19)
    for _ in range(30):
        n = rng.randint(2, 25)
        pts = [(rng.randint(0, 50), rng.randint(0, 50)) for _ in range(n)]
        got, _, _, _ = dc.closest_pair(pts)
        assert got == brute(pts)
