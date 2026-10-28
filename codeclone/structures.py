"""Hand-written Stack and Queue used across the project (CO1)."""


class Stack:
    """LIFO stack. A Python list is used only as raw storage; push/pop are at the end -> O(1)."""

    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def __len__(self):
        return len(self._items)


class _QNode:
    """One cell of the queue's singly linked list."""

    def __init__(self, item):
        self.item = item
        self.next = None


class Queue:
    """FIFO queue built on a singly linked list with head and tail pointers.
    enqueue at tail, dequeue at head -> both O(1)."""

    def __init__(self):
        self._head = None
        self._tail = None
        self._size = 0

    def enqueue(self, item):
        cell = _QNode(item)
        if self._tail is None:
            self._head = self._tail = cell
        else:
            self._tail.next = cell
            self._tail = cell
        self._size += 1

    def dequeue(self):
        if self._head is None:
            raise IndexError("dequeue from empty queue")
        cell = self._head
        self._head = cell.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        return cell.item

    def is_empty(self):
        return self._size == 0

    def __len__(self):
        return self._size
