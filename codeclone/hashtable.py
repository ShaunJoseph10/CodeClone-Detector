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
