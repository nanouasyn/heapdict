from functools import partial
from itertools import chain
from typing import Mapping, MutableMapping, Iterable


def use_docstring_of(target):
    """Return decorator that sets wrapped function doc-string the same as in
    target.

    >>> @use_docstring_of(dict.clear)
    ... def f(): ...
    >>> f.__doc__
    'D.clear() -> None.  Remove all items from D.'

    """

    def decorator(function):
        function.__doc__ = target.__doc__
        return function

    return decorator


class HeapDict(MutableMapping):
    """Priority queue that supports fast retrieving items with the lowest
    priority and fast changing priorities for arbitrary keys.

    Implements the ``dict`` interface, the keys of which are priority queue
    elements, and the values are priorities of these elements. Items are
    extracted with ``popitem`` method in ascending order of their priority.

    The search of the lowest priority item has `O(1)` runtime complexity. The
    extraction of this item or arbitraty item by key has complexity of
    `O(log(n))`. Adding or removing items or changing priority of existing keys
    has also `O(log(n))` runtime complexity. In other respects ``HeapDict``
    has the same runtime complexity as the built-in ``dict``.

    """

    def __init__(self, iterable=None, /, *, maxheap=False, **kwargs):
        """Initialize priority queue instance.

        Optional *iterable* argument provides an initial iterable of pairs
        (key, priority) or {key: priority} mapping to initialize the priority
        queue.

        By default, a min heap is created, but if *maxheap* parameter is
        ``True``, then it is max heap, that is, the elements with the
        highest priority are extracted first.

        Other optional keyword arguments will be added in a queue as pairs:
        their names will be interpreted as keys, and their values will be
        interpreted as priorities.

        Runtime complexity: `O(n)`

        """
        if iterable is None:
            iterable = ()
        elif isinstance(iterable, Mapping):
            iterable = iterable.items()
        elif not isinstance(iterable, Iterable):
            raise TypeError(
                f"{type(iterable).__qualname__!r} object is not iterable"
            )
        iterable = chain(iterable, kwargs.items())
        self._heap = []
        self._keys = {}
        self._maxheap = maxheap
        for key, priority in iterable:
            if (i := self._keys.get(key, None)) is not None:
                self._heap[i] = (key, priority)
            else:
                self._keys[key] = len(self._heap)
                self._heap.append((key, priority))
        for i in reversed(range(len(self._heap) // 2)):
            self._sift_up(i)

    @classmethod
    def fromkeys(cls, iterable, value, maxheap=False):
        """Create a new priority queue with keys from iterable and priorities
        set to value.

        By default, a min heap is created, but if *maxheap* parameter is
        ``True``, then it is max heap, that is, the elements with the
        highest priority are extracted first.
        """
        return cls(((k, value) for k in iterable), maxheap=maxheap)

    def _swap(self, i, j):
        self._keys[self._heap[i][0]], self._keys[self._heap[j][0]] = j, i
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _sift_up(self, i):
        select_next = partial(
            max if self.maxheap else min, key=lambda i: self._heap[i][1]
        )
        while True:
            next_index = select_next(
                x for x in [i, 2 * i + 1, 2 * i + 2] if x < len(self._heap)
            )
            if next_index == i:
                return
            self._swap(i, next_index)
            i = next_index

    def _sift_down(self, i):
        select_next = partial(
            min if self.maxheap else max, key=lambda i: self._heap[i][1]
        )
        while True:
            next_index = select_next(x for x in [i, (i - 1) // 2] if x >= 0)
            if next_index == i:
                return
            self._swap(i, next_index)
            i = next_index

    @property
    def maxheap(self):
        return self._maxheap

    @use_docstring_of(dict.__getitem__)
    def __getitem__(self, key):
        return self._heap[self._keys[key]][1]

    @use_docstring_of(dict.__setitem__)
    def __setitem__(self, key, priority):
        # Если ключ уже известен, мы могли бы удалить пару ключ-приоритет и
        # заново вставить новую пару с тем же ключом, но новым приоритетом.
        # Однако, это сломает сохранение порядка вставки, поддерживаемое
        # словарём. Поэтому мы просто вставим новый узел в кучу в ту же
        # позицию, где сейчас находится узел с соответствующим узлом, и
        # выполним просеивание.
        if (i := self._keys.get(key, None)) is not None:
            self._heap[i] = (key, priority)
            self._sift_down(i)
            self._sift_up(i)
        else:
            i = len(self._heap)
            self._heap.append((key, priority))
            self._keys[key] = i
            self._sift_down(i)

    @use_docstring_of(dict.__delitem__)
    def __delitem__(self, key):
        i = self._keys[key]
        self._swap(i, len(self._heap) - 1)
        self._keys.pop(key)
        self._heap.pop()
        if i < len(self._heap):
            self._sift_down(i)
            self._sift_up(i)

    def popitem(self):
        """Remove and return a (key, priority) pair as 2-tuple.

        Removed pair will be the pair with the lowest priority (or the highest
        if ``maxheap=True``).

        >>> heapdict = HeapDict({'x': 5, 'y': 1, 'z': 10})
        >>> heapdict
        HeapDict({'x': 5, 'y': 1, 'z': 10})
        >>> heapdict.popitem()
        ('y', 1)
        >>> heapdict # heapdict has changed
        HeapDict({'x': 5, 'z': 10})

        Runtime complexity: `O(log(n))`.

        :raises KeyError: if heapdict is empty

        """
        try:
            key, priority = self._heap[0]
        except IndexError:
            raise KeyError("can't pop item: heapdict is empty")
        del self[key]
        return key, priority

    def peekitem(self):
        """Return a (key, priority) pair as 2-tuple.

        Returned pair will be the pair with the lowest priority (or the highest
        if ``maxheap=True``).

        >>> heapdict = HeapDict({'x': 5, 'y': 1, 'z': 10})
        >>> heapdict
        HeapDict({'x': 5, 'y': 1, 'z': 10})
        >>> heapdict.peekitem()
        ('y', 1)
        >>> heapdict # heapdict has not changed
        HeapDict({'x': 5, 'y': 1, 'z': 10})

        Runtime complexity: `O(1)`

        :raises KeyError: if heapdict is empty

        """
        try:
            return self._heap[0]
        except IndexError:
            raise KeyError("can't peek item: heapdict is empty")

    @use_docstring_of(dict.__len__)
    def __len__(self):
        return len(self._keys)

    @use_docstring_of(dict.__iter__)
    def __iter__(self):
        yield from self._keys

    @use_docstring_of(dict.__or__)
    def __or__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return type(self)(
            chain(self.items(), other.items()), maxheap=self.maxheap
        )

    @use_docstring_of(dict.__ror__)
    def __ror__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return type(self)(
            chain(other.items(), self.items()), maxheap=self.maxheap
        )

    @use_docstring_of(dict.clear)
    def clear(self):
        self._heap.clear()
        self._keys.clear()

    @use_docstring_of(dict.copy)
    def copy(self):
        new_heap_dict = type(self)(maxheap=self.maxheap)
        new_heap_dict._heap = self._heap.copy()
        new_heap_dict._keys = self._keys.copy()
        return new_heap_dict

    @use_docstring_of(dict.copy)
    def __copy__(self):
        return self.copy()

    @use_docstring_of(dict.__repr__)
    def __repr__(self) -> str:
        items = (f"{key!r}: {priority!r}" for key, priority in self.items())
        items = ", ".join(items)
        args = [f"{{{items}}}"]
        if self.maxheap:
            args.append("maxheap=True")
        args = ", ".join(args)
        return f"{type(self).__name__}({args})"
