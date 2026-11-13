"""Tests for foundations: adversary lower bound + master theorem."""

import math

from backend.algorithms import foundations


def test_adversary_n2():
    r = foundations.adversary_sorting_lab(2)
    assert r["n_factorial"] == 2
    assert r["lower_bound_ceil"] == 1
    assert r["permutation_count"] == 2
    # merge sort with n=2 needs exactly 1 comparison
    assert r["min_comparisons"] == 1
    assert r["max_comparisons"] == 1


def test_adversary_n4_reaches_lower_bound():
    r = foundations.adversary_sorting_lab(4)
    assert r["n_factorial"] == 24
    assert r["lower_bound_ceil"] == 5   # ceil(log2(24)) = 5
    assert r["permutation_count"] == 24
    # merge sort worst case for n=4 is exactly 5 comparisons
    assert r["max_comparisons"] == 5
    assert r["min_comparisons"] >= 4    # some permutation needs at least 4


def test_adversary_n5():
    r = foundations.adversary_sorting_lab(5)
    assert r["n_factorial"] == 120
    assert r["lower_bound_ceil"] == 7   # ceil(log2(120)) = 7
    assert r["permutation_count"] == 120
    assert r["max_comparisons"] >= 7


def test_master_theorem_case1():
    # T(n) = 2T(n/2) + n^0 -> log_b(2)=1 > 0 -> case 1 -> Theta(n)
    r = foundations.master_theorem(2, 2, 0)
    assert r["case"] == 1
    assert "n^1.0" in r["teta"] or "n^1.0000" in r["teta"]


def test_master_theorem_case2_merge_sort():
    # T(n) = 2T(n/2) + n -> log_2(2)=1=d -> case 2 -> Theta(n log n)
    r = foundations.master_theorem(2, 2, 1)
    assert r["case"] == 2
    assert "log n" in r["teta"]


def test_master_theorem_case3():
    # T(n) = 2T(n/2) + n^2 -> log_2(2)=1 < 2 -> case 3 -> Theta(n^2)
    r = foundations.master_theorem(2, 2, 2)
    assert r["case"] == 3
    assert "n^2" in r["teta"]


def test_master_theorem_karatsuba():
    # T(n) = 3T(n/2) + n -> log_2(3) ~ 1.585 > 1 -> case 1 -> Theta(n^1.585)
    r = foundations.master_theorem(3, 2, 1)
    assert r["case"] == 1
    assert "1.585" in r["teta"]


def test_master_theorem_binary_search():
    # T(n) = T(n/2) + 1 -> log_2(1)=0 = d -> case 2 -> Theta(log n)
    r = foundations.master_theorem(1, 2, 0)
    assert r["case"] == 2


def test_master_theorem_rejects_bad_input():
    import pytest
    with pytest.raises(ValueError):
        foundations.master_theorem(0, 2, 1)
    with pytest.raises(ValueError):
        foundations.master_theorem(2, 1, 1)
