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

    def test_basic_usage(self):

        heapdict = MinHeapDict()
        heapdict._check_invariants()
        assert len(heapdict) == 0
        # Пустой HeapDict эквивалентен False. Мы следуем соглашению для коллекций.
        assert not heapdict

        heapdict['a'] = 5
        # Вставка ключа ничего не ломает.
        heapdict._check_invariants()
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
        heapdict._check_invariants()
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
        heapdict._check_invariants()
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
        heapdict._check_invariants()
        assert len(heapdict) == 4

        assert heapdict.popitem() == ('d', 3)
        # Удаление минимума ничего не ломает.
        heapdict._check_invariants()
        assert len(heapdict) == 3
        assert heapdict.peekitem() == ('a', 5)

    def test_errors(self):
        for HeapDict in [MinHeapDict, MaxHeapDict]:
            heapdict = HeapDict()
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
            heapdict._check_invariants()

    def test_create(self):
        for HeapDict in [MinHeapDict, MaxHeapDict]:
            # create from keys
            heapdict = HeapDict.fromkeys(['a', 'b', 'c', 'b'], 0)
            heapdict._check_invariants()
            assert dict(heapdict) == {'a': 0, 'b': 0, 'c': 0}
            # create from pairs
            heapdict = HeapDict([('a', 5), ('b', 1), ('c', 10), ('b', 20)])
            heapdict._check_invariants()
            assert dict(heapdict) == {'a': 5, 'b': 20, 'c': 10}
            # create from another dict
            heapdict = HeapDict({'a': 5, 'b': 1, 'c': 10, 'b': 20})  # noqa
            heapdict._check_invariants()
            assert dict(heapdict) == {'a': 5, 'b': 20, 'c': 10}
            # create from another HeapDict
            for AnotherHeapDict in [MinHeapDict, MaxHeapDict]:
                another_heapdict = AnotherHeapDict({'a': 5, 'b': 1, 'c': 10, 'b': 20})  # noqa
                heapdict = HeapDict(another_heapdict)
                heapdict._check_invariants()
                assert dict(heapdict) == {'a': 5, 'b': 20, 'c': 10}
            # create empty HeapDict
            heapdict = HeapDict()
            heapdict._check_invariants()
            assert dict(heapdict) == {}
            # error if create from non-iterable
            with pytest.raises(TypeError):
                heapdict = HeapDict(10)  # noqa

    def test_pop_item_by_last_index_in_heap(self):
        # Удаление элемента кучи по последнему индексу требует осторожности в реализации.
        # Если обменять последний элемент с последним же, который сейчас удаляется, и попытаться
        # восстановить свойство кучи для этого элемента, возможна ошибка.
        heapdict = MinHeapDict({'a': 1, 'b': 2})
        assert heapdict.peekitem() == ('a', 1)
        heapdict.pop('b')
        heapdict._check_invariants()
        assert len(heapdict) == 1

        heapdict = MaxHeapDict({'a': 1, 'b': 2})
        assert heapdict.peekitem() == ('b', 2)
        heapdict.pop('b')
        heapdict._check_invariants()
        assert len(heapdict) == 1

    def test_preserves_insertion_order_on_change_priority_for_existing_key(self):
        for HeapDict in [MinHeapDict, MaxHeapDict]:
            heapdict = HeapDict({'a': 1, 'b': 5, 'c': 10})
            heapdict['b'] = 20
            # Изменение приоритета произвольного существующего ключа не изменяет порядок вставки.
            assert list(heapdict.items()) == [('a', 1), ('b', 20), ('c', 10)]

    def test_preserves_insertion_order_on_update(self):
        for HeapDict in [MinHeapDict, MaxHeapDict]:
            heapdict = HeapDict({'a': 1, 'b': 5, 'c': 10})
            heapdict.update({'d': 13, 'b': 20, 'e': 10, 'c': 10})
            # Изменение приоритета существующего ключа не изменяет порядок вставки при слиянии.
            expected = [('a', 1), ('b', 20), ('c', 10), ('d', 13), ('e', 10)]
            assert list(heapdict.items()) == expected

    def test_clear(self):
        for HeapDict in [MinHeapDict, MaxHeapDict]:
            heapdict = HeapDict([('a', 1), ('b', 2), ('c', 3), ('d', 2), ('c', 3)])
            heapdict.clear()
            # Очистка не ломает инварианты.
            heapdict._check_invariants()
            # Объект пуст после очистки.
            assert len(heapdict) == 0

    def test_copy(self):
        for copy_func in [copy.copy, lambda x: x.copy()]:
            for HeapDict in [MinHeapDict, MaxHeapDict]:
                original = HeapDict(zip('abcdef', [3, 3, 1, 6, 3, 4]))
                clone = copy_func(original)

                original._check_invariants()
                clone._check_invariants()
                clone['x'] = 5
                assert 'x' in clone
                assert 'x' not in original
                clone.pop('d')
                assert 'd' not in clone
                assert 'd' in original
                clone['a'] = 100
                assert clone['a'] == 100
                assert original['a'] != 100
                original._check_invariants()
                clone._check_invariants()

    def test_repr(self):
        heapdict = MinHeapDict({'a': 1, 'b': 2, 'c': 3})
        assert repr(heapdict) == "MinHeapDict({'a': 1, 'b': 2, 'c': 3})"
        heapdict = MaxHeapDict({'a': 1, 'b': 2, 'c': 3})
        assert repr(heapdict) == "MaxHeapDict({'a': 1, 'b': 2, 'c': 3})"

    def test_saves_last_duplicate(self):
        # Наполняем объект парами с одинаковыми, но не идентичными ключами.
        pairs = [(tuple([1]), 3), (tuple([1]), 1), (tuple([1]), 2)]
        for HeapDict in [MinHeapDict, MaxHeapDict]:
            heapdict = HeapDict(pairs)
            heapdict._check_invariants()
            # Сохранилась только последняя пара ключ-значение.
            assert len(heapdict) == 1
            assert heapdict[tuple([1])] == 2
            assert heapdict.peekitem()[0] is pairs[-1][0]

    @given(st.lists(st.integers()))
    def test_priorities_extracted_in_a_sort_order(self, alist):
        for HeapDict, expected in [(MinHeapDict, sorted(alist)),
                                   (MaxHeapDict, sorted(alist, reverse=True))]:
            heapdict = HeapDict(enumerate(alist))
            priorities = []
            while heapdict:
                _, priority = heapdict.popitem()
                priorities.append(priority)
            assert priorities == expected
