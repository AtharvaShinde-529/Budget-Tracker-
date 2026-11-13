# BudgetTracker — DAA Project Report

A personalised budget and expense tracker for students, built to demonstrate
every major algorithm paradigm from the Design and Analysis of Algorithms
syllabus (Units I–VI).

## 1. Project overview

| | |
|---|---|
| **Language** | Python 3.10 |
| **Backend** | FastAPI + Uvicorn |
| **Database** | SQLite (money stored as integer paise) |
| **Frontend** | HTML + CSS + vanilla JS + Chart.js (offline) |
| **Testing** | pytest (140+ tests) |
| **Benchmarking** | matplotlib + time.perf_counter |

Every algorithm in `backend/algorithms/` is written by hand. Python's own
`sorted()`, `heapq`, `itertools`, `bisect` and `collections` are banned there
by an AST-based guard test (`tests/test_no_builtins.py`). They appear only
in tests as oracles.

## 2. Architecture




Rule: **algorithms/ never imports services/, db/, or FastAPI**. Pure
list-in, `(result, Stats)`-out. Enforced by `test_no_builtins.py`.

## 3. Algorithm coverage (per syllabus topic)

### Unit I — Basics, complexity, lower bounds

**Insertion sort** — `backend/algorithms/sorting.py:insertion_sort`
- *Recurrence:* T(n) = T(n-1) + O(n)
- *Complexity:* best n, average n², worst n², space O(1)
- *Correctness:* Loop invariant — after iteration i, a[0..i] is sorted and
  contains the original a[0..i]. Preservation: inserting a[i] into the sorted
  prefix by shifting maintains sortedness. Termination: i = n-1.
- *Where:* baseline in benchmark lab.

**Selection sort** — T(n) = T(n-1) + O(n), Θ(n²) always, O(1) space.
- *Loop invariant:* after iteration i, a[0..i-1] contains the i smallest
  elements in sorted order.

**Bubble sort** — Θ(n²) average/worst, Θ(n) best (early exit).
- *Where:* baseline comparison in the Benchmark page.

**Merge sort** — T(n) = 2T(n/2) + O(n) → Θ(n log n) by Master theorem case 2.
- *Space:* O(n) for the merge buffer.
- *Stability:* uses `<=` on merge, so equal elements keep their order.
- *Where:* **default sort in Expenses page**. Enables multi-key sort by two
  stable passes (e.g. category then amount).

**Quick sort (randomized)** — expected T(n) = 2·(n-1)·ln(n) ≈ 1.386 n log₂ n
- *Worst case:* Θ(n²) with probability ≈ 0 for random pivots.
- *Space:* O(log n) recursion depth (recurse on smaller side first).
- *Pivot strategy:* random + 3-way partition for duplicates.
- *Where:* sort dropdown.

**Heap sort** — build-heap Θ(n) + n × Θ(log n) extraction → Θ(n log n), O(1) space.
- *Where:* in-place sort option.

**Counting sort** — Θ(n + k) with k = max - min + 1.
- *Where:* sort by amount_paise when k is small.

**Radix sort (LSD, base 256)** — Θ(d(n + b)) with d = digits.
- *Where:* sort by amount_paise (integer keys only — enforced by service).

**Binary search / lower_bound / upper_bound** — T(n) = T(n/2) + 1 → Θ(log n).
- *Where:* date-range expense query in O(log n + k).

**Adversary lower bound** — `backend/algorithms/foundations.py:adversary_sorting_lab`
- Any comparison sort needs ≥ ⌈log₂(n!)⌉ comparisons worst-case.
- For n=4: ⌈log₂(24)⌉ = 5. merge_sort's actual worst case on n=4 is
  exactly 5, so it's optimal for this size.
- *Where:* Theory Lab page → adversary panel.

### Unit II — Recursion and Divide & Conquer

**Randomized quickselect** — expected T(n) = T(n/2) + O(n) → Θ(n) expected.
- *Worst case:* Θ(n²) with probability vanishingly small.
- *Correctness:* After partition, pivot is at its final position. If k == pivot
  index, return; else recurse on the correct side.
- *Where:* Analytics page median, P90, top-K.

**Median of medians** — deterministic T(n) = T(n/5) + T(7n/10) + O(n) → Θ(n).
- *Groups of 5:* chosen so (n/5) medians guarantee the pivot is between
  the 30th and 70th percentile of the array.
- *Where:* order_stats.median(method='mom') for comparison.

**Inversion count (D&C)** — T(n) = 2T(n/2) + O(n) → Θ(n log n) via merge sort.
- Counts pairs (i, j) with i < j and a[i] > a[j] using a modified merge.
- *Where:* Analytics page ranking change vs last month.

**Max-sum subarray (D&C)** — T(n) = 2T(n/2) + O(n) → Θ(n log n).
- Best-crossing computation: best suffix of left half + best prefix of right half.
- *Where:* Analytics page — worst overspend streak.

**Majority element (Boyer–Moore)** — Θ(n) time, O(1) space.
- *Correctness:* Vote-cancellation argument. If a strict majority exists, the
  candidate must survive all cancellations. Verification pass confirms.
- *D&C variant:* T(n) = 2T(n/2) + O(1), also Θ(n).
- *Where:* Analytics page dominant category.

**Closest pair of points (D&C)** — T(n) = 2T(n/2) + O(n) → Θ(n log n).
- Strip check: sort strip by y (insertion sort, O(n) for small strips),
  check each point against next 7 in the strip.
- *Where:* Analytics page duplicate detection.

### Unit III — Dynamic Programming (partial)

Implemented: stubs in `backend/algorithms/dp.py`. See Coverage page for
which rows are implemented vs partial vs stub. This is an honest report —
DP features are future work, not viva-ready.

### Unit IV — Greedy and Backtracking

**Fractional knapsack** — O(n log n). Sort by value/weight ratio descending.
- *Exchange argument:* Any optimal solution must prefer higher ratio items;
  swapping any lower-ratio item for a higher-ratio fraction doesn't decrease
  value. Proof by contradiction.
- *Where:* Optimiser — goal funding.

**Job sequencing with deadlines** — O(n log n) sort + O(n α(n)) Union-Find.
- *Greedy choice:* process jobs by penalty descending; assign each to the
  latest free slot ≤ deadline. Exchange argument guarantees optimality.
- *Where:* Optimiser — bill scheduler.

**Greedy coin change** — O(n) on canonical denominations.
- Correct for INR (1,2,5,10,20,50,100,200,500,1000,2000).
- *Fails for:* arbitrary systems, e.g. coins {1,3,4} amount 6 → greedy uses
  4+1+1 (3 coins) vs optimal 3+3 (2 coins). Report notes this in the viva.
- *Where:* Optimiser — cash breakdown.

**Min-transaction settlement** — two MaxHeaps, O(n log n).
- *Greedy choice:* match largest creditor with largest debtor, transfer min.
- *Where:* Optimiser — roommate settlement.

**Interval scheduling** — O(n log n) sort by end ascending.
- *Exchange argument:* earliest-finish-time greedy is optimal (CLRS §16.1).
- *Where:* Optimiser — shift picks.

**Huffman coding** — O(n log n) with MinHeap.
- *Correctness:* Greedy choice — two least-frequent symbols must be siblings
  at the deepest level (exchange argument). Prefix-free property follows from
  tree structure.
- *Where:* Optimiser — expense log compression.

### Unit V — Network Flows (stub)

Reserved for future work. Not implemented in this submission.

### Unit VI — NP-completeness (stub)

Reserved for future work. Not implemented in this submission.

## 4. Empirical benchmarks

Run `python -m benchmarks.run_benchmarks` to regenerate. Graphs are in
`benchmarks/results/`.

| Graph | What it shows |
|---|---|
| `sort_time_vs_n.png` | Sort time vs array size (log-log) — empirically n log n for merge/quick/heap, n² for insertion/selection |
| `sort_by_distribution.png` | Same algorithms on random / sorted / reversed / duplicate data |
| `quickselect_vs_sort.png` | Quickselect O(n) vs merge-sort-then-index O(n log n) — the gap is visible |
| `greedy_vs_brute.png` | Job scheduling: greedy O(n log n) vs brute-force O(2ⁿ) |
| `huffman_compression.png` | Compression ratio on sample strings |

## 5. Correctness — invariant / exchange argument / induction summary

| Algorithm | Proof style | Sketch |
|---|---|---|
| Merge sort | Loop invariant | Merge preserves order of two sorted halves |
| Quick sort | Expected analysis | Indicator variables, expected comparisons ≈ 2n ln n |
| Quickselect | Expected analysis | T(n) = T(n/2) + O(n), harmonic-sum recurrence |
| Median of medians | Induction | T(n/5) + T(7n/10) + n = O(n) |
| Inversion count | Loop invariant | Each merge contributes (mid - i) inversions |
| Max-sum subarray | Induction on recursion | Three cases: left, right, crossing |
| Closest pair | Induction + geometric argument | 7-neighbor strip check is sufficient |
| Fractional knapsack | Exchange argument | Prefer higher ratio |
| Job sequencing | Exchange argument | Highest penalty gets latest free slot |
| Settlement | Greedy-stays-optimal | Matching largest amounts keeps count minimal |
| Huffman | Exchange argument | Siblings at deepest level |
| Interval scheduling | Exchange argument | Earliest finish time |

## 6. Testing evidence

- **140+ unit tests** covering sorts, searches, order statistics, D&C,
  greedy, Huffman, foundations, expense service, undo/redo, non-comparison
  sort contract.
- **1000 random arrays per sort** vs Python's `sorted()` as oracle.
- **Closest pair** vs O(n²) brute force.
- **Inversion count** vs O(n²) brute force.
- **Max-sum subarray** vs Kadane's algorithm.
- **Job sequencing** vs exhaustive subset enumeration for n ≤ 8.
- **Interval scheduling** vs brute-force max independent set.
- **Huffman** round-trip (encode → decode = original), prefix-free check.
- **Adversary lab** vs ⌈log₂(n!)⌉ — merge sort matches bound for n ∈ {2..5}.
- **Non-comparison sort guard** — 500 errors prevented by service validation.
- **AST guard** — no `sorted()`, `heapq`, `itertools` in `backend/algorithms/`.

## 7. Viva talk track (8-minute demo)

1. **Dashboard** — seeded 205 expenses.
2. **Expenses** — change sort field to Amount, change algorithm to Merge sort
   → live comparison counter is shown. Change to Radix sort → dropdown hides
   non-comparison sorts for non-amount fields.
3. **Analytics** — median expense (quickselect), worst streak (max-subarray
   D&C), dominant category (Boyer-Moore), duplicates (closest pair).
4. **Optimiser** — edit monthly savings input, click Optimise → fraction
   knapsack re-runs; bill scheduler shows penalty avoided; Huffman shows
   compression ratio on real expense descriptions.
5. **Theory Lab** — adversary lab with n=4 → "any comparison sort needs at
   least 5 comparisons, merge sort achieves exactly 5, so it's optimal at
   n=4"; Master theorem for merge sort → "case 2, Θ(n log n)".
6. **Coverage** — "here is every syllabus topic with a tick or a note".

## 8. Limitations / future work

- **Units III, V, VI** are stubs. The algorithms are catalogued in
  `backend/algorithms/dp.py`, `flows.py`, `nplab.py`, `backtracking.py`
  and `enumeration.py` but not wired to features.
- **0/1 knapsack, min-coins DP** — would sharpen the greedy vs DP contrast.
- **Kruskal/Prim/Dijkstra** — planned for Money Graphs page.
- **ILP lab** — scipy is installed but not exercised.
