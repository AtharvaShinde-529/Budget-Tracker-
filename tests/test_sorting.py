import random

import pytest

from backend.algorithms import sorting

SORTS = [
    sorting.insertion_sort,
    sorting.selection_sort,
    sorting.bubble_sort,
    sorting.merge_sort,
    sorting.quick_sort,
    sorting.heap_sort,
    sorting.counting_sort,
    sorting.radix_sort,
]

EDGE_CASES = [
    [],
    [1],
    [2, 1],
    [5, 5, 5, 5],
    list(range(10)),
    list(range(10, 0, -1)),
    [3, -1, 0, -1, 7, -100, 7],
    [0, 0, 1, -1, 0],
    [-5, -4, -3, -2, -1],
]


@pytest.mark.parametrize("fn", SORTS, ids=[f.__name__ for f in SORTS])
@pytest.mark.parametrize("data", EDGE_CASES)
def test_edge_cases(fn, data):
    out, _ = fn(data)
    assert out == sorted(data)


@pytest.mark.parametrize("fn", SORTS, ids=[f.__name__ for f in SORTS])
def test_random_1000(fn):
    rng = random.Random(1234)
    for _ in range(1000):
        n = rng.randint(0, 40)
        data = [rng.randint(-50, 50) for _ in range(n)]
        out, _ = fn(data)
        assert out == sorted(data), data


def test_merge_sort_is_stable():
    data = [(1, "a"), (0, "b"), (1, "c"), (0, "d"), (1, "e")]
    out, _ = sorting.merge_sort(data)
    assert [t for _, t in out] == ["b", "d", "a", "c", "e"]


def test_input_not_mutated():
    data = [3, 1, 2]
    for fn in SORTS:
        fn(data)
    assert data == [3, 1, 2]


def test_stats_are_counted():
    _, stats = sorting.merge_sort(list(range(64)))
    assert stats.comparisons > 0
    assert stats.max_depth >= 1


def test_merge_sort_comparisons_near_nlogn():
    # For n=1024 the comparison count should be between ~n*log2(n)/2 and 2*n*log2(n)
    import math
    n = 1024
    _, stats = sorting.merge_sort(list(range(n)))
    lo = 0.5 * n * math.log2(n)
    hi = 2.0 * n * math.log2(n)
    assert lo <= stats.comparisons <= hi
