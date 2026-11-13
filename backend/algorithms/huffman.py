"""Huffman coding for compressing the exported expense log."""

from backend.algorithms.structures import MinHeap
from backend.instrumentation import Stats


class _HNode:
    __slots__ = ("char", "freq", "left", "right", "order")

    def __init__(self, char=None, freq=0, left=None, right=None, order=0):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right
        self.order = order


def build_huffman(text_or_freqs, stats=None):
    """Build Huffman codes from a string or a frequency dict.
    Returns (codes: {char: bitstring}, root: _HNode, Stats).
    """
    stats = stats or Stats()
    if isinstance(text_or_freqs, str):
        freqs = {}
        for ch in text_or_freqs:
            freqs[ch] = freqs.get(ch, 0) + 1
    else:
        freqs = dict(text_or_freqs)

    if not freqs:
        return {}, None, stats

    if len(freqs) == 1:
        only = next(iter(freqs))
        root = _HNode(char=only, freq=freqs[only], order=0)
        return {only: "0"}, root, stats

    heap = MinHeap(key=lambda n: (n.freq, n.order))
    order_counter = 0
    for ch, f in freqs.items():
        heap.push(_HNode(char=ch, freq=f, order=order_counter))
        order_counter += 1

    while len(heap) > 1:
        a = heap.pop()
        b = heap.pop()
        merged = _HNode(freq=a.freq + b.freq, left=a, right=b, order=order_counter)
        order_counter += 1
        heap.push(merged)
        stats.calls += 1

    root = heap.pop()

    codes = {}
    def dfs(node, prefix):
        if node.char is not None:
            codes[node.char] = prefix or "0"
            return
        if node.left:
            dfs(node.left, prefix + "0")
        if node.right:
            dfs(node.right, prefix + "1")
    dfs(root, "")

    stats.extra = {"unique_chars": len(freqs)}
    return codes, root, stats


def huffman_encode(text, codes, stats=None):
    """Encode text using codes. Returns (bits, Stats)."""
    stats = stats or Stats()
    parts = []
    for ch in text:
        if ch not in codes:
            raise ValueError(f"char {ch!r} not in codes")
        parts.append(codes[ch])
        stats.comparisons += 1
    return "".join(parts), stats


def huffman_decode(bits, root, stats=None):
    """Decode bits using the Huffman tree. Returns (text, Stats)."""
    stats = stats or Stats()
    if root is None:
        return "", stats
    # Single-symbol case: the "tree" is just one leaf, so every bit maps to it.
    if root.char is not None:
        return root.char * len(bits), stats
    chars = []
    node = root
    for b in bits:
        if b == "0":
            node = node.left
        elif b == "1":
            node = node.right
        else:
            raise ValueError(f"invalid bit {b!r}")
        stats.comparisons += 1
        if node is not None and node.char is not None:
            chars.append(node.char)
            node = root
    if node is not root and (node is None or node.char is None):
        raise ValueError("incomplete bit sequence")
    return "".join(chars), stats


def is_prefix_free(codes):
    """True if no code is a prefix of another."""
    keys = list(codes.keys())
    for i in range(len(keys)):
        for j in range(len(keys)):
            if i == j:
                continue
            if codes[keys[i]].startswith(codes[keys[j]]):
                return False
    return True

