"""Fingerprint table: hash table with SEPARATE CHAINING (CO4).
Every bucket is a singly LINKED LIST (CO2) of Entry cells."""


class Entry:
    """One linked-list cell: a subtree fingerprint, the file it came from, and the node."""

    def __init__(self, fingerprint, file_id, node):
        self.fingerprint = fingerprint
        self.file_id = file_id
        self.node = node
        self.next = None  # CO2: link to the next cell in the same bucket


class HashTable:
    MAX_LOAD = 0.75

    def __init__(self, capacity=64):
        self.capacity = capacity
        self.count = 0
        self.buckets = [None] * capacity  # each slot holds the head of a linked list

    def _index(self, fingerprint):
        return fingerprint % self.capacity  # CO4: hash function -> bucket index

    def insert(self, fingerprint, file_id, node):
        """O(1): link the new entry in at the head of its bucket."""
        entry = Entry(fingerprint, file_id, node)
        i = self._index(fingerprint)
        entry.next = self.buckets[i]  # CO2: insert at the head of the linked list
        self.buckets[i] = entry
        self.count += 1
        if self.load_factor() > self.MAX_LOAD:
            self.rehash()

    def get_bucket(self, fingerprint):
        """Return the entries whose fingerprint equals `fingerprint` (walks one chain)."""
        found = []
        entry = self.buckets[self._index(fingerprint)]
        while entry is not None:  # CO2: linked-list traversal
            if entry.fingerprint == fingerprint:
                found.append(entry)
            entry = entry.next
        return found

    def load_factor(self):
        return self.count / self.capacity

    def rehash(self):
        """Double the capacity and move every entry to its new bucket. O(n)."""
        old = self.buckets
        self.capacity *= 2
        self.buckets = [None] * self.capacity
        for head in old:
            entry = head
            while entry is not None:
                nxt = entry.next
                i = self._index(entry.fingerprint)
                entry.next = self.buckets[i]
                self.buckets[i] = entry
                entry = nxt

    def chains(self):
        """Yield every non-empty bucket as a Python list of its entries."""
        for head in self.buckets:
            cells = []
            entry = head
            while entry is not None:
                cells.append(entry)
                entry = entry.next
            if cells:
                yield cells


class _Cell:
    """One linked-list cell of a HashMap bucket (CO2)."""

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


def key_hash(key):
    """Stable integer for an int, str or tuple key (Python's hash() is randomised per run)."""
    if isinstance(key, int):
        return key
    if isinstance(key, tuple):
        h = 0
        for part in key:
            h = (h * 1000003 + key_hash(part)) % (2 ** 61 - 1)
        return h
    h = 0
    for ch in str(key):
        h = (h * 131 + ord(ch)) % (2 ** 61 - 1)
    return h


class HashMap:
    """Key -> value map, separate chaining (CO4) with linked-list buckets (CO2)."""
    MAX_LOAD = 0.75

    def __init__(self, capacity=16):
        self.capacity = capacity
        self.count = 0
        self.buckets = [None] * capacity

    def _find(self, key):
        cell = self.buckets[key_hash(key) % self.capacity]
        while cell is not None:  # CO2: walk the chain
            if cell.key == key:
                return cell
            cell = cell.next
        return None

    def get(self, key, default=None):
        cell = self._find(key)
        return default if cell is None else cell.value

    def put(self, key, value):
        cell = self._find(key)
        if cell is not None:
            cell.value = value
            return
        i = key_hash(key) % self.capacity
        cell = _Cell(key, value)
        cell.next = self.buckets[i]
        self.buckets[i] = cell
        self.count += 1
        if self.count / self.capacity > self.MAX_LOAD:
            self._grow()

    def remove(self, key):
        i = key_hash(key) % self.capacity
        prev, cell = None, self.buckets[i]
        while cell is not None:
            if cell.key == key:
                if prev is None:
                    self.buckets[i] = cell.next
                else:
                    prev.next = cell.next  # CO2: unlink from the chain
                self.count -= 1
                return
            prev, cell = cell, cell.next

    def __contains__(self, key):
        return self._find(key) is not None

    def __len__(self):
        return self.count

    def items(self):
        for head in self.buckets:
            cell = head
            while cell is not None:
                yield cell.key, cell.value
                cell = cell.next

    def _grow(self):
        old = list(self.items())
        self.capacity *= 2
        self.buckets = [None] * self.capacity
        self.count = 0
        for k, v in old:
            self.put(k, v)


class HashSet:
    """Set of keys, stored as a HashMap with value True."""

    def __init__(self, keys=()):
        self._map = HashMap()
        for k in keys:
            self.add(k)

    def add(self, key):
        self._map.put(key, True)

    def discard(self, key):
        self._map.remove(key)

    def __contains__(self, key):
        return key in self._map

    def __len__(self):
        return len(self._map)

    def __iter__(self):
        for k, _ in self._map.items():
            yield k

    def copy(self):
        return HashSet(self)

    def update(self, keys):
        for k in keys:
            self.add(k)
