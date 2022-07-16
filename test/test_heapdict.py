import pytest
import copy
from hypothesis import (
    given,
    strategies as st
)

from heapdict import (
    MinHeapDict,
    MaxHeapDict
)


class TestHeapDict:

    def check_invariants(self, heapdict: MaxHeapDict | MinHeapDict):
        assert len(heapdict._keys) == len(heapdict._heap)
        assert all(heapdict._heap[i][0] == key for key, i in heapdict._keys.items())
        assert all(heapdict._keys[key] == i for i, (key, _) in enumerate(heapdict._heap))
        for i in range(1, len(heapdict._heap)):
            if isinstance(heapdict, MinHeapDict):
                assert heapdict._heap[i][1] >= heapdict._heap[(i - 1) // 2][1]
            else:
                assert heapdict._heap[i][1] <= heapdict._heap[(i - 1) // 2][1]

    def test_basic_usage(self):
        heapdict = MinHeapDict()
        self.check_invariants(heapdict)
        assert len(heapdict) == 0
        # Пустой HeapDict эквивалентен False. Мы следуем соглашению для коллекций.
        assert not heapdict

        heapdict['a'] = 5
        # Вставка ключа ничего не ломает.
        self.check_invariants(heapdict)
        assert len(heapdict) == 1
        # Не пустой HeapDict эквивалентен True.
        assert heapdict
        assert 'a' in heapdict
        assert 'a' in heapdict.keys()
        assert heapdict['a'] == 5
        assert 5 in heapdict.values()
        assert ('a', 5) in heapdict.items()
        assert heapdict.peekitem() == ('a', 5)

        heapdict['b'] = 1
        heapdict['c'] = 10
        self.check_invariants(heapdict)
        assert len(heapdict) == 3
        # Все ключи и приоритеты на месте.
        assert ('a', 5) in heapdict.items()
        assert ('b', 1) in heapdict.items()
        assert ('c', 10) in heapdict.items()
        # Пара с минимальным приоритетом лежит свеху, хотя её вставили не первой и не последней.
        assert heapdict.peekitem() == ('b', 1)

        heapdict['b'] = 20
        # Увеличение приоритета для ключа, который обладал минимальным приоритетом, ничего не
        # ломает.
        self.check_invariants(heapdict)
        assert len(heapdict) == 3
        # Все ключи и приоритеты на месте, кроме изменённого.
        assert ('a', 5) in heapdict.items()
        assert ('b', 20) in heapdict.items()
        assert ('c', 10) in heapdict.items()
        # Пара с минимальным приоритетом изменилась.
        assert heapdict.peekitem() == ('a', 5)

        heapdict['d'] = 3
        heapdict['e'] = 13
        heapdict.pop('c')
        # Удаление произвольного ключа ничего не ломает.
        self.check_invariants(heapdict)
        assert len(heapdict) == 4

        assert heapdict.popitem() == ('d', 3)
        # Удаление минимума ничего не ломает.
        self.check_invariants(heapdict)
        assert len(heapdict) == 3
        assert heapdict.peekitem() == ('a', 5)

    @pytest.mark.parametrize('cls', [MinHeapDict, MaxHeapDict])
    def test_errors(self, cls):
        heapdict = cls()
        with pytest.raises(KeyError):
            heapdict.popitem()
        with pytest.raises(KeyError):
            heapdict.peekitem()
        with pytest.raises(KeyError):
            heapdict['x']  # noqa
        with pytest.raises(KeyError):
            del heapdict['x']
        with pytest.raises(KeyError):
            heapdict.pop('x')
        # Попытка добавления нехэшируемого ключа завершается ошибкой, но ничего не ломает.
        with pytest.raises(TypeError):
            heapdict[[]] = 1
        assert len(heapdict) == 0
        self.check_invariants(heapdict)

    @pytest.mark.parametrize('cls', [MinHeapDict, MaxHeapDict])
    def test_create(self, cls):
        heapdict = cls.fromkeys(['a', 'b', 'c', 'b'], 0)
        self.check_invariants(heapdict)
        assert dict(heapdict) == {'a': 0, 'b': 0, 'c': 0}

        heapdict = cls([('a', 5), ('b', 1), ('c', 10), ('b', 20)])
        self.check_invariants(heapdict)
        assert dict(heapdict) == {'a': 5, 'b': 20, 'c': 10}

        heapdict = cls({'a': 5, 'b': 1, 'c': 10, 'b': 20})  # noqa
        self.check_invariants(heapdict)
        assert dict(heapdict) == {'a': 5, 'b': 20, 'c': 10}

        for another_cls in [MinHeapDict, MaxHeapDict]:
            another_heapdict = another_cls({'a': 5, 'b': 1, 'c': 10, 'b': 20})  # noqa
            heapdict = cls(another_heapdict)
            self.check_invariants(heapdict)
            assert dict(heapdict) == {'a': 5, 'b': 20, 'c': 10}

        heapdict = cls()
        self.check_invariants(heapdict)
        assert dict(heapdict) == {}

        with pytest.raises(TypeError):
            heapdict = cls(10)  # noqa

        heapdict = cls({'a': 5, 'b': 1, 'c': 10}, b=20, iterable=3)
        self.check_invariants(heapdict)
        assert dict(heapdict) == {'a': 5, 'b': 20, 'c': 10, 'iterable': 3}

    def test_pop_item_by_last_index_in_heap(self):
        # Удаление элемента кучи по последнему индексу требует осторожности в реализации.
        # Если обменять последний элемент с последним же, который сейчас удаляется, и попытаться
        # восстановить свойство кучи для этого элемента, возможна ошибка.
        heapdict = MinHeapDict({'a': 1, 'b': 2})
        assert heapdict.peekitem() == ('a', 1)
        heapdict.pop('b')
        self.check_invariants(heapdict)
        assert len(heapdict) == 1

        heapdict = MaxHeapDict({'a': 1, 'b': 2})
        assert heapdict.peekitem() == ('b', 2)
        heapdict.pop('b')
        self.check_invariants(heapdict)
        assert len(heapdict) == 1

    @pytest.mark.parametrize('cls', [MinHeapDict, MaxHeapDict])
    def test_preserves_insertion_order_on_change_priority_for_existing_key(self, cls):
        heapdict = cls({'a': 1, 'b': 5, 'c': 10})
        heapdict['b'] = 20
        assert list(heapdict.items()) == [('a', 1), ('b', 20), ('c', 10)]

    @pytest.mark.parametrize('cls', [MinHeapDict, MaxHeapDict])
    def test_preserves_insertion_order_on_update(self, cls):
        heapdict = cls({'a': 1, 'b': 5, 'c': 10})

        heapdict.update({'d': 13, 'b': 20, 'e': 10, 'c': 10})
        assert list(heapdict.items()) == [('a', 1), ('b', 20), ('c', 10), ('d', 13), ('e', 10)]

    @pytest.mark.parametrize('cls', [MinHeapDict, MaxHeapDict])
    def test_clear(self, cls):
        heapdict = cls([('a', 1), ('b', 2), ('c', 3), ('d', 2), ('c', 3)])

        heapdict.clear()
        self.check_invariants(heapdict)
        assert len(heapdict) == 0

        heapdict.clear()
        self.check_invariants(heapdict)
        assert len(heapdict) == 0

    @pytest.mark.parametrize('cls, copy_func', [
        (MinHeapDict, copy.copy),
        (MinHeapDict, lambda x: x.copy()),
        (MaxHeapDict, copy.copy),
        (MaxHeapDict, lambda x: x.copy())
    ])
    def test_copy(self, cls, copy_func):
        original = cls(zip('abcdef', [3, 3, 1, 6, 3, 4]))
        clone = copy_func(original)
        self.check_invariants(original)
        self.check_invariants(clone)
        assert original is not clone
        assert original == clone

        clone['x'] = 5
        assert 'x' in clone
        assert 'x' not in original

        clone.pop('d')
        assert 'd' not in clone
        assert 'd' in original

        clone['a'] = 100
        assert clone['a'] == 100
        assert original['a'] != 100
        self.check_invariants(original)
        self.check_invariants(clone)

    def test_repr(self):
        heapdict = MinHeapDict({'a': 1, 'b': 2, 'c': 3})
        assert repr(heapdict) == "MinHeapDict({'a': 1, 'b': 2, 'c': 3})"
        heapdict = MaxHeapDict({'a': 1, 'b': 2, 'c': 3})
        assert repr(heapdict) == "MaxHeapDict({'a': 1, 'b': 2, 'c': 3})"

    @pytest.mark.parametrize('cls', [MinHeapDict, MaxHeapDict])
    def test_or(self, cls):
        union = cls({'a': 1, 'b': 2}) | cls({'c': 3})
        assert isinstance(union, cls)
        assert union == {'a': 1, 'b': 2, 'c': 3}

        union = cls({'a': 1, 'b': 2}) | dict(c=3)
        assert isinstance(union, cls)
        assert union == {'a': 1, 'b': 2, 'c': 3}

        union = dict(a=1) | cls({'b': 2, 'c': 3})
        assert isinstance(union, cls)
        assert union == {'a': 1, 'b': 2, 'c': 3}

    @pytest.mark.parametrize('cls', [MinHeapDict, MaxHeapDict])
    def test_saves_last_duplicate(self, cls):
        # Наполняем объект парами с одинаковыми, но не идентичными ключами.
        pairs = [(tuple([1]), 3), (tuple([1]), 1), (tuple([1]), 2)]
        heapdict = cls(pairs)
        self.check_invariants(heapdict)
        # Сохранилась только последняя пара ключ-значение.
        assert len(heapdict) == 1
        assert heapdict[tuple([1])] == 2
        assert heapdict.peekitem()[0] is pairs[-1][0]

    @given(st.lists(st.integers()))
    @pytest.mark.parametrize('cls', [MinHeapDict, MaxHeapDict])
    def test_priorities_extracted_in_a_sort_order(self, cls, alist):
        heapdict = cls(enumerate(alist))
        priorities = []
        while heapdict:
            _, priority = heapdict.popitem()
            priorities.append(priority)
        assert priorities == sorted(alist, reverse=isinstance(heapdict, MaxHeapDict))
