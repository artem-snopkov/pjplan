import re
from datetime import datetime
from typing import List, Optional, Union


def _to_list(val: Union['Task', List['Task']]):
    if type(val) is Task:
        return [val]
    elif type(val) is list or type(val) is tuple or type(val) is set:
        return val
    else:
        raise RuntimeError("Unsupported type", type(val))


class TaskList:

    def __init__(self, _list: List['Task'], setter=None):
        self.__list = _list
        self.__setter = setter

    def __iter__(self):
        return iter(self.__list)

    def append(self, task):
        if task not in self.__list:
            return self.__list.append(task)

    def remove(self, item):
        return self.__list.remove(item)

    def remove_all(self, key=None, **kwargs) -> 'UnmodifiableTaskList':
        tasks_to_delete = self(key, **kwargs)
        if not tasks_to_delete:
            return UnmodifiableTaskList([])

        for t in tasks_to_delete:
            t.parent = None
            t.predecessors = []
            t.successors = []

        return tasks_to_delete

    def copy(self):
        return self.__list.copy()

    def __setattr__(self, key, value):
        if key.find('__') > 0:
            super().__setattr__(key, value)
        else:
            for t in self:
                t.__setattr__(key, value)

    def __len__(self):
        return len(self.__list)

    def __add__(self, other):
        vals = [v for v in other if v not in self.__list]
        return self.__list.__add__(vals)

    def __call__(self, key=None, **kwargs) -> Union[Optional['Task'], 'UnmodifiableTaskList']:
        if key is not None:
            if type(key) is int:
                return next((t for t in self if t.id == key), None)
            if callable(key):
                return UnmodifiableTaskList([t for t in self if key(t)])
            raise RuntimeError("Unsupported arg type: " + type(key))

        if kwargs is None:
            raise RuntimeError("Key and Kwargs are None")

        def search(t, **kw):
            for k, v in kw.items():
                if k.endswith("_like_"):
                    k = k[0:-6]
                    if not re.search(v, t.__getattribute__(k)):
                        return False
                elif k.endswith("_not_in_"):
                    k = k[0:-8]
                    if t.__getattribute__(k) in v:
                        return False
                elif k.endswith("_in_"):
                    k = k[0:-4]
                    if not t.__getattribute__(k) in v:
                        return False
                elif t.__getattribute__(k) != v:
                    return False
            return True

        return UnmodifiableTaskList([t for t in self if search(t, **kwargs)])

    def sort(self, key, reverse=False) -> None:
        if self.__setter is None:
            raise RuntimeError("Unsupported operation")

        if type(key) is str:
            self.__list = sorted(self.__list, key=lambda x: x.__getattribute__(key), reverse=reverse)
        elif type(key) is list or type(key) is tuple or type(key) is set:
            self.__list = sorted(self.__list,
                                 key=lambda x: '-'.join([str(x.__getattribute__(k)) for k in key]),
                                 reverse=reverse)
        else:
            raise RuntimeError("Unsupported key type", type(key))

        self.__setter(self.__list)

    def reorder(self, ids):
        if self.__setter is None:
            raise RuntimeError("Unsupported operation")

        _all = self.__list.copy()

        new_list = []
        for _id in ids:
            ch = next(t for t in self if t.id == _id)
            new_list.append(ch)
            _all.remove(ch)

        self.__list = new_list + _all
        self.__setter(self.__list)

    def __lshift__(self, other: Union['Task', List['Task']]):
        for t in self:
            t.predecessors += _to_list(other)
        return other

    def __rshift__(self, other: Union['Task', List['Task']]):
        for t in self:
            t.successors += _to_list(other)
        return other

    def __getitem__(self, query):
        return self.__list.__getitem__(query)

    def __str__(self) -> str:
        return self.__list.__str__()

    def __repr__(self) -> str:
        return self.__list.__repr__()


class UnmodifiableTaskList(TaskList):
    def append(self, task):
        raise RuntimeError("Unsupported operation")

    def remove(self, item):
        raise RuntimeError("Unsupported operation")


class ChildrenList(TaskList):

    def __init__(self, parent: 'Task', _list, _setter):
        super().__init__(_list, _setter)
        self.__parent = parent

    def append(self, task: 'Task'):
        task.parent = self.__parent

    def remove(self, item: 'Task'):
        item.parent = None


class PredecessorsList(TaskList):
    def __init__(self, parent: 'Task', _list):
        super().__init__(_list)
        self.__parent = parent

    def append(self, task: 'Task'):
        self.__parent.predecessors = [v for v in self.__parent.predecessors] + [task]

    def remove(self, item: 'Task'):
        self.__parent.predecessors = [v for v in self.__parent.predecessors if v != item]


class SuccessorsList(TaskList):
    def __init__(self, parent: 'Task', _list):
        super().__init__(_list)
        self.__parent = parent

    def append(self, task: 'Task'):
        self.__parent.successors = [v for v in self.__parent.successors] + [task]

    def remove(self, item: 'Task'):
        self.__parent.successors = [v for v in self.__parent.successors if v != item]


class Task:
    """
    Task - задача, элемент WBS (Work Breakdown Structure), вершина графа задач.
    Задача связана с другими задачами одним из четырех отношений:
    1. parent (родительская задача). Может быть только один.
    2. children (дочерние задачи)
    3. predecessor (предшественники)
    4. successor (последователи)
    """

    def __init__(
            self,
            id: int,
            name: str = None,
            resource: str = None,
            start: datetime = None,
            end: datetime = None,
            milestone: bool = False,
            estimate: float = None,
            spent: float = None,
            parent: 'Task' = None,
            children: List['Task'] = None,
            predecessors: List['Task'] = None,
            successors: List['Task'] = None,
            **kwargs
    ):
        """
        Конструктор
        :param id: идентификатор задачи
        :param name: название задачи
        :param resource: ресурс, требуемый для выполнения задачи
        :param start: дата начала выполнения задачи
        :param end: дата окончания выполнения задачи
        :param milestone: флаг, определяющий, является ли задача контрольной точкой проекта
        :param estimate: оценка объема ресурса, требуемого для выполнения задачи
        :param spent: оценка потраченного к настоящему времени на задачу объема ресурса
        :param parent: родительская задача
        :param children: дочерние задачи
        :param predecessors: задачи предшественники
        :param successors: задачи-последователи
        :param kwargs: дополнительные атрибуты задачи
        """
        self.id = id
        self.name = name
        self.resource = resource
        self.start = start
        self.end = end
        self.milestone = milestone
        self.estimate = estimate
        self.spent = spent

        self.__parent = None
        self.parent = parent

        self.__children = []
        self.children = children

        self.__predecessors = []
        self.predecessors = predecessors

        self.__successors = []
        self.successors = successors

        for k, v in kwargs.items():
            self.__setattr__(k, v)

    @property
    def parent(self) -> 'Task':
        """Родительская задача"""
        return self.__parent

    @parent.setter
    def parent(self, value):
        if self.__parent and self in self.__parent.__children:
            self.__parent.__children.remove(self)

        self.__parent = value

        if value and self not in value.__children:
            value.__children.append(self)

    @property
    def parents(self) -> UnmodifiableTaskList:
        """Список родительских задач. Вычисляется рекурсивно вверх по дереву задач"""
        return UnmodifiableTaskList(self.__get_all_parents())

    def __get_all_parents(self) -> List['Task']:
        def get_parent(t):
            if t is not None:
                yield t
                yield from get_parent(t.parent)

        return [t for t in get_parent(self.__parent)]

    def __set_children(self, lst):
        self.__children = lst

    @property
    def children(self) -> ChildrenList:
        """Список дочерних задач"""
        return ChildrenList(self, self.__children, self.__set_children)

    @children.setter
    def children(self, value: List['Task']):
        if not value:
            value = []

        for v in self.__children:
            v.__parent = None

        self.__children.clear()

        new_children = [t for t in value]

        for v in new_children:
            v.parent = self

    @property
    def all_children(self) -> TaskList:
        """Список всех дочерних задач. Вычисляется рекурсивно вниз по дереву задач"""
        return UnmodifiableTaskList(self.__get_all_children())

    def __get_all_children(self):
        def get_children(t):
            for ch in t.__children:
                yield ch
                yield from get_children(ch)

        return [t for t in get_children(self)]

    @property
    def predecessors(self) -> TaskList:
        """Список прямых предшественников"""
        return PredecessorsList(self, self.__predecessors)

    @predecessors.setter
    def predecessors(self, value: List['Task']):
        if not value:
            value = []

        for v in self.__predecessors:
            v.__successors.remove(self)

        self.__predecessors = [v for v in value]

        for v in value:
            if self not in v.__successors:
                v.__successors.append(self)

    @property
    def all_predecessors(self) -> TaskList:
        """Список всех предшественников. Вычисляется рекурсивно по дереву предшественников"""
        return UnmodifiableTaskList(self.__get_all_predecessors())

    def __get_all_predecessors(self):
        def get_predecessor(t):
            for pr in t.predecessors:
                yield pr
                yield from get_predecessor(pr)

        return [t for t in get_predecessor(self)]

    @property
    def successors(self) -> TaskList:
        """Список прямых последователей"""
        return SuccessorsList(self, self.__successors)

    @successors.setter
    def successors(self, value: List['Task']):
        if not value:
            value = []

        for v in self.__successors:
            v.__predecessors.remove(self)

        self.__successors = [v for v in value]

        for v in value:
            if self not in v.__predecessors:
                v.__predecessors.append(self)

    @property
    def all_successors(self) -> TaskList:
        """Список всех последователей. Вычисляется рекурсивно по дереву всех последователей"""
        return UnmodifiableTaskList(self.__get_all_successors())

    def __get_all_successors(self):
        def get_successor(t):
            for pr in t.successors:
                yield pr
                yield from get_successor(pr)

        return [t for t in get_successor(self)]

    def __to_dict(self):
        d = {}
        for k in self.__dict__.keys():
            d[k] = self.__getattribute__(k)
        return d

    def clone(self, **kwargs) -> 'Task':
        cloned = Task(id=self.id, name=self.name)

        keys_to_gnore = {'_Task__parent', '_Task__children', '_Task__predecessors', '_Task__successors'}

        for k in self.__dict__.keys():
            if k not in keys_to_gnore:
                cloned.__setattr__(k, self.__getattribute__(k))

        for k, v in kwargs.items():
            cloned.__setattr__(k, v)

        return cloned

    def __floordiv__(self, other: Union['Task', List['Task']]):
        """
        Синоним children.append(other) и childred += other
        :param other: задача или список задач
        :return: other
        """
        self.children += _to_list(other)
        return other

    def __lshift__(self, other: Union['Task', List['Task']]):
        """
        Синоним predecessors.append(other) или predecessors += other
        :param other: задача или список задач
        :return: other
        """
        self.predecessors += _to_list(other)
        return other

    def __rshift__(self, other: Union['Task', List['Task']]):
        """
        Синоним successors.append(other) или successors += other
        :param other: задача или список задач
        :return: other
        """
        self.successors += _to_list(other)
        return other

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __str__(self):
        return str(self.__to_dict())

    def __repr__(self):
        return self.__str__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class WBS:

    def __init__(self, name=None, tasks: List[Task] = None, **kwargs):
        self.__root = Task(0, name, children=tasks)
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    @property
    def name(self):
        return self.__root.name

    @name.setter
    def name(self, value):
        self.__root.name = value

    @property
    def roots(self):
        return self.__root.children

    @roots.setter
    def roots(self, value):
        self.__root.children = value

    @property
    def start(self):
        starts = [t.start for t in self.__root.children if t.start is not None]
        if len(starts):
            return min(starts)
        return None

    @property
    def end(self):
        ends = [t.end for t in self.__root.children if t.end is not None]
        if len(ends):
            return max(ends)
        return None

    def remove_all(self, key = None, **kwargs):
        return self.__root.all_children.remove_all(key, **kwargs)

    def __len__(self):
        return len(self.__root.all_children)

    def __getitem__(self, item):
        return self.__root.all_children[item]

    def __iter__(self):
        return iter(self.__root.all_children)

    def __call__(self, key=None, **kwargs):
        return self.__root.all_children(key, **kwargs)

    def __floordiv__(self, other: Union['Task', List['Task']]):
        return self.__root // other

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def clone(self) -> 'WBS':
        """
        Клонирует WBS - список дочерних задач и всех связанных с ними задач
        :return: клон WBS
        """
        all_tasks = {task.id: task for task in self.__root.all_children + [self.__root]}

        cloned_tasks = {task.id: task.clone() for task in all_tasks.values()}

        # У задач в списке all_tasks могут быть predecessors или successors вне графа задач
        # (например, из другого проекта). При клонировании эти задачи клонироваться не должны.
        # Добавляем их в cloned_tasks как есть.
        for t in all_tasks.values():
            for pr in t.predecessors:
                cloned_tasks.setdefault(pr.id, pr)
            for sc in t.successors:
                cloned_tasks.setdefault(sc.id, sc)

        for t in all_tasks.values():
            c = cloned_tasks[t.id]
            c.parent = cloned_tasks[all_tasks[t.id].parent.id] if all_tasks[t.id].parent else None
            c.children = [cloned_tasks[ch.id] for ch in all_tasks[t.id].children]
            c.predecessors = [cloned_tasks[ch.id] for ch in all_tasks[t.id].predecessors]
            c.successors = [cloned_tasks[ch.id] for ch in all_tasks[t.id].successors]

        cloned_project = WBS(self.__root.name)
        cloned_project.__root = cloned_tasks[self.__root.id]
        keys_to_gnore = {'_WBS__roots', '_WBS__root'}
        for k in self.__dict__.keys():
            if k not in keys_to_gnore:
                cloned_project.__setattr__(k, self.__getattribute__(k))

        return cloned_project
