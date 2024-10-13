# heapdict

Реализация очереди с приоритетами на Python, позволяющая за логарифмическое время добавлять в
очередь элементы с указанными приоритетами, извлекать элементы с наименьшим и наибольшим приоритетом,
а также изменять приоритеты существующих элементов. Для этого библиотека предоставляет класс HeapDict,
который реализует интерфейс словаря, ключами которого считаются добавляемые в очередь элементы, а
значениями — приоритеты этих элементов. Все добавляемые элементы (ключи) должны быть уникальными и
хэшируемыми, а их приоритеты (значения) — сравнимыми между собой. HeapDict построена на основе
[min-max кучи](https://en.wikipedia.org/wiki/Min-max_heap).

Вот, например, реализация алгоритма Дейкстры для поиска длины кратчайшего пути в графе, обладающая,
благодаря использованию HeapDict, асимптотикой O((V + E) * log(V)):

```python
import math

from heapdict import HeapDict

def dijkstra(graph, start):
    queue = HeapDict({start: 0})
    distances = {}
    while queue:
        vertex, distance = queue.pop_min_item()
        distances[vertex] = distance
        for neighbour, edge_length in graph[vertex].items():
            if neighbour in distances:
                continue
            distance_to_neighbour = distance + edge_length
            if distance_to_neighbour < queue.get(neighbour, math.inf):
                queue[neighbour] = distance_to_neighbour
    return distances
```

```pycon
>>> graph = {
...     "A": {"B": 5, "C": 0},
...     "B": {"D": 15, "E": 20},
...     "C": {"D": 30, "E": 35},
...     "D": {"F": 20},
...     "E": {"F": 10},
...     "F": {},
... }
>>> dijkstra(graph, "A")
{'A': 0, 'C': 0, 'B': 5, 'D': 20, 'E': 25, 'F': 35}
```