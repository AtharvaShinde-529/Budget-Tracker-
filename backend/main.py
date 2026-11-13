"""FastAPI entrypoint. Grows each step; this version wires /health, /registry and demo routes."""

import random

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from backend import registry
from backend.algorithms import searching, sorting

app = FastAPI(title="BudgetTracker - DAA Project", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/registry")
def get_registry():
    return registry.REGISTRY


@app.get("/demo/sort")
def demo_sort(n: int = 20, seed: int = 0):
    """Run every sorting algorithm on the same random input and report statistics."""
    rng = random.Random(seed)
    data = [rng.randint(-500, 500) for _ in range(n)]
    reference = sorted(data)  # used only as an oracle here, fine in the API layer

    results = {}
    for name, fn in [
        ("insertion_sort", sorting.insertion_sort),
        ("selection_sort", sorting.selection_sort),
        ("bubble_sort",    sorting.bubble_sort),
        ("merge_sort",     sorting.merge_sort),
        ("quick_sort",     sorting.quick_sort),
        ("heap_sort",      sorting.heap_sort),
        ("counting_sort",  sorting.counting_sort),
        ("radix_sort",     sorting.radix_sort),
    ]:
        out, stats = fn(data)
        results[name] = {"sorted_ok": out == reference, "stats": stats.as_dict()}

    return {"n": n, "input": data, "results": results}


@app.get("/demo/search")
def demo_search(n: int = 50, seed: int = 0, target: int = 100):
    rng = random.Random(seed)
    data, _ = sorting.merge_sort([rng.randint(0, 200) for _ in range(n)])
    idx, stats = searching.binary_search(data, target)
    lo, hi, _ = searching.range_indices(data, 50, 150)
    return {
        "sorted": data,
        "target": target,
        "index": idx,
        "comparisons": stats.comparisons,
        "range_50_150": data[lo:hi],
    }


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html><body style="font-family: system-ui; padding: 2rem; max-width: 40rem; margin: auto;">
    <h1>BudgetTracker - DAA Project</h1>
    <p>Backend is running. Try:</p>
    <ul>
      <li><a href="/docs">/docs</a> - interactive API docs</li>
      <li><a href="/registry">/registry</a> - algorithm metadata</li>
      <li><a href="/demo/sort?n=50">/demo/sort</a> - all sorts with stats</li>
      <li><a href="/demo/search?n=50">/demo/search</a> - binary search + range</li>
    </ul>
    <p>UI comes in Step 4. This is just proof the API is up.</p>
    </body></html>
    """
