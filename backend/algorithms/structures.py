"""Hand-written data structures. No heapq, no collections.

Everything here is written by hand so we can defend each one in the viva.
"""


class MinHeap:
    """Binary min-heap. O(log n) push/pop, O(1) peek."""

    def __init__(self, key=None):
        self._a = []
        self._key = key or (lambda x: x)

    def __len__(self):
        return len(self._a)

    def push(self, item):
        a = self._a
        a.append(item)
        i = len(a) - 1
        while i > 0:
            p = (i - 1) // 2
            if self._key(a[p]) <= self._key(a[i]):
                break
            a[p], a[i] = a[i], a[p]
            i = p

    def peek(self):
        if not self._a:
            raise IndexError("peek from empty heap")
        return self._a[0]

    def pop(self):
        a = self._a
        if not a:
            raise IndexError("pop from empty heap")
        top = a[0]
        last = a.pop()
        if a:
            a[0] = last
            i, n = 0, len(a)
            while True:
                l, r, small = 2 * i + 1, 2 * i + 2, i
                if l < n and self._key(a[l]) < self._key(a[small]):
                    small = l
                if r < n and self._key(a[r]) < self._key(a[small]):
                    small = r
                if small == i:
                    break
                a[i], a[small] = a[small], a[i]
                i = small
        return top


class MaxHeap:
    """Max-heap via a MinHeap with a negated key."""

    def __init__(self, key=None):
        self._inner_key = key or (lambda x: x)
        self._h = MinHeap(key=lambda x: -self._inner_key(x))

    def __len__(self):
        return len(self._h)

    def push(self, x):
        self._h.push(x)

    def pop(self):
        return self._h.pop()

    def peek(self):
        return self._h.peek()


class Stack:
    def __init__(self):
        self._a = []

    def push(self, x):
        self._a.append(x)

    def pop(self):
        if not self._a:
            raise IndexError("pop from empty stack")
        return self._a.pop()

    def peek(self):
        if not self._a:
            raise IndexError("peek from empty stack")
        return self._a[-1]

    def __len__(self):
        return len(self._a)

    def __bool__(self):
        return bool(self._a)


class Queue:
    """FIFO queue using a head index (amortised O(1) per op)."""

    def __init__(self):
        self._a = []
        self._head = 0

    def enqueue(self, x):
        self._a.append(x)

    def dequeue(self):
        if self._head >= len(self._a):
            raise IndexError("dequeue from empty queue")
        x = self._a[self._head]
        self._head += 1
        if self._head > 32 and self._head * 2 > len(self._a):
            self._a = self._a[self._head:]
            self._head = 0
        return x

    def __len__(self):
        return len(self._a) - self._head

    def __bool__(self):
        return len(self) > 0


class Node:
    __slots__ = ("value", "next")

    def __init__(self, value, next=None):
        self.value = value
        self.next = next


class LinkedList:
    """Singly linked list with append, delete, and Josephus elimination."""

    def __init__(self):
        self.head = None
        self._n = 0

    def append(self, value):
        node = Node(value)
        if self.head is None:
            self.head = node
        else:
            cur = self.head
            while cur.next is not None:
                cur = cur.next
            cur.next = node
        self._n += 1

    def __len__(self):
        return self._n

    def to_list(self):
        out = []
        cur = self.head
        while cur is not None:
            out.append(cur.value)
            cur = cur.next
        return out


class TrieNode:
    __slots__ = ("children", "is_word", "freq")

    def __init__(self):
        self.children = {}
        self.is_word = False
        self.freq = 0


class Trie:
    """Prefix tree for autocomplete of merchant names / descriptions."""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, weight=1):
        node = self.root
        for ch in word.lower():
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_word = True
        node.freq += weight

    def _walk(self, prefix):
        node = self.root
        for ch in prefix.lower():
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def startswith(self, prefix, limit=10):
        node = self._walk(prefix)
        if node is None:
            return []
        out, buf = [], []

        def dfs(n):
            if len(out) >= limit:
                return
            if n.is_word:
                out.append("".join(buf))
            for ch, child in n.children.items():
                buf.append(ch)
                dfs(child)
                buf.pop()

        dfs(node)
        return out


class UnionFind:
    """Disjoint-set with path halving and union by rank. Nearly O(1) per op."""

    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        self.components -= 1
        return True


class Fenwick:
    """Fenwick tree (binary indexed tree): point update, prefix and range sum. O(log n)."""

    def __init__(self, values):
        self.n = len(values)
        self.tree = [0] * (self.n + 1)
        for i, v in enumerate(values, 1):
            self._add(i, v)

    def _add(self, i, delta):
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def update(self, idx0, delta):
        self._add(idx0 + 1, delta)

    def prefix(self, idx0):
        i, s = idx0 + 1, 0
        while i > 0:
            s += self.tree[i]
            i -= i & -i
        return s

    def range_sum(self, lo, hi):
        if hi < lo:
            return 0
        return self.prefix(hi) - (self.prefix(lo - 1) if lo > 0 else 0)
