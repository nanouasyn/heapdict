from functools import partial
from typing import (
    TypeVar,
    Mapping,
    MutableMapping,
    Dict,
    Tuple,
    List,
    Iterable
)

K = TypeVar('K')
P = TypeVar('P')


class HeapDict(MutableMapping[K, P]):

    def __init__(self, iterable=None, *, max: bool = False): # noqa
        self._heap: List[Tuple[K, P]] = []
        self._keys: Dict[K, int] = {}
        self._max = max
        # TODO: инициализация кучи за O(N)
        if isinstance(iterable, Mapping):
            for k, v in iterable.items():
                self[k] = v
        elif isinstance(iterable, Iterable):
            for k, v in iterable:
                self[k] = v
        elif iterable is not None:
            raise TypeError(f'{type(iterable).__qualname__!r} object is not iterable')

    @staticmethod
    def fromkeys(iterable, value, *, reverse: bool = False) -> 'HeapDict':
        return HeapDict(((k, value) for k in iterable), max=reverse)

    def _swap(self, i: int, j: int) -> None:
        self._keys[self._heap[i][0]], self._keys[self._heap[j][0]] = j, i
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _sift_down(self, i: int) -> None:
        select_next = partial([max, min][self._max], key=lambda i: self._heap[i][1])
        while True:
            next_index = select_next(x for x in [i, (i - 1) // 2] if x >= 0)
            if next_index == i:
                return
            self._swap(i, next_index)
            i = next_index

    def _sift_up(self, i: int) -> None:
        select_next = partial([min, max][self._max], key=lambda i: self._heap[i][1])
        while True:
            next_index = select_next(x for x in [i, 2 * i + 1, 2 * i + 2] if x < len(self._heap))
            if next_index == i:
                return
            self._swap(i, next_index)
            i = next_index

    # Приватный метод проверки сохранения инвариантов кучи, предназначенный для тестирования,
    # по аналогии с соответствующим методом _check в sortedcontainers.
    def _check_invariants(self) -> None:
        # Куча упорядочена верно.
        for i in range(1, len(self._heap)):
            if not self._max:
                assert self._heap[i][1] >= self._heap[(i - 1) // 2][1]
            else:
                assert self._heap[i][1] <= self._heap[(i - 1) // 2][1]
        # Словарь и куча согласованны.
        assert len(self._keys) == len(self._heap)
        assert all(self._heap[i][0] == key for key, i in self._keys.items())
        assert all(self._keys[key] == i for i, (key, _) in enumerate(self._heap))

    def __len__(self) -> int:
        return len(self._keys)

    def __iter__(self) -> Iterable[K]:
        yield from self._keys

    def __getitem__(self, key: K) -> P:
        return self._heap[self._keys[key]][1]

    def __setitem__(self, key: K, priority: P) -> None:
        # Если ключ уже известен, мы могли бы удалить пару ключ-приоритет и заново вставить новую
        # пару с тем же ключом, но новым приоритетом. Однако, это сломает сохранение порядка
        # вставки, поддерживаемое словарём. Поэтому мы просто вставим новый узел в кучу в ту же
        # позицию, где сейчас находится узел с соответствующим узлом, и выполним просеивание.
        if (i := self._keys.get(key, None)) is not None:
            self._heap[i] = (key, priority)
            self._sift_down(i)
            self._sift_up(i)
        else:
            i = len(self._heap)
            self._heap.append((key, priority))
            self._keys[key] = i
            self._sift_down(i)

    def __delitem__(self, key: K) -> None:
        i = self._keys[key]
        self._swap(i, len(self._heap) - 1)
        self._keys.pop(key)
        self._heap.pop()
        if i < len(self._heap):
            self._sift_down(i)
            self._sift_up(i)

    def __repr__(self) -> str:
        items = ', '.join(f'{key!r}: {priority!r}' for key, priority in self.items())
        items = f'{{{items}}}'
        max_kwarg = f'max={self._max}' if self._max is True else None
        params = ', '.join(p for p in [items, max_kwarg] if p is not None)
        return f'{type(self).__name__}({params})'

    def __copy__(self) -> 'HeapDict':
        return self.copy()

    def copy(self) -> 'HeapDict':
        new_heap_dict = HeapDict(max=self._max)
        new_heap_dict._heap = self._heap.copy()
        new_heap_dict._keys = self._keys.copy()
        return new_heap_dict

    def popitem(self) -> tuple[K, P]:
        try:
            key, priority = self._heap[0]
        except IndexError:
            raise KeyError("can't pop item: dictionary is empty")
        del self[key]
        return key, priority

    # Родительский clear удалял бы каждый ключ по очереди, что привело бы к накладным расходам
    # на восстановление свойств кучи после каждого удаления. Поэтому мы переопределяем этот
    # метод более эффективной реализацией.
    def clear(self) -> None:
        self._heap.clear()
        self._keys.clear()

    def peekitem(self) -> tuple[K, P]:
        try:
            return self._heap[0]
        except IndexError:
            raise KeyError("can't peek item: dictionary is empty")
