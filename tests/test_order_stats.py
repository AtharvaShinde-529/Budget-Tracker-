"""Tests for order_stats: quickselect, median-of-medians, percentiles, outliers."""

import random

from backend.algorithms import order_stats


def test_quickselect_matches_sorted_index():
    rng = random.Random(42)
    for _ in range(200):
        n = rng.randint(1, 40)
        data = [rng.randint(-100, 100) for _ in range(n)]
        k = rng.randint(0, n - 1)
        out, _ = order_stats.randomized_quickselect(data, k)
        assert out == sorted(data)[k]


def test_median_of_medians_matches_sorted_index():
    rng = random.Random(7)
    for _ in range(100):
        n = rng.randint(1, 50)
        data = [rng.randint(-100, 100) for _ in range(n)]
        k = rng.randint(0, n - 1)
        out, _ = order_stats.median_of_medians(data, k)
        assert out == sorted(data)[k]


def test_median_odd_even():
    assert order_stats.median([3, 1, 2])[0] == 2
    assert order_stats.median([4, 1, 3, 2])[0] == 2.5
    assert order_stats.median([7])[0] == 7
    # MoM should agree
    assert order_stats.median([4, 1, 3, 2], method="mom")[0] == 2.5


def test_percentile_boundaries():
    data = list(range(1, 101))  # 1..100
    assert order_stats.percentile(data, 0)[0] == 1
    assert order_stats.percentile(data, 100)[0] == 100
    p50, _ = order_stats.percentile(data, 50)
    assert 50 <= p50 <= 51


def test_iqr_outliers_detects_obvious():
    normal = [10, 12, 11, 13, 12, 10, 11, 12, 13, 11, 12, 10]
    data = normal + [1000]
    outliers, stats = order_stats.iqr_outliers(data)
    assert len(outliers) == 1
    assert outliers[0][1] == 1000


def test_top_k():
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    top, _ = order_stats.top_k(data, 3)
    assert top == [9, 6, 5]
