import pytest
import copy
from hypothesis import (
    given,
    strategies as st
)

from heapdict import HeapDict


class TestHeapDict:

    def test_basic_usage(self):

        heapdict = HeapDict()
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

    def test_pop_item_by_last_index_in_heap(self):
        """ Удаление элемента в конце кучи работает корректно. """
        # Удаление элемента кучи по последнему индексу требует осторожности в реализации.
        # Если обменять последний элемент с последним же, который сейчас удаляется, и попытаться
        # восстановить свойство кучи для этого элемента, возможна ошибка.
        heapdict = HeapDict({'a': 1, 'b': 2})
        assert heapdict.peekitem() == ('a', 1)
        heapdict.pop('b')
        heapdict._check_invariants()
        assert len(heapdict) == 1

    def test_preserves_insertion_order_on_change_priority_for_existing_key(self):
        """ Порядок вставки сохраняется при изменении приоритета существующего ключа. """
        heapdict = HeapDict({'a': 1, 'b': 5, 'c': 10})
        heapdict['b'] = 20

        # Изменение приоритета произвольного существующего ключа не изменяет порядок вставки.
        # Мы сохраняем те же гарантии, что и словарь. Это же отражено и в строковом представлении.
        assert list(heapdict.items()) == [('a', 1), ('b', 20), ('c', 10)]
        assert repr(heapdict) == "HeapDict({'a': 1, 'b': 20, 'c': 10})"

    def test_preserves_insertion_order_on_update(self):
        """ Порядок вставки сохраняется при слиянии. """
        heapdict = HeapDict({'a': 1, 'b': 5, 'c': 10})
        heapdict.update({'d': 13, 'b': 20, 'e': 10, 'c': 10})

        # Изменение приоритета существующего ключа не изменяет порядок вставки при слиянии.
        assert list(heapdict.items()) == [('a', 1), ('b', 20), ('c', 10), ('d', 13), ('e', 10)]
        assert repr(heapdict) == "HeapDict({'a': 1, 'b': 20, 'c': 10, 'd': 13, 'e': 10})"

    def test_clear(self):
        """ Очистка HeapDict работает корректно. """
        heapdict = HeapDict([('a', 1), ('b', 2), ('c', 3), ('d', 2), ('c', 3)])
        heapdict.clear()
        # Очистка не ломает инварианты.
        heapdict._check_invariants()
        # Объект пуст после очистки.
        assert len(heapdict) == 0

    def test_copy(self):
        """ HeapDict реализует копирование как через метод copy, так и через функцию copy.copy. """
        for copy_func in [copy.copy, lambda x: x.copy()]:
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

    def test_saves_last_duplicate(self):
        """ При добавлении дублирующихся ключей, должен сохраняться только последний. """
        # Наполняем объект парами с одинаковыми, но не идентичными ключами.
        pairs = [(tuple([1]), 3), (tuple([1]), 1), (tuple([1]), 2)]
        heapdict = HeapDict(pairs)
        # Дубликаты не ломают инварианты.
        heapdict._check_invariants()
        # Сохранилась только последняя пара ключ-значение.
        assert len(heapdict) == 1
        assert heapdict[tuple([1])] == 2
        assert heapdict.peekitem()[0] is pairs[-1][0]

    @given(st.lists(st.integers()))
    def test_priorities_extracted_in_a_sort_order(self, alist):
        """ Извлечение элементов из HeapDict происходит в порядке сортировки. """
        heapdict = HeapDict(enumerate(alist))
        priorities = []
        while heapdict:
            _, priority = heapdict.popitem()
            priorities.append(priority)
        assert priorities == sorted(alist)
