# heapdict
ru
Реализация очереди с приоритетами на Python. Позволяет добавлять элементы, указывая для каждого из 
них приоритет, чтобы быстро, за константное время, находить элемент с наименьшим (либо наибольшим) 
приоритетом. Добавление, извлечение элементов, а также изменение приоритета уже имеющихся в очереди
элементов осуществляется за логарифмическое время.

Библиотека предоставляет два класса — MinHeapDict и MaxHeapDict, оптимизированных, соответственно, 
для быстрого поиска минимального и максимального элементов. Оба класса реализуют интерфейс
словаря, ключами которого являются добавляемые в очередь элементы, а значениями — приоритеты
этих элементов. При этом, все добавляемые элементы должны быть уникальными и хэшируемыми, а
их приоритеты — сравнимыми между собой. Единственное отличие от словаря заключается в логике работы 
метода ``popitem`` — он извлекает пару из элемента и приоритета с наименьшим (либо наибольшим) 
приоритетом. Также, для удобства добавлен метод ``peekitem``, возвращающий соответствующую пару,
но не извлекающую её из коллекции.

eng
Implementing a Priority Queue in Python. Allows you to add elements by specifying for each of
them priority, in order to quickly, in constant time, find the element with the smallest (or largest)
priority. Adding, extracting elements and changing the priority of those already in the queue
elements is carried out in logarithmic time.

The library provides two classes - MinHeapDict and MaxHeapDict , optimized, respectively,
to quickly find the minimum and maximum elements. Both classes implement the interface
a dictionary whose keys are the elements added to the queue, and whose values ​​are the priorities
these elements. At the same time, all added elements must be unique and hashable, and
their priorities are comparable. The only difference from the dictionary is the logic of work
``popitem`` method - it extracts a pair from the element and the priority with the lowest (or highest)
priority. Also, for convenience, the ``peekitem`` method has been added, which returns the corresponding pair,
but not extracting it from the collection.

```python
from heapdict import MinHeapDict

heapdict = MinHeapDict({'x': 20, 'y': 5, 'z': 10})

print(heapdict) # MinHeapDict({'x': 20, 'y': 5, 'z': 10})
print(heapdict.peekitem()) # ('y', 5)
print(heapdict.popitem()) # ('y', 5)
print(heapdict) # MinHeapDict({'x': 20, 'z': 10})

print(heapdict.peekitem()) # ('z', 10)
heapdict['z'] = 50
print(heapdict.peekitem()) # ('x', 20)
```
