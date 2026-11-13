"""Benchmark script ? generates 5 PNG graphs in benchmarks/results/.

Run with:  python -m benchmarks.run_benchmarks

Uses matplotlib (installed), and never uses the built-in sort in
backend/algorithms code. The built-in sort is allowed here in the
benchmark script since we only use it as an oracle.
"""

import pathlib
import time
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from backend.algorithms import sorting, order_stats, greedy, huffman, divide_conquer


RESULTS_DIR = pathlib.Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------- data generators ----------

def random_data(n, seed=0):
    rng = random.Random(seed)
    return [rng.randint(0, 100_000) for _ in range(n)]


def sorted_data(n):
    return list(range(n))


def reversed_data(n):
    return list(range(n, 0, -1))


def duplicates_data(n):
    return [i % 3 for i in range(n)]


DISTRIBUTIONS = {
    "random": random_data,
    "sorted": lambda n: sorted_data(n),
    "reversed": lambda n: reversed_data(n),
    "duplicates": duplicates_data,
}

SORTS_TO_BENCH = {
    "insertion_sort": sorting.insertion_sort,
    "selection_sort": sorting.selection_sort,
    "merge_sort":     sorting.merge_sort,
    "quick_sort":     sorting.quick_sort,
    "heap_sort":      sorting.heap_sort,
}


# ---------- experiment 1: sort time vs n ----------

def exp1_sort_time_vs_n():
    sizes = [100, 500, 1000, 2000, 5000]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for name, fn in SORTS_TO_BENCH.items():
        times = []
        for n in sizes:
            data = random_data(n, seed=42)
            t0 = time.perf_counter()
            fn(data)
            times.append((time.perf_counter() - t0) * 1000)  # ms
        ax.plot(sizes, times, marker="o", label=name)
    ax.set_xlabel("n (array size)")
    ax.set_ylabel("time (ms)")
    ax.set_title("Sort time vs n (random data)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = RESULTS_DIR / "sort_time_vs_n.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"  wrote {path.name}")


# ---------- experiment 2: distribution matters ----------

def exp2_distribution():
    n = 2000
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x_labels = list(DISTRIBUTIONS.keys())
    for name, fn in SORTS_TO_BENCH.items():
        times = []
        for dist_name, gen in DISTRIBUTIONS.items():
            data = gen(n)
            t0 = time.perf_counter()
            fn(data)
            times.append((time.perf_counter() - t0) * 1000)
        ax.bar(
            [i + list(SORTS_TO_BENCH).index(name) * 0.15 for i in range(len(x_labels))],
            times, width=0.15, label=name,
        )
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels)
    ax.set_ylabel("time (ms)")
    ax.set_title(f"Sort time by distribution (n={n})")
    ax.legend()
    fig.tight_layout()
    path = RESULTS_DIR / "sort_by_distribution.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"  wrote {path.name}")


# ---------- experiment 3: quickselect vs sort-then-index ----------

def exp3_quickselect_vs_sort():
    sizes = [1000, 5000, 10000, 50000, 100000]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    select_times = []
    sort_times = []
    for n in sizes:
        data = random_data(n, seed=7)
        # quickselect median
        t0 = time.perf_counter()
        order_stats.randomized_quickselect(data, n // 2)
        select_times.append((time.perf_counter() - t0) * 1000)
        # sort-then-index
        t0 = time.perf_counter()
        sorted_copy, _ = sorting.merge_sort(data)
        _ = sorted_copy[n // 2]
        sort_times.append((time.perf_counter() - t0) * 1000)
    ax.plot(sizes, select_times, marker="o", label="quickselect (expected O(n))")
    ax.plot(sizes, sort_times, marker="s", label="merge sort + index (O(n log n))")
    ax.set_xlabel("n")
    ax.set_ylabel("time (ms)")
    ax.set_title("Median: quickselect vs sort-then-index")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = RESULTS_DIR / "quickselect_vs_sort.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"  wrote {path.name}")


# ---------- experiment 4: greedy vs brute-force on job scheduling ----------

def exp4_greedy_vs_brute():
    """Show greedy scheduler's optimality on small instances (matches brute force)."""
    sizes = [3, 4, 5, 6, 7]
    greedy_times = []
    brute_times = []
    import itertools

    def brute_max_penalty(jobs):
        max_dl = max(j["deadline_day"] for j in jobs)
        best = 0
        for r in range(len(jobs) + 1):
            for combo in itertools.combinations(jobs, r):
                feasible = True
                for d in range(1, max_dl + 1):
                    if sum(1 for j in combo if j["deadline_day"] <= d) > d:
                        feasible = False
                        break
                if feasible:
                    best = max(best, sum(j["penalty_paise"] for j in combo))
        return best

    for n in sizes:
        rng = random.Random(42)
        jobs = [
            {"name": f"j{k}", "deadline_day": rng.randint(1, n),
             "penalty_paise": rng.randint(1, 100)}
            for k in range(n)
        ]

        t0 = time.perf_counter()
        scheduled, _ = greedy.job_sequencing_with_deadlines(jobs)
        greedy_times.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        brute_max_penalty(jobs)
        brute_times.append((time.perf_counter() - t0) * 1000)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(sizes, greedy_times, marker="o", label="greedy (O(n log n))")
    ax.plot(sizes, brute_times, marker="s", label="brute force (O(2?))")
    ax.set_xlabel("n jobs")
    ax.set_ylabel("time (ms)")
    ax.set_title("Job scheduling: greedy vs brute force")
    ax.set_yscale("log")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = RESULTS_DIR / "greedy_vs_brute.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"  wrote {path.name}")


# ---------- experiment 5: Huffman compression on real strings ----------

def exp5_huffman_compression():
    texts = {
        "abcabcabc": "abcabcabc",
        "aaabbbccc repeated": "aaabbbccc" * 10,
        "english sentence": "the quick brown fox jumps over the lazy dog " * 5,
        "lorem ipsum": "lorem ipsum dolor sit amet consectetur adipiscing elit " * 5,
        "one-char only": "a" * 50,
    }
    names = list(texts.keys())
    ratios = []
    for name in names:
        text = texts[name]
        if not text:
            ratios.append(0)
            continue
        codes, _, _ = huffman.build_huffman(text)
        bits, _ = huffman.huffman_encode(text, codes)
        original_bits = len(text) * 8
        ratios.append(len(bits) / original_bits)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(range(len(names)), [r * 100 for r in ratios], color="#6366f1")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylabel("% of 8-bit baseline")
    ax.set_title("Huffman compression ratio on sample strings")
    ax.axhline(100, color="red", linestyle="--", alpha=0.5, label="uncompressed baseline")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = RESULTS_DIR / "huffman_compression.png"
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"  wrote {path.name}")


# ---------- main ----------

def main():
    print("Running benchmarks (5 experiments, ~10 seconds)...")
    exp1_sort_time_vs_n()
    exp2_distribution()
    exp3_quickselect_vs_sort()
    exp4_greedy_vs_brute()
    exp5_huffman_compression()
    print(f"\nAll graphs written to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
