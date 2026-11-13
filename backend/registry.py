"""Algorithm metadata powering the Info panel and Syllabus Coverage page.

Every row is one syllabus topic the app actually uses. Add here as you build.
"""

REGISTRY = {
    "insertion_sort": {
        "unit": "I", "paradigm": "Incremental", "stable": True,
        "complexity": {"best": "n", "average": "n^2", "worst": "n^2", "space": "O(1)"},
        "recurrence": "T(n) = T(n-1) + O(n)",
        "how": "Walk left-to-right; insert each element into the sorted prefix by shifting.",
        "feature": "Baseline for benchmark comparison.",
    },
    "selection_sort": {
        "unit": "I", "paradigm": "Selection", "stable": False,
        "complexity": {"best": "n^2", "average": "n^2", "worst": "n^2", "space": "O(1)"},
        "recurrence": "T(n) = T(n-1) + O(n)",
        "how": "Find the minimum of the unsorted suffix, swap it into place.",
        "feature": "Baseline for benchmark comparison.",
    },
    "bubble_sort": {
        "unit": "I", "paradigm": "Exchange", "stable": True,
        "complexity": {"best": "n", "average": "n^2", "worst": "n^2", "space": "O(1)"},
        "recurrence": "T(n) = T(n-1) + O(n)",
        "how": "Repeated adjacent swaps; early exit if a pass makes no swaps.",
        "feature": "Baseline for benchmark comparison.",
    },
    "merge_sort": {
        "unit": "II", "paradigm": "Divide and Conquer", "stable": True,
        "complexity": {"best": "n log n", "average": "n log n", "worst": "n log n", "space": "O(n)"},
        "recurrence": "T(n) = 2T(n/2) + O(n)",
        "how": "Split, recurse, merge with a stable <= comparison.",
        "feature": "Default expense sort. Stable so multi-key sort is two passes.",
    },
    "quick_sort": {
        "unit": "II", "paradigm": "Divide and Conquer (randomized)", "stable": False,
        "complexity": {"best": "n log n", "average": "n log n (expected)", "worst": "n^2 (very unlikely)", "space": "O(log n)"},
        "recurrence": "Expected T(n) = T(n/2) + O(n)",
        "how": "Random pivot; 3-way partition into <, =, >; recurse on the smaller side first.",
        "feature": "Selectable sort with live comparison counts.",
    },
    "heap_sort": {
        "unit": "I", "paradigm": "Selection via heap", "stable": False,
        "complexity": {"best": "n log n", "average": "n log n", "worst": "n log n", "space": "O(1)"},
        "recurrence": "build-heap O(n) + n extractions O(log n) each",
        "how": "Bottom-up heapify, then repeatedly swap the max to the end.",
        "feature": "In-place sort option.",
    },
    "counting_sort": {
        "unit": "I", "paradigm": "Non-comparison", "stable": False,
        "complexity": {"best": "n + k", "average": "n + k", "worst": "n + k", "space": "O(n + k)"},
        "recurrence": "none",
        "how": "Bucket by key value; k = max - min + 1 must be small.",
        "feature": "Sort by day-of-month.",
    },
    "radix_sort": {
        "unit": "I", "paradigm": "Non-comparison", "stable": False,
        "complexity": {"best": "d(n + b)", "average": "d(n + b)", "worst": "d(n + b)", "space": "O(n + b)"},
        "recurrence": "none",
        "how": "LSD digit passes with stable buckets; d digits in base b.",
        "feature": "Sort amounts stored in integer paise.",
    },
    "linear_search": {
        "unit": "I", "paradigm": "Linear scan", "stable": None,
        "complexity": {"best": "1", "average": "n", "worst": "n", "space": "O(1)"},
        "recurrence": "T(n) = T(n-1) + O(1)",
        "how": "Scan until match.",
        "feature": "Fallback search when data not sorted.",
    },
    "binary_search": {
        "unit": "I", "paradigm": "Decrease and Conquer", "stable": None,
        "complexity": {"best": "1", "average": "log n", "worst": "log n", "space": "O(1)"},
        "recurrence": "T(n) = T(n/2) + 1",
        "how": "Halve the sorted array; lower_bound / upper_bound for ranges.",
        "feature": "Date-range expense query in O(log n + k).",
    },
}


def get(name):
    return REGISTRY.get(name)


def all_names():
    return list(REGISTRY)
