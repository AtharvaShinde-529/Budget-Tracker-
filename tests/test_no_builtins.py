"""Guard: backend/algorithms/*.py must be hand-written.

Uses AST parsing instead of regex so docstrings and comments can safely
mention built-in names while real calls still trip the check.

Banned in backend/algorithms/:
  - calls to sorted()
  - calls to x.sort()
  - imports of heapq, itertools, bisect, collections
"""

import ast
import pathlib

ALGO_DIR = pathlib.Path(__file__).resolve().parents[1] / "backend" / "algorithms"

BANNED_MODULES = {"heapq", "itertools", "bisect", "collections"}
BANNED_CALL_NAMES = {"sorted"}


def _scan(path: pathlib.Path):
    """Return list of (lineno, description) for banned uses in one file."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in BANNED_CALL_NAMES:
                hits.append((node.lineno, f"call to {f.id}()"))
            elif isinstance(f, ast.Attribute) and f.attr == "sort":
                hits.append((node.lineno, "call to .sort()"))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BANNED_MODULES:
                    hits.append((node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in BANNED_MODULES:
                    hits.append((node.lineno, f"from {node.module} import ..."))
    return hits


def test_algorithms_are_hand_written():
    problems = []
    for path in sorted(ALGO_DIR.glob("*.py")):
        for lineno, desc in _scan(path):
            problems.append(f"{path.name}:{lineno}  {desc}")
    assert not problems, "Banned uses in algorithms/:\n" + "\n".join(problems)


def test_self_check_catches_fake_violation(tmp_path):
    """Prove the scanner actually fires on a real violation."""
    fake = ALGO_DIR / "_fake_violation.py"
    fake.write_text(
        "def f(xs):\n"
        "    import heapq\n"
        "    return sorted(xs)\n",
        encoding="utf-8",
    )
    try:
        hits = _scan(fake)
        descs = " ".join(d for _, d in hits)
        assert "sorted()" in descs
        assert "heapq" in descs
    finally:
        fake.unlink()
