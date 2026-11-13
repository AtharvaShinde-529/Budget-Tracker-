import random

from backend.algorithms import searching, sorting


def test_binary_search_hits_and_misses():
    data = [1, 3, 3, 3, 7, 9]
    assert searching.binary_search(data, 3)[0] in (1, 2, 3)
    assert searching.binary_search(data, 5)[0] == -1
    assert searching.binary_search(data, 1)[0] == 0
    assert searching.binary_search(data, 9)[0] == 5
    assert searching.binary_search(data, 0)[0] == -1
    assert searching.binary_search(data, 10)[0] == -1


def test_bounds():
    data = [1, 3, 3, 3, 7, 9]
    assert searching.lower_bound(data, 3)[0] == 1
    assert searching.upper_bound(data, 3)[0] == 4
    assert searching.lower_bound(data, 0)[0] == 0
    assert searching.upper_bound(data, 99)[0] == len(data)


def test_range_random_against_filter():
    rng = random.Random(7)
    for _ in range(200):
        data = [rng.randint(0, 100) for _ in range(rng.randint(0, 50))]
        s, _ = sorting.merge_sort(data)
        lo, hi = sorted([rng.randint(0, 100), rng.randint(0, 100)])
        a, b, _ = searching.range_indices(s, lo, hi)
        assert s[a:b] == [x for x in s if lo <= x < hi]


def test_linear_search():
    data = [5, 3, 7, 1]
    assert searching.linear_search(data, 7)[0] == 2
    assert searching.linear_search(data, 99)[0] == -1
