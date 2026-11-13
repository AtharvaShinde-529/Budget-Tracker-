"""Guard: backend/algorithms/*.py must be hand-written.

No built-in sort, heapq, itertools, bisect, or collections.
"""

import pathlib
import re

ALGO_DIR = pathlib.Path(__file__).resolve().parents[1] / "backend" / "algorithms"

BANNED = [
    (re.compile(r"\bsorted\("),                       "sorted()"),
    (re.compile(r"\.sort\("),                         ".sort()"),
    (re.compile(r"^\s*import\s+heapq"),               "import heapq"),
    (re.compile(r"^\s*from\s+heapq"),                 "from heapq"),
    (re.compile(r"^\s*import\s+itertools"),           "import itertools"),
    (re.compile(r"^\s*from\s+itertools"),             "from itertools"),
    (re.compile(r"^\s*import\s+bisect"),              "import bisect"),
    (re.compile(r"^\s*from\s+bisect"),                "from bisect"),
    (re.compile(r"^\s*import\s+collections\b"),       "import collections"),
    (re.compile(r"^\s*from\s+collections\s+import"),  "from collections import ..."),
]


def test_algorithms_are_hand_written():
    problems = []
    for path in sorted(ALGO_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8-sig")
        for lineno, line in enumerate(text.splitlines(), 1):
            for pat, name in BANNED:
                if pat.search(line):
                    problems.append(f"{path.name}:{lineno}  [{name}]  {line.strip()}")
    assert not problems, "Banned patterns in algorithms/:\n" + "\n".join(problems)
