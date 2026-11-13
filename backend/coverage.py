"""Syllabus coverage matrix ? data for the Coverage page.

Each row is one syllabus topic, mapped to the feature in this app that uses
it, and the status ('implemented' / 'partial' / 'lab-only').
"""

COVERAGE = [
    # ---------- Unit I: Basics, complexity, lower bounds ----------
    {"unit": "I", "topic": "Big-O, Omega, Theta",           "feature": "Every algorithm reports comparisons/swaps/calls; benchmark graphs", "status": "implemented"},
    {"unit": "I", "topic": "Best / average / worst case",    "feature": "Sort dropdown runs on all distributions in benchmarks/",            "status": "implemented"},
    {"unit": "I", "topic": "Recursive analysis",             "feature": "max_depth counter on every recursive algorithm",                    "status": "implemented"},
    {"unit": "I", "topic": "Insertion / selection / bubble", "feature": "Baseline sorts in backend/algorithms/sorting.py",                  "status": "implemented"},
    {"unit": "I", "topic": "Merge / quick / heap",           "feature": "Sort algorithm dropdown in Expenses page",                         "status": "implemented"},
    {"unit": "I", "topic": "Counting / radix",               "feature": "Sort by amount_paise (integer keys)",                              "status": "implemented"},
    {"unit": "I", "topic": "Linear search",                  "feature": "Fallback search in analytics (keyword filter)",                    "status": "implemented"},
    {"unit": "I", "topic": "Binary search + bounds",         "feature": "Date-range expense query",                                         "status": "implemented"},
    {"unit": "I", "topic": "Adversary lower bound",          "feature": "Adversary lab ? permutation enumeration vs merge_sort",             "status": "implemented"},
    {"unit": "I", "topic": "Correctness proofs / invariants","feature": "Report: per-algorithm correctness sections",                       "status": "implemented"},

    # ---------- Unit II: Recursion and Divide & Conquer ----------
    {"unit": "II", "topic": "Recurrences, Master theorem",   "feature": "Master theorem calculator",                                         "status": "implemented"},
    {"unit": "II", "topic": "Enumeration of sets/perms/combs","feature": "What-if lab + adversary lab",                                       "status": "implemented"},
    {"unit": "II", "topic": "Josephus problem",              "feature": "Who-pays picker (structures.py LinkedList)",                       "status": "implemented"},
    {"unit": "II", "topic": "Randomized quick sort",         "feature": "Sort dropdown",                                                     "status": "implemented"},
    {"unit": "II", "topic": "Merge sort (stable)",           "feature": "Default sort in Expenses page",                                     "status": "implemented"},
    {"unit": "II", "topic": "Counting inversions",           "feature": "Analytics ? category ranking change vs last month",                 "status": "implemented"},
    {"unit": "II", "topic": "Majority element",              "feature": "Analytics ? dominant category (Boyer-Moore)",                       "status": "implemented"},
    {"unit": "II", "topic": "Randomized quickselect",        "feature": "Analytics ? median, P90, top-K",                                    "status": "implemented"},
    {"unit": "II", "topic": "Median of medians",             "feature": "Order stats alternative in report",                                "status": "implemented"},
    {"unit": "II", "topic": "Closest pair of points",        "feature": "Analytics ? duplicate detection",                                  "status": "implemented"},
    {"unit": "II", "topic": "Randomness in computation",     "feature": "Random pivots in quick sort / quickselect",                         "status": "implemented"},

    # ---------- Unit III: Dynamic Programming ----------
    {"unit": "III", "topic": "Fibonacci DP",                 "feature": "Not wired ? syllabus demo only",                                   "status": "partial"},
    {"unit": "III", "topic": "Matrix chain",                 "feature": "Not wired",                                                        "status": "partial"},
    {"unit": "III", "topic": "Coin change DP",               "feature": "Compare vs greedy in report",                                       "status": "partial"},
    {"unit": "III", "topic": "TSP (Held-Karp)",              "feature": "Not wired ? stub in dp.py",                                        "status": "stub"},
    {"unit": "III", "topic": "Optimal BST",                  "feature": "Practical 6 ? stub in dp.py",                                       "status": "stub"},
    {"unit": "III", "topic": "Floyd-Warshall",               "feature": "Not wired",                                                        "status": "stub"},
    {"unit": "III", "topic": "LIS / LCS",                    "feature": "Not wired",                                                        "status": "stub"},

    # ---------- Unit IV: Greedy and Backtracking ----------
    {"unit": "IV", "topic": "Fractional knapsack",           "feature": "Optimiser ? goal funding",                                          "status": "implemented"},
    {"unit": "IV", "topic": "Job sequencing with deadlines", "feature": "Optimiser ? bill scheduler (Union-Find)",                           "status": "implemented"},
    {"unit": "IV", "topic": "Greedy coin change",            "feature": "Optimiser ? cash breakdown (INR denominations)",                    "status": "implemented"},
    {"unit": "IV", "topic": "Min-transaction settlement",    "feature": "Optimiser ? roommate settlement (two heaps)",                       "status": "implemented"},
    {"unit": "IV", "topic": "Interval scheduling",           "feature": "Optimiser ? shift picks",                                           "status": "implemented"},
    {"unit": "IV", "topic": "Huffman coding",                "feature": "Optimiser ? expense log compression",                               "status": "implemented"},
    {"unit": "IV", "topic": "Subset-sum backtracking",       "feature": "What-if lab",                                                       "status": "stub"},
    {"unit": "IV", "topic": "N-queens / Sudoku / Hamiltonian","feature": "Not wired ? stub in backtracking.py",                              "status": "stub"},

    # ---------- Unit V: Network Flows ----------
    {"unit": "V",  "topic": "Max-flow / min-cut",            "feature": "Not wired ? stub in flows.py",                                     "status": "stub"},
    {"unit": "V",  "topic": "Bipartite matching",             "feature": "Not wired ? stub in flows.py",                                     "status": "stub"},

    # ---------- Unit VI: NP-completeness ----------
    {"unit": "VI", "topic": "Verifier vs solver",            "feature": "Not wired ? stub in nplab.py",                                     "status": "stub"},
    {"unit": "VI", "topic": "Reductions (VC?IS?Clique)",     "feature": "Not wired",                                                        "status": "stub"},
    {"unit": "VI", "topic": "DPLL SAT",                      "feature": "Not wired",                                                        "status": "stub"},
    {"unit": "VI", "topic": "ILP modelling",                 "feature": "Not wired",                                                        "status": "stub"},
]


def coverage_summary():
    total = len(COVERAGE)
    done = sum(1 for r in COVERAGE if r["status"] == "implemented")
    partial = sum(1 for r in COVERAGE if r["status"] == "partial")
    stub = sum(1 for r in COVERAGE if r["status"] == "stub")
    by_unit = {}
    for r in COVERAGE:
        by_unit.setdefault(r["unit"], {"total": 0, "done": 0})
        by_unit[r["unit"]]["total"] += 1
        if r["status"] == "implemented":
            by_unit[r["unit"]]["done"] += 1
    return {
        "total": total,
        "implemented": done,
        "partial": partial,
        "stub": stub,
        "completion_pct": round(100 * done / total, 1) if total else 0,
        "by_unit": by_unit,
    }
