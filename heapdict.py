import inspect
from functools import partial, wraps
from itertools import chain
from typing import Mapping, MutableMapping, Iterable


__all__ = ['HeapDict']


def default_empty_behavior(func):
    """Collection method decorated with this decorator not called if the
    collection is empty. Instead, the value of the *default* parameter is
    returned if it is specified. If the collection is empty, but *default* is
    not specified, ``ValueError`` is raised.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self:
            if "default" in kwargs:
                del kwargs["default"]
            return func(self, *args, **kwargs)
        if "default" not in kwargs:
            raise ValueError("collection is empty")
        return kwargs["default"]

    signature = inspect.signature(func)
    parameters = signature.parameters.values()
    if not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters):
        wrapper.__signature__ = signature.replace(
            parameters=[
                *parameters,
                inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD),
            ]
        )

    return wrapper


class HeapDict(MutableMapping):
    """Priority queue that supports retrieving and extraction keys with the
    lowest/highest priority and changing priorities for arbitrary keys.

    Implements the ``dict`` interface, the keys of which are priority queue
    elements, and the values are priorities of these elements. All keys must be
    hashable, and all values must be comparable to each other. The preservation
    of the insertion order is guaranteed in the same way as it is guaranteed
    for built-in dictionaries.
    """

    def __init__(self, iterable=None, /, **kwargs):
        """Initialize priority queue instance.

        Optional *iterable* argument provides an initial iterable of pairs
        (key, priority) or {key: priority} mapping to initialize the priority
        queue.

        Other optional keyword arguments will be added in a queue as pairs:
        their names will be interpreted as keys, and their values will be
        interpreted as priorities.

        If there are several pairs with the same keys, only the last one will
        be included in the dictionary.

        >>> heapdict = HeapDict([('a', 1), ('b', 2), ('a', 3)], b=4, c=5)
        HeapDict({'a': 3, 'b': 4, 'c': 5})

        Runtime complexity: `O(n)`.
        """
        if iterable is None:
            iterable = ()
        elif isinstance(iterable, Mapping):
            iterable = iterable.items()
        elif not isinstance(iterable, Iterable):
            raise TypeError(
                f"{type(iterable).__qualname__!r} object is not iterable"
            )

        self._priorities = dict(chain(iterable, kwargs.items()))
        self._heap = list(self._priorities)
        self._indexes = {k: v for v, k in enumerate(self._priorities)}

        # Restoring the heap invariant.
        push_down = self._push_down
        for i in reversed(range(len(self._heap) // 2)):
            push_down(i)

    @classmethod
    def fromkeys(cls, iterable, value, /):
        """Create a new priority queue with keys from *iterable* and priorities
        set to *value*.

        >>> HeapDict.fromkeys("abcdef", 0)
        HeapDict('a': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0)

        RuntimeComplexity: `O(n)`.
        """
        h = HeapDict()
        h._priorities = dict.fromkeys(iterable, value)
        h._heap = list(h._priorities)
        h._indexes = {k: v for v, k in enumerate(h._priorities)}
        # All priorities are equal, so the heap doesn't need to be fixed.
        return h

    def _swap(self, i, j):
        indexes, heap = self._indexes, self._heap
        indexes[heap[i]], indexes[heap[j]] = j, i
        heap[i], heap[j] = heap[j], heap[i]

    def _get_level(self, i):
        return (i + 1).bit_length() - 1

    def _get_parent(self, i):
        return (i - 1) // 2

    def _get_grandparent(self, i):
        return (i - 3) // 4

    def _with_children(self, i):
        yield i
        first = 2 * i + 1
        yield from range(first, min(len(self._heap), first + 2))

    def _with_grandchildren(self, i):
        yield i
        first = 4 * i + 3
        yield from range(first, min(len(self._heap), first + 4))

    def _get_selector(self, level):
        priorities, heap = self._priorities, self._heap
        selector = [min, max][level % 2]
        return partial(selector, key=lambda i: priorities[heap[i]])

    def _push_down(self, i):
        with_children = self._with_children
        with_grandchildren = self._with_grandchildren
        select = self._get_selector(self._get_level(i))
        while True:
            should_be_parent = select(with_children(i))
            if should_be_parent != i:
                self._swap(i, should_be_parent)

            should_be_grandparent = select(with_grandchildren(i))
            if should_be_grandparent == i:
                return
            self._swap(i, should_be_grandparent)
            i = should_be_grandparent

    def _push_up(self, i):
        parent = self._get_parent(i)
        if parent < 0:
            return
        select = self._get_selector(self._get_level(parent))
        if select(parent, i) == i:
            self._swap(i, parent)
            i = parent

        get_grandparent = self._get_grandparent
        select = self._get_selector(self._get_level(i))
        while (grandparent := get_grandparent(i)) >= 0:
            if select(grandparent, i) == grandparent:
                break
            self._swap(i, grandparent)
            i = grandparent

    def _get_max_index(self):
        length = len(self._heap)
        return self._get_selector(1)(1, 2) if length > 2 else length - 1

    @default_empty_behavior
    def min_item(self):
        """Return (key, priority) pair with the lowest priority.

        >>> heapdict = HeapDict({'a': 10, 'b': 5, 'c': 7})
        >>> heapdict.min_item()
        ('b', 5)

        The *default* keyword-only argument specifies an object to return if
        the dict is empty. If the dict is empty but *default* is not specified,
        a ``ValueError`` will be thrown.

        Runtime complexity: `O(1)`.
        """
        key = self._heap[0]
        priority = self._priorities[key]
        return key, priority

    @default_empty_behavior
    def pop_min_item(self):
        """Remove and return (key, priority) pair with the lowest priority.

        >>> heapdict = HeapDict({'a': 10, 'b': 5, 'c': 7})
        >>> heapdict.pop_min_item()
        ('b', 5)
        >>> heapdict
        HeapDict({'a': 10, 'c': 7})

        The *default* keyword-only argument specifies an object to return if
        the dict is empty. If the dict is empty but *default* is not specified,
        a ``ValueError`` will be thrown.

        Runtime complexity: `O(log(n))`.
        """
        key = self._heap[0]
        priority = self._priorities[key]
        del self[key]
        return key, priority

    @default_empty_behavior
    def max_item(self):
        """Return (key, priority) pair with the highest priority.

        >>> heapdict = HeapDict({'a': 10, 'b': 5, 'c': 7})
        >>> heapdict.max_item()
        ('a', 10)

        The *default* keyword-only argument specifies an object to return if
        the dict is empty. If the dict is empty but *default* is not specified,
        a ``ValueError`` will be thrown.

        Runtime complexity: `O(1)`.
        """
        key = self._heap[self._get_max_index()]
        priority = self._priorities[key]
        return key, priority

    @default_empty_behavior
    def pop_max_item(self):
        """Remove and return (key, priority) pair with the highest priority.

        >>> heapdict = HeapDict({'a': 10, 'b': 5, 'c': 7})
        >>> heapdict.pop_max_item()
        ('a', 10)
        >>> heapdict
        HeapDict({'b': 5, 'c': 7})

        The *default* keyword-only argument specifies an object to return if
        the dict is empty. If the dict is empty but *default* is not specified,
        a ``ValueError`` will be thrown.

        Runtime complexity: `O(log(n))`.
        """
        key = self._heap[self._get_max_index()]
        priority = self._priorities[key]
        del self[key]
        return key, priority

    def __getitem__(self, key):
        """Return priority of *key*.

        >>> heapdict = HeapDict({'a': 10, 'b': 5, 'c': 7})
        >>> heapdict['a']
        10
        >>> heapdict['b']
        5

        Raises ``KeyError`` if *key* is not in the dictionary.

        RuntimeComplexity: `O(1)`.
        """
        return self._priorities[key]

    def __setitem__(self, key, priority):
        """Insert *key* with a specified *priority* if *key* is not in the
        dictionary, or change priority of existing *key* to *priority*
        otherwise.

        >>> heapdict = HeapDict({'a': 10, 'b': 5, 'c': 7})
        >>> heapdict['d'] = 20
        >>> heapdict['a'] = 0
        >>> heapdict
        HeapDict({'a': 0, 'b': 5, 'c': 7, 'd': 20})

        RuntimeComplexity: `O(log(n))`.
        """
        self._priorities[key] = priority
        if key in self._indexes:
            i = self._indexes[key]
            self._push_up(i)
            self._push_down(i)
        else:
            self._heap.append(key)
            self._indexes[key] = i = len(self._heap) - 1
            self._push_up(i)

    def __delitem__(self, key):
        """Remove *key* from the dictionary.

        >>> heapdict = HeapDict({'a': 10, 'b': 5, 'c': 7})
        >>> del heapdict['b']
        >>> heapdict
        HeapDict({'a': 10, 'c': 7})

        Raises ``KeyValue`` if *key* is not in the dictionary.

        RuntimeComplexity: `O(log(n))`.
        """
        i = self._indexes[key]
        self._priorities.pop(key)
        self._indexes.pop(key)
        end_key = self._heap.pop()
        if i < len(self._heap):
            self._heap[i], self._indexes[end_key] = end_key, i
            self._push_up(i)
            self._push_down(i)

    def popitem(self):
        """Remove and return a (key, priority) pair inserted last as a 2-tuple.

        Raises ``ValueError`` if dictionary is empty.

        Runtime complexity: `O(log(n))`.
        """
        if not self:
            raise ValueError("collection is empty")
        key = next(reversed(self._priorities))
        priority = self.pop(key)
        return key, priority

    def __len__(self):
        """Return the number of keys.

        Runtime complexity: `O(1)`
        """
        return len(self._heap)

    def __iter__(self):
        """Return keys iterator in the insertion order."""
        return iter(self._priorities)

    def __reversed__(self):
        """Return keys iterator in the reverse insertion order."""
        return reversed(self._priorities)

    def __or__(self, other):
        """Return union of this dict and *other* mapping interpreted as
        ``HeapDict`` instance (self | other).

        The resulting ``HeapDict`` will be a copy of this dict, into which all
        (key, priority) pairs from *other* have been inserted.
        """
        if not isinstance(other, Mapping):
            return NotImplemented
        return type(self)(chain(self.items(), other.items()))

    def __ror__(self, other):
        """Return union of this dict and *other* mapping interpreted as
        ``HeapDict`` instance (other | self).

        The resulting ``HeapDict`` will be a copy of *other*, into which all
        (key, priority) pairs from this dict have been inserted.
        """
        if not isinstance(other, Mapping):
            return NotImplemented
        return type(self)(chain(other.items(), self.items()))

    def clear(self):
        """Remove all items from dict."""
        self._priorities.clear()
        self._heap.clear()
        self._indexes.clear()

    def copy(self):
        """Return a shallow copy of dict."""
        heapdict = type(self)()
        heapdict._priorities = self._priorities.copy()
        heapdict._heap = self._heap.copy()
        heapdict._indexes = self._indexes.copy()
        return heapdict

    def __copy__(self):
        """Return a shallow copy of dict."""
        return self.copy()

    def __repr__(self) -> str:
        """Return repr(self)."""
        if not self:
            return f"{type(self).__name__}()"
        return f"{type(self).__name__}({self._priorities})"
