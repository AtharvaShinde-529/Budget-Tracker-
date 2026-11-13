"""Operation counters shared by every algorithm. No algorithm imports anything else."""


class Stats:
    """Mutable counter object passed through algorithms.

    Every algorithm returns (result, stats) so the UI and benchmarks can show
    comparisons, swaps, calls, recursion depth and any algorithm-specific counters.
    """

    __slots__ = ("comparisons", "swaps", "calls", "_depth", "max_depth", "extra")

    def __init__(self):
        self.comparisons = 0
        self.swaps = 0
        self.calls = 0
        self._depth = 0
        self.max_depth = 0
        self.extra = {}

    def enter(self):
        self.calls += 1
        self._depth += 1
        if self._depth > self.max_depth:
            self.max_depth = self._depth

    def exit(self):
        self._depth -= 1

    def as_dict(self):
        return {
            "comparisons": self.comparisons,
            "swaps": self.swaps,
            "calls": self.calls,
            "max_depth": self.max_depth,
            **self.extra,
        }

    def __repr__(self):
        return f"Stats({self.as_dict()})"
