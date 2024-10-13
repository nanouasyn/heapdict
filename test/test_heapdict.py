import operator
from collections import OrderedDict
from contextlib import contextmanager

import hypothesis
import pytest
import copy
from hypothesis import given, strategies as st

from heapdict import HeapDict


def check_heapdict_invariants(heapdict: HeapDict):
    priorities = heapdict._priorities
    heap = heapdict._heap
    indexes = heapdict._indexes
    assert len(heapdict) == len(priorities) == len(heap) == len(indexes)
    assert list(heapdict) == list(priorities) == list(indexes)
    assert all(heap[i] == key for key, i in indexes.items())
    assert all(indexes[key] == i for i, key in enumerate(heap))

    for i in range(1, len(heap)):
        parent = heapdict._get_parent(i)
        if heapdict._get_level(i) % 2 == 0:
            assert priorities[heap[parent]] >= priorities[heap[i]]
        else:
            assert priorities[heap[parent]] <= priorities[heap[i]]

    for i in range(3, len(heap)):
        grandparent = heapdict._get_grandparent(i)
        if heapdict._get_level(i) % 2 == 0:
            assert priorities[heap[grandparent]] <= priorities[heap[i]]
        else:
            assert priorities[heap[grandparent]] >= priorities[heap[i]]


@contextmanager
def heapdict_not_changes(heapdict: HeapDict):
    heapdict_copy = heapdict.copy()
    try:
        yield heapdict
    except BaseException:
        raise
    assert heapdict._priorities == heapdict_copy._priorities
    assert heapdict._indexes == heapdict_copy._indexes
    assert heapdict._heap == heapdict_copy._heap


def assert_args_are_equivalent_by_function(func, a, b):
    a_result, a_error = None, None
    try:
        a_result = func(a)
    except Exception as e:
        a_error = e

    b_result, b_error = None, None
    try:
        b_result = func(b)
    except Exception as e:
        b_error = e

    assert a_result == b_result
    assert type(a_error) == type(b_error)


def assert_heapdict_is_empty(heapdict):
    assert not heapdict
    assert len(heapdict) == 0
    assert dict(heapdict) == {}

    with pytest.raises(ValueError):
        _ = heapdict.min_item()
    assert heapdict.min_item(default=42) == 42

    with pytest.raises(ValueError):
        _ = heapdict.pop_min_item()
    assert heapdict.pop_min_item(default=42) == 42

    with pytest.raises(ValueError):
        _ = heapdict.max_item()
    assert heapdict.max_item(default=42) == 42

    with pytest.raises(ValueError):
        _ = heapdict.pop_max_item()
    assert heapdict.pop_max_item(default=42) == 42

    with pytest.raises(ValueError):
        _ = heapdict.popitem()

    assert heapdict._priorities == {}
    assert heapdict._heap == []
    assert heapdict._indexes == {}


def test_create_empty():
    heapdict = HeapDict()

    assert_heapdict_is_empty(heapdict)


def test_create_from_incompatible():
    with pytest.raises(TypeError):
        _ = HeapDict(42)  # type: ignore

    with pytest.raises(TypeError):
        _ = HeapDict([1, 2, 3])


@given(keys=st.lists(st.integers()))
def test_create_fromkeys(keys):
    heapdict = HeapDict.fromkeys(keys, 0)
    check_heapdict_invariants(heapdict)

    expected = dict.fromkeys(keys, 0)
    assert heapdict == expected
    assert OrderedDict(heapdict) == OrderedDict(expected)


@given(pairs=st.lists(st.tuples(st.integers(), st.integers())))
def test_create_from_pairs(pairs):
    heapdict = HeapDict(iter(pairs))
    check_heapdict_invariants(heapdict)

    expected = dict(pairs)
    assert heapdict == expected
    assert OrderedDict(heapdict) == OrderedDict(expected)


@given(dictionary=st.dictionaries(st.integers(), st.integers()))
def test_create_from_dict(dictionary):
    heapdict = HeapDict(dictionary)
    check_heapdict_invariants(heapdict)

    assert heapdict == dictionary
    assert OrderedDict(heapdict) == OrderedDict(dictionary)


@given(
    pairs=st.lists(st.tuples(st.text(), st.integers())),
    kwargs=st.dictionaries(st.text(), st.integers()),
)
def test_create_from_pairs_and_kwargs(pairs, kwargs):
    heapdict = HeapDict(pairs, **kwargs)
    check_heapdict_invariants(heapdict)

    expected = dict([*pairs, *kwargs.items()])
    assert heapdict == expected
    assert OrderedDict(heapdict) == OrderedDict(expected)


def test_create_from_kwargs_bad_parameter_names():
    heapdict = HeapDict(iterable=1, kwargs=2)
    check_heapdict_invariants(heapdict)

    expected = {'iterable': 1, 'kwargs': 2}
    assert heapdict == expected
    assert OrderedDict(heapdict) == OrderedDict(expected)


@given(pairs=st.lists(st.tuples(st.integers(), st.integers())))
def test_create_from_heapdict(pairs):
    another_heapdict = HeapDict(pairs)
    check_heapdict_invariants(another_heapdict)

    heapdict = HeapDict(another_heapdict)
    check_heapdict_invariants(heapdict)

    assert OrderedDict(heapdict) == OrderedDict(another_heapdict)


@given(pairs=st.lists(st.tuples(st.integers(), st.integers())))
def test_create_from_insertions(pairs):
    created = HeapDict(pairs)

    filled = HeapDict()
    for key, value in pairs:
        filled[key] = value
    check_heapdict_invariants(filled)

    assert OrderedDict(created) == OrderedDict(filled)

    created_order = [created.pop_min_item()[1] for _ in range(len(created))]
    assert_heapdict_is_empty(created)

    filled_order = [filled.pop_min_item()[1] for _ in range(len(filled))]
    assert_heapdict_is_empty(filled)

    assert created_order == filled_order


@pytest.mark.parametrize("copy_func", [copy.copy, lambda x: x.copy()])
def test_copy(copy_func):
    original = HeapDict(zip("abcdef", [3, 3, 1, 6, 3, 4]))

    clone = copy_func(original)
    check_heapdict_invariants(original)

    assert original is not clone
    assert original == clone
    assert OrderedDict(original) == OrderedDict(clone)

    assert original._priorities == clone._priorities
    assert original._priorities is not clone._priorities
    assert original._indexes == clone._indexes
    assert original._indexes is not clone._indexes
    assert original._heap == clone._heap
    assert original._heap is not clone._heap

    clone["x"] = 5
    check_heapdict_invariants(original)
    check_heapdict_invariants(clone)

    assert "x" in clone
    assert "x" not in original

    clone.pop("d")
    check_heapdict_invariants(original)
    check_heapdict_invariants(clone)

    assert "d" not in clone
    assert "d" in original

    clone["a"] = 100
    check_heapdict_invariants(original)
    check_heapdict_invariants(clone)

    assert clone["a"] == 100
    assert original["a"] != 100


@given(pairs=st.lists(st.tuples(st.integers(), st.integers()), min_size=1))
def test_pop_min(pairs):
    heapdict = HeapDict(pairs)

    with heapdict_not_changes(heapdict):
        key, priority = item = heapdict.min_item()

        assert key in heapdict
        assert heapdict[key] == priority

    extracted_item = heapdict.pop_min_item()
    check_heapdict_invariants(heapdict)

    with heapdict_not_changes(heapdict):
        assert key not in heapdict
        with pytest.raises(KeyError):
            _ = heapdict[key]

    assert extracted_item == item


@given(pairs=st.lists(st.tuples(st.integers(), st.integers()), min_size=1))
def test_pop_max(pairs):
    heapdict = HeapDict(pairs)

    with heapdict_not_changes(heapdict):
        key, priority = item = heapdict.max_item()

        assert key in heapdict
        assert heapdict[key] == priority

    extracted_item = heapdict.pop_max_item()
    check_heapdict_invariants(heapdict)

    with heapdict_not_changes(heapdict):
        assert key not in heapdict
        with pytest.raises(KeyError):
            _ = heapdict[key]

    assert extracted_item == item


@given(
    pairs=st.lists(st.tuples(st.integers(), st.integers()), min_size=1),
    random=st.randoms(),
)
def test_pop(pairs, random):
    heapdict = HeapDict(pairs)

    key = random.choice(pairs)[0]
    hypothesis.note(f"{key = }")

    with heapdict_not_changes(heapdict):
        assert key in heapdict
        priority = heapdict[key]

    extracted_priority = heapdict.pop(key)
    check_heapdict_invariants(heapdict)

    with heapdict_not_changes(heapdict):
        assert key not in heapdict
        with pytest.raises(KeyError):
            _ = heapdict[key]

    assert extracted_priority == priority


@given(pairs=st.lists(st.tuples(st.integers(), st.integers()), min_size=1))
def test_pop_by_last_heap_index(pairs):
    heapdict = HeapDict(pairs)

    with heapdict_not_changes(heapdict):
        last_key = heapdict._heap[-1]
        hypothesis.note(f"{last_key = }")

        assert last_key in heapdict
        priority = heapdict[last_key]

    extracted_priority = heapdict.pop(last_key)
    check_heapdict_invariants(heapdict)

    with heapdict_not_changes(heapdict):
        assert last_key not in heapdict
        with pytest.raises(KeyError):
            _ = heapdict[last_key]

    assert priority == extracted_priority


@given(pairs=st.lists(st.tuples(st.integers(), st.integers())))
def test_reversed(pairs):
    heapdict = HeapDict(pairs)

    with heapdict_not_changes(heapdict):
        assert list(reversed(heapdict)) == list(heapdict)[::-1]


@given(pairs=st.lists(st.tuples(st.integers(), st.integers()), min_size=1))
def test_popitem(pairs):
    heapdict = HeapDict(pairs)

    with heapdict_not_changes(heapdict):
        key = next(reversed(heapdict))

        assert key in heapdict
        priority = heapdict[key]

    extracted_item = heapdict.popitem()
    check_heapdict_invariants(heapdict)

    with heapdict_not_changes(heapdict):
        assert key not in heapdict
        with pytest.raises(KeyError):
            _ = heapdict[key]

    assert extracted_item == (key, priority)


@given(alist=st.lists(st.integers()))
def test_sorting_by_pop_min(alist):
    heapdict = HeapDict(enumerate(alist))

    sorted_by_heapdict = []
    while heapdict:
        sorted_by_heapdict.append(heapdict.pop_min_item()[1])
        check_heapdict_invariants(heapdict)

    assert sorted_by_heapdict == sorted(alist)
    assert_heapdict_is_empty(heapdict)


@given(alist=st.lists(st.integers()))
def test_sorting_by_pop_max(alist):
    heapdict = HeapDict(enumerate(alist))

    sorted_by_heapdict = []
    while heapdict:
        sorted_by_heapdict.append(heapdict.pop_max_item()[1])
        check_heapdict_invariants(heapdict)

    assert sorted_by_heapdict == sorted(alist, reverse=True)
    assert_heapdict_is_empty(heapdict)


@given(alist=st.lists(st.integers()), random=st.randoms(use_true_random=True))
def test_sorting_by_random_extractions(alist, random):
    operations = random.choices(["pop_min", "pop_max"], k=len(alist))
    hypothesis.note(f"{operations = }")

    heapdict = HeapDict(enumerate(alist))

    minimums, maximums = [], []
    for operation in operations:
        if operation == "pop_min":
            minimums.append(heapdict.pop_min_item()[1])
        elif operation == "pop_max":
            maximums.append(heapdict.pop_max_item()[1])
        check_heapdict_invariants(heapdict)
    sorted_by_heapdict = minimums + maximums[::-1]

    assert sorted_by_heapdict == sorted(alist)
    assert_heapdict_is_empty(heapdict)


@given(st.randoms(use_true_random=True))
def test_compare_with_builtin_dict_behavior(random):
    keys = list("abcde")
    values = range(-5, 5)
    operation_types = {
        "set": lambda key, value: lambda d: operator.setitem(d, key, value),
        "pop": lambda key: lambda d: d.pop(key),
    }
    operations = []
    for _ in range(50):
        operation_type = random.choice(list(operation_types))
        if operation_type == "set":
            operation = ("set", random.choice(keys), random.choice(values))
            operations.append(operation)
        elif operation_type == "pop":
            operation = ("pop", random.choice(keys))
        else:
            assert False
        operations.append(operation)
    hypothesis.note(f"{operations = }")

    heapdict = HeapDict()
    builtin_dict = dict()

    for operation in operations:
        func = operation_types[operation[0]](*operation[1:])
        assert_args_are_equivalent_by_function(func, heapdict, builtin_dict)
        check_heapdict_invariants(heapdict)

    assert OrderedDict(heapdict) == OrderedDict(builtin_dict)


def test_missing_key():
    heapdict = HeapDict({'a': 5, 'b': 10, 'c': 12})

    with heapdict_not_changes(heapdict):
        with pytest.raises(KeyError):
            _ = heapdict['x']

    with heapdict_not_changes(heapdict):
        assert heapdict.get('x', default=42) == 42

    with heapdict_not_changes(heapdict):
        with pytest.raises(KeyError):
            del heapdict['x']

    with heapdict_not_changes(heapdict):
        with pytest.raises(KeyError):
            _ = heapdict.pop('x')

    with heapdict_not_changes(heapdict):
        assert heapdict.pop('x', 42) == 42


def test_unhashable_key():
    heapdict = HeapDict({'a': 5, 'b': 10, 'c': 12})

    with heapdict_not_changes(heapdict):
        with pytest.raises(TypeError):
            heapdict[[]] = 7


def test_pairs_order_does_not_matter_for_equality():
    heapdict1 = HeapDict({'a': 1, 'b': 2})
    heapdict2 = HeapDict({'b': 2, 'a': 1})

    assert heapdict1 == heapdict2
    assert dict(heapdict1) == dict(heapdict2)
    assert OrderedDict(heapdict1) != OrderedDict(heapdict2)


def test_equals_but_nonidentical_keys_behavior():
    # Insert pairs with equal but not identical keys.
    pairs = [(tuple([1]), 3), (tuple([1]), 1), (tuple([1]), 2)]
    heapdict = HeapDict(pairs)
    heapdict[tuple([1])] = 4
    heapdict[tuple([1])] = 2
    heapdict[tuple([1])] = 5
    check_heapdict_invariants(heapdict)

    # Only one pair is stored (first inserted key and last updated priority).
    assert OrderedDict(heapdict) == OrderedDict({tuple([1]): 5})
    assert heapdict.min_item()[0] is pairs[0][0]
    assert heapdict.min_item()[0] is not pairs[1][0]

    # Key is available to pop.
    heapdict.pop(tuple([1]))

    assert_heapdict_is_empty(heapdict)


def test_preserves_insertion_order_on_update():
    heapdict = HeapDict({"a": 1, "b": 5, "c": 10})
    heapdict["b"] = 20

    assert OrderedDict(heapdict) == OrderedDict({"a": 1, "b": 20, "c": 10})

    heapdict = HeapDict({"a": 1, "b": 5, "c": 10})
    del heapdict["b"]
    heapdict["b"] = 20

    assert OrderedDict(heapdict) == OrderedDict({"a": 1, "c": 10, "b": 20})


def test_clear():
    heapdict = HeapDict([("a", 1), ("b", 2), ("c", 3), ("d", 2), ("c", 3)])

    heapdict.clear()

    assert_heapdict_is_empty(heapdict)


def test_repr():
    heapdict = HeapDict()

    assert repr(heapdict) == "HeapDict()"

    heapdict = HeapDict({"a": 1, "b": 2, "c": 3})

    assert repr(heapdict) == "HeapDict({'a': 1, 'b': 2, 'c': 3})"


@pytest.mark.parametrize(
    "operand_types", [(HeapDict, HeapDict), (HeapDict, dict), (dict, HeapDict)]
)
@given(
    pairs1=st.lists(st.tuples(st.integers(), st.integers())),
    pairs2=st.lists(st.tuples(st.integers(), st.integers())),
)
def test_union(pairs1, pairs2, operand_types):
    operand1 = operand_types[0](pairs1)
    hypothesis.note(f"{operand1 = }")

    operand2 = operand_types[1](pairs2)
    hypothesis.note(f"{operand2 = }")

    union = operand1 | operand2

    assert isinstance(union, HeapDict)
    check_heapdict_invariants(union)

    expected = dict(pairs1) | dict(pairs2)
    assert union == expected
    assert OrderedDict(union) == OrderedDict(expected)


def test_union_with_incompatible():
    heapdict = HeapDict()

    with pytest.raises(TypeError):
        _ = heapdict | 42  # type: ignore

    with pytest.raises(TypeError):
        _ = 42 | heapdict  # type: ignore
