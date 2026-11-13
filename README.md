# BudgetTracker - Design and Analysis of Algorithms (DAA) Project

**Author:** Atharva Shinde  
**Email:** atharvashinde529@gmail.com  

## 📌 Project Overview
**BudgetTracker** is a personalised budget and expense tracking application designed specifically for students. It was built as a comprehensive course project to demonstrate the practical application of the **Design and Analysis of Algorithms (DAA)** syllabus (Units I - VI). 

Instead of simply writing algorithms in a terminal, every major DAA concept is integrated into a fully functional, interactive web application. The project strictly adheres to the rule: **No built-in sorting (`sorted()`), `heapq`, or `itertools` are used in the core algorithm modules.** Every sort, search, and optimization routine is hand-written from scratch.

## 🚀 Key Features
*   **Interactive UI:** A dark-theme, responsive web interface built with vanilla JS and Chart.js.
*   **Live Instrumentation:** Watch algorithms work in real-time. The UI displays live comparison counts, swaps, and recursion depths for sorting operations.
*   **Expense Management:** Full CRUD operations with SQLite, storing money as integers (paise) to avoid floating-point errors.
*   **Undo/Redo Engine:** Custom stack implementation for reversing database mutations.
*   **Advanced Analytics:** Outlier detection (IQR), duplicate detection (Closest Pair), and overspend streaks (Max Subarray).
*   **Optimiser Lab:** Fractional Knapsack for goal funding, Job Sequencing for bills, and Huffman coding for log compression.
*   **Theory Lab:** Interactive tools for calculating the Master Theorem and proving the Adversary Lower Bound for sorting.

---

## 🧠 Algorithms Implemented (Hand-Written)

### 1. Sorting & Searching
*   **Sorts:** Insertion, Selection, Bubble, Merge (stable), Quick (randomized 3-way), Heap, Counting, Radix.
*   **Searches:** Linear, Binary, Lower Bound / Upper Bound (O(log n) range queries).

### 2. Divide & Conquer
*   **Inversion Count:** Measures how "out of order" spending rankings are between months (O(n log n)).
*   **Max Subarray:** Finds the worst overspend streak by analyzing daily spend vs. average (O(n log n)).
*   **Majority Element:** Uses Boyer-Moore voting to find dominant spending categories (O(n)).
*   **Closest Pair of Points:** Detects suspicious duplicate expenses within tolerance limits (O(n log n)).

### 3. Order Statistics
*   **Randomized Quickselect:** Expected O(n) time to find medians, 90th percentiles, and Top-K expenses.
*   **Median of Medians:** Deterministic O(n) selection variant.
*   **IQR Outliers:** Uses 1.5x Interquartile Range to flag extreme expenses (e.g., a laptop purchase among daily chai expenses).

### 4. Greedy Optimisation
*   **Fractional Knapsack:** Maximises "value" when funding wishlist items on a limited monthly savings budget.
*   **Job Sequencing with Deadlines:** Maximises avoided late fees when scheduling bill payments using Union-Find.
*   **Coin/Note Change:** Greedy breakdown for Indian Rupee denominations.
*   **Min-Transaction Settlement:** Uses two Max-Heaps to settle roommate debts with the minimum number of transactions.
*   **Interval Scheduling:** Picks the maximum number of non-overlapping work shifts.
*   **Huffman Coding:** Compresses the exported expense log text.

### 5. Custom Data Structures
*   **Heaps:** MinHeap and MaxHeap (built from scratch, used in settlement and Huffman).
*   **Trie:** For fast autocomplete of merchant/expense descriptions.
*   **Union-Find:** Disjoint-set with path compression and union by rank.
*   **Fenwick Tree:** Binary Indexed Tree for O(log n) prefix sum updates.
*   **Stacks, Queues, Linked Lists.**

---

## 🛠️ Tech Stack
*   **Backend:** Python 3.10, FastAPI, Uvicorn, SQLite3 (native).
*   **Frontend:** HTML5, CSS3, Vanilla JavaScript, Chart.js.
*   **Testing:** Pytest (149+ tests covering correctness and edge cases).
*   **Benchmarking:** Matplotlib (generates empirical complexity graphs).
*   **Environment:** PowerShell (Windows), Git.

---

## 📂 Project Structure
```text
BudgetTracker/
├── backend/
│   ├── algorithms/      # Pure, hand-written algorithms (no built-ins)
│   ├── services/        # Business logic and database glue
│   ├── main.py          # FastAPI routes
│   ├── db.py            # SQLite connection and schema
│   └── seed.py          # Generates 205 realistic test expenses
├── frontend/
│   ├── index.html       # UI Layout (8 pages)
│   ├── css/style.css    # Dark theme styling
│   └── js/              # App logic and API wrappers
├── benchmarks/
│   └── run_benchmarks.py# Generates 5 empirical complexity graphs
├── tests/               # Pytest suites for all algorithms and services
├── report/              # Detailed project report with proofs and pseudocode
└── requirements.txt
