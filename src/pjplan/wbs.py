import re
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Union, Iterable, Callable, Any

_ROOT_ID = sys.maxsize


def _to_list(val: Union['Task', Iterable['Task']]) -> List['Task']:
    if val is None:
        return []
    elif type(val) is Task:
        return [val]
    elif type(val) is list or type(val) is tuple or type(val) is set:
        return [t for t in val]
    elif isinstance(val, Iterable):
        return [t for t in val]
    else:
        raise RuntimeError("Unsupported type", type(val))


def _find_root(task: 'Task'):
    if task.parent is not None:
        return _find_root(task.parent)
    return task


def _collect_subtree(task: 'Task') -> List['Task']:
    res = [task]
    for ch in task.children:
        res += _collect_subtree(ch)
    return res


def _has_id_intersection(parent: 'Task', children: Iterable['Task']):
    parent_root = _find_root(parent)
    parent_tree = _collect_subtree(parent_root)
    all_children_tasks = []
    for ch in children:
        all_children_tasks += _collect_subtree(ch)

    parent_tree_object_ids = set([id(t) for t in parent_tree])
    new_tasks = [t for t in all_children_tasks if id(t) not in parent_tree_object_ids]

    if len(new_tasks) == 0:
        return False

    parent_tree_ids = set([t.id for t in parent_tree])
    new_task_ids = set([t.id for t in new_tasks])
    return len(parent_tree_ids.intersection(new_task_ids)) > 0


def _check_not_none(obj: Any, name: str):
    if obj is None:
        raise RuntimeError(f"{name} is None")


def _check_no_nones_in_list(lst: List, name: str):
    for v in lst:
        if v is None:
            raise RuntimeError(f"{name} contains None value")


class _Repr:
    """Utility class for print task sheets"""

    __red = '91m'
    __green = '92m'
    __yellow = '93m'
    __blue = '94m'
    __pink = '95m'
    __teal = '96m'
    __grey = '97m'

    __DEFAULT_THEME = {
        'header_color': __green,
        'level_colors': [__blue, __teal, __yellow, __pink, __red, __grey]
    }

    @staticmethod
    def __calc_max_title_len(task: 'Task', level, _current_max):
        name_len = len(task.name) if task.name is not None else 0
        _current_max = max(_current_max, len('   ' * level) + name_len)
        for ch in task.children:
            _current_max = _Repr.__calc_max_title_len(ch, level + 1, _current_max)
        return _current_max

    @staticmethod
    def __get_linked_task_id(task: 'Task', linked_task: 'Task'):
        if linked_task is None or linked_task.id == _ROOT_ID:
            return ''
        external = linked_task.wbs != task.wbs
        return f"{linked_task.id}{'(external)' if external else ''}"

    @staticmethod
    def __get_linked_tasks_id(task: 'Task', linked_tasks: Iterable['Task']):
        res = []
        for t in linked_tasks:
            res.append(_Repr.__get_linked_task_id(task, t))
        return ','.join(res)

    @staticmethod
    def __get_field_value(t: 'Task', field: str) -> str:
        if field == 'predecessors':
            return '[' + _Repr.__get_linked_tasks_id(t, t.predecessors) + ']'
        if field == 'successors':
            return '[' + _Repr.__get_linked_tasks_id(t, t.successors) + ']'
        if field == 'parent':
            return _Repr.__get_linked_task_id(t, t.parent)

        if field not in t.__dict__:
            field = field.lower()
            if field not in t.__dict__:
                return ''

        v = t.__getattribute__(field)
        if isinstance(v, datetime):
            return v.strftime('%d.%m.%Y %H:%M')

        if v is None:
            return '-'

        return str(v)

    @staticmethod
    def __max_field_len(tasks: Iterable['Task'], field: str) -> int:
        max_len = len(field) + 1
        for t in tasks:
            max_len = max(max_len, len(_Repr.__get_field_value(t, field)))
            max_len = max(max_len, _Repr.__max_field_len(t.children, field))

        return max_len

    @staticmethod
    def __colored(text, color):
        return '\033[' + color + text + '\033[0m'

    @staticmethod
    def __print_task_subtree(task: 'Task', fields: Iterable[str], level, fmt, children, theme):
        values = []
        for f in fields:
            if f == 'name':
                values.append('   ' * level + (task.name if task.name is not None else ''))
            else:
                values.append(_Repr.__get_field_value(task, f))

        if 'print_color' in task.__dict__:
            color = task.print_color
        else:
            colors = theme['level_colors']
            color = colors[level] if level < len(colors) else _Repr.__grey

        res = _Repr.__colored(fmt.format(*values), color) + '\n'
        if children:
            for ch in task.children:
                res += _Repr.__print_task_subtree(ch, fields, level + 1, fmt, children, theme)

        return res

    @staticmethod
    def repr(tasks: Iterable['Task'], fields: Iterable[str] = None, children=True, theme: dict = None):
        if fields is None:
            fields = ['id', 'name', 'resource', 'estimate', 'spent', 'start', 'end', 'predecessors']

        if theme is None:
            theme = _Repr.__DEFAULT_THEME

        max_title_len = 0
        for _t in tasks:
            max_title_len = max(max_title_len, _Repr.__calc_max_title_len(_t, 0, 0))

        fmt = ""
        for f in fields:
            if len(fmt) > 0:
                fmt += "  "
            if f.lower() == 'name':
                fmt += f"{{:{max_title_len}}}"
            else:
                fmt += f"{{:{_Repr.__max_field_len(tasks, f)}}}"

        title = [s.upper() for s in fields]

        color = theme['header_color'] if 'header_color' in theme else _Repr.__grey

        res = _Repr.__colored(fmt.format(*title), color) + '\n'

        for _task in tasks:
            res += _Repr.__print_task_subtree(_task, fields, 0, fmt, children, theme)

        return res


class ImmutableTaskList:
    """Immutable task list implementation"""

    def __init__(self, _list: List['Task']):
        self._list = _list

    def index(self, task: 'Task') -> int:
        """
        Returns index of task in list
        :param task: task
        :return: index in list
        :raises RuntimeError if task does not exists in list
        """
        _check_not_none(task, "Task")
        return self._list.index(task)

    @staticmethod
    def __get_task_attribute(t: 'Task', attribute_name: str):
        if attribute_name == 'parent_id':
            return t.parent.id if t.parent else None
        return t.__getattribute__(attribute_name) if attribute_name in t.__dict__ else None

    def __call__(
            self,
            key: Union[int, Callable[['Task'], bool]] = None,
            **kwargs
    ) -> Union[Optional['Task'], 'ImmutableTaskList']:
        """
        Search tasks in list
        :param key: task id or Callable[[Task], bool] that implements filter
        :param kwargs: task filters
        :return: list of matched tasks
        """
        if key is not None:
            if type(key) is int:
                return next((t for t in self if t.id == key), None)
            if callable(key):
                return ImmutableTaskList([t for t in self if key(t)])
            raise RuntimeError(f"Unsupported key type: {type(key)}")

        if kwargs is None:
            return ImmutableTaskList([t for t in self._list])

        def search(t, **kw):
            for k, v in kw.items():
                if k.endswith("_like_"):
                    k = k[0:-6]
                    if not re.search(v, self.__get_task_attribute(t, k)):
                        return False
                elif k.endswith("_not_in_"):
                    k = k[0:-8]
                    if self.__get_task_attribute(t, k) in v:
                        return False
                elif k.endswith("_in_"):
                    k = k[0:-4]
                    if not self.__get_task_attribute(t, k) in v:
                        return False
                elif k.endswith("_ne_"):
                    k = k[0:-4]
                    if not self.__get_task_attribute(t, k) != v:
                        return False
                elif k.endswith("_le_"):
                    k = k[0:-4]
                    if not self.__get_task_attribute(t, k) <= v:
                        return False
                elif k.endswith("_lt_"):
                    k = k[0:-4]
                    if not self.__get_task_attribute(t, k) < v:
                        return False
                elif k.endswith("_ge_"):
                    k = k[0:-4]
                    if not self.__get_task_attribute(t, k) >= v:
                        return False
                elif k.endswith("_gt_"):
                    k = k[0:-4]
                    if not self.__get_task_attribute(t, k) > v:
                        return False
                elif self.__get_task_attribute(t, k) != v:
                    return False
            return True

        return ImmutableTaskList([t for t in self if search(t, **kwargs)])

    def __iter__(self):
        return iter(self._list)

    def __setattr__(self, key, value):
        """
        Set attribute to all tasks in list
        :param key: attribute name
        :param value: attribute value
        :return:
        """
        if key.startswith('__') > 0 or key.startswith('_'):
            super().__setattr__(key, value)
        else:
            tasks = [t for t in self._list]
            for t in tasks:
                t.__setattr__(key, value)

    def __len__(self) -> int:
        """
        Returns len of list
        :return: len of list
        """
        return len(self._list)

    def __add__(self, other):
        """
        Concatenate this list with other
        :param other: other task list
        :return:
        """
        return self._list.__add__(_to_list(other))

    def __lshift__(self, other: Union['Task', Iterable['Task']]):
        for t in self:
            t.predecessors += other
        return other

    def __rshift__(self, other: Union['Task', Iterable['Task']]):
        for t in self:
            t.successors += other
        return other

    def __getitem__(self, query):
        return self._list.__getitem__(query)

    def __str__(self) -> str:
        return self._list.__str__()

    def __repr__(self) -> str:
        return _Repr.repr(self)

    def print(self, fields: Iterable[str] = None, children=True, theme: dict = None) -> None:
        """
        Print task sheet
        :param fields: fields to print
        :param children: show/hide child tasks
        :param theme: color theme

        Color theme specified by dict:
        {
            'header_color': '<header color>',
            'level_colors': ['<level 0 color>', '<level 1 color>', ...]
        }
        """
        return print(_Repr.repr(self, fields, children, theme))


class TaskList(ImmutableTaskList, ABC):
    """Mutable task list implementation"""

    def __init__(self, _list: List['Task']):
        super().__init__(_list)

    @abstractmethod
    def remove(self, task: 'Task'):
        pass

    def remove_all(self, key: Union[int, Callable[['Task'], bool]] = None, **kwargs) -> 'ImmutableTaskList':
        """
        Remove all tasks matched to key from list
        :param key: see __call__ for details
        :param kwargs: see __call__ for details
        :return: deleted tasks
        """
        tasks_to_delete = self(key, **kwargs)
        if not tasks_to_delete:
            return ImmutableTaskList([])

        for t in tasks_to_delete:
            self.remove(t)

        return tasks_to_delete


class ChildrenList(TaskList):

    def __init__(self, parent: 'Task', _list, _setter):
        super().__init__(_list)
        self.__parent = parent
        self.__setter = _setter

    def append(self, task: 'Task'):
        """
        Appends task to the end of children list. If task already exists in WBS, it will be moved to new parent
        :param task: task
        :return:
        :raises RuntimeError: if WBS integrity lost (i.e. task with same ID already exists)
        """
        _check_not_none(task, 'Task')
        task.parent = self.__parent

    def remove(self, task: 'Task') -> bool:
        """
        Removes task from children list and from WBS
        :param task: task to remove
        :return: True, if task exists. Otherwise False
        """
        _check_not_none(task, 'Task')
        if task not in self._list:
            return False
        self.__parent.children = [t for t in self._list if t != task]
        return True

    def insert(self, index: int, task: 'Task'):
        """
        Insert task in children list before index. If task already exists in WBS it will be moved to new parent
        :param index: index
        :param task: task
        :raises RuntimeError: if WBS integrity lost (i.e. task with same ID already exists)
        """
        _check_not_none(task, 'Task')
        task.parent = self.__parent
        if len(self) > 0:
            self.move(task, before=self[index])

    def move(self, task: 'Task', before: Optional['Task'] = None, after: Optional['Task'] = None) -> None:
        """
        Move task before or after another task
        :param task: task to move
        :param before: task
        :param after: task
        :raises RuntimeError: if task/before/after does not exists in list
        """
        if task not in self._list:
            raise RuntimeError("'Task' not found in list")
        if before is not None and before not in self._list:
            raise RuntimeError("'Before' not found in list")
        if after is not None and after not in self._list:
            raise RuntimeError("After not found in list")
        if before is not None and after is not None:
            raise RuntimeError("'Before' and 'After' is not None. Only one parameter must be set")

        self._list.remove(task)
        if before is not None:
            self._list.insert(self._list.index(before), task)
        elif after is not None:
            self._list.insert(self._list.index(after) + 1, task)
        else:
            raise RuntimeError("'Before' or 'After' must be not None")

        self.__setter(self._list)

    def sort(self, key: Union[str, List[str]], reverse=False) -> None:
        """
        Sort tasks in list ascending by specified attribute
        :param key: attribute name or list of attribute names
        :param reverse: reverse sort
        """
        if self.__setter is None:
            raise RuntimeError("Unsupported operation")

        if type(key) is str:
            self._list = sorted(self._list, key=lambda x: x.__getattribute__(key), reverse=reverse)
        elif type(key) is list or type(key) is tuple or type(key) is set:
            self._list = sorted(self._list,
                                 key=lambda x: '-'.join([str(x.__getattribute__(k)) for k in key]),
                                 reverse=reverse)
        else:
            raise RuntimeError(f"Unsupported key type {type(key)}")

        self.__setter(self._list)

    def reorder(self, ids: List[int]) -> None:
        """
        Put tasks with specified ids on top of list in order
        :param ids: list of task ids
        """
        if self.__setter is None:
            raise RuntimeError("Unsupported operation")

        _all = self._list.copy()

        new_list = []
        for _id in ids:
            ch = next(t for t in self if t.id == _id)
            new_list.append(ch)
            _all.remove(ch)

        self._list = new_list + _all
        self.__setter(self._list)


class PredecessorsList(TaskList):
    """List of predecessor tasks"""

    def __init__(self, parent: 'Task', _list):
        super().__init__(_list)
        self.__parent = parent

    def append(self, task: 'Task'):
        """
        Appends task to predecessors list
        :param task: task to add
        :raises RuntimeError: if WBS integrity lost (i.e. root is predecessor of child)
        """
        _check_not_none(task, 'Task')
        self.__parent.predecessors = [v for v in self.__parent.predecessors] + [task]

    def remove(self, task: 'Task') -> bool:
        """
        Removes task from predecessors
        :param task: task to remove
        :return: True, if task exists in predecessors.
        """
        _check_not_none(task, 'Task')
        if task not in self._list:
            return False
        self.__parent.predecessors = [v for v in self.__parent.predecessors if v != task]
        return True


class SuccessorsList(TaskList):
    """List of successors tasks"""

    def __init__(self, parent: 'Task', _list):
        super().__init__(_list)
        self.__parent = parent

    def append(self, task: 'Task'):
        """
        Appends task to successors
        :param task: task to add
        :raises RuntimeError: if WBS integrity lost (i.e. root is successor of child)
        """
        _check_not_none(task, 'Task')
        self.__parent.successors = [v for v in self.__parent.successors] + [task]

    def remove(self, task: 'Task') -> bool:
        """
        Removes task from successors
        :param task: task to remove
        :return: True, if task exists in successors
        """
        _check_not_none(task, 'Task')
        if task not in self._list:
            return False
        self.__parent.successors = [v for v in self.__parent.successors if v != task]
        return True


class Task:
    """
    Task is a base Work Burn-down Structure (WBS) element. A node in tasks graph.
    Tasks are connected in several ways:
    1. parent
    2. children
    3. predecessor
    4. successor
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
        :param id: task id, unique in task graph
        :param name: task name
        :param resource: resource name (person, machine, etc.), necessary to perform task
        :param start: task start date
        :param end: task end date
        :param milestone: is task milestone or not
        :param estimate: task estimation in hours
        :param spent: task completed work in hours
        :param predecessors: predecessor tasks
        :param successors: successor tasks
        :param kwargs: additional task attributes
        """
        self.id = id
        self.name = name
        self.resource = resource
        self.start = start
        self.end = end
        self.milestone = milestone
        self.estimate = estimate
        self.spent = spent

        self.__wbs: Optional['WBS'] = None

        self.__parent = None
        self.__children = []
        self.__predecessors = []
        self.__successors = []

        if parent is not None:
            self.parent = parent
        if children is not None:
            self.children = children
        if successors:
            self.successors = successors
        if predecessors:
            self.predecessors = predecessors

        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def _attach(self, wbs: 'WBS'):
        if wbs is None:
            return
        self.__wbs = wbs
        for ch in self.children:
            ch._attach(wbs)

    @property
    def parent(self) -> Optional['Task']:
        """Parent task"""
        if self.__parent is None or self.__parent.id == _ROOT_ID:
            return None
        return self.__parent

    @property
    def wbs(self):
        """WBS that task attached to or None, if task detached"""
        return self.__wbs

    # noinspection PyProtectedMember
    @parent.setter
    def parent(self, parent: Optional['Task']):
        """
        Setter for parent task
        :param parent: new parent
        """

        if self.__wbs is None:
            # Check parent changed
            if parent is not None and (self.parent is None or id(self.parent) != id(parent)):
                # Check no ID duplicates
                if _has_id_intersection(parent, [self]):
                    raise RuntimeError("Task subtree ids intersects with parent tree ids")
        else:
            if parent is not None and parent.__wbs != self.__wbs:
                raise RuntimeError("Parent must be from same WBS")

        if parent is not None:
            if parent in self.all_children:
                raise RuntimeError(f"Task {parent.id} is a child of task {self.id}. Can't make child "
                                   f"a parent of its parent")

        if self.__parent is not None and self in self.__parent.__children:
            self.__parent.__children.remove(self)

        if parent is None:
            if self.__wbs is not None:
                self.__wbs._root().children.append(self)
            else:
                self.__parent = None
                self.predecessors = []
                self.successors = []
                for ch in self.__children:
                    ch.parent = None

        else:
            self.__parent = parent
            self._attach(parent.__wbs)
            if parent and self not in parent.__children:
                parent.__children.append(self)

    @property
    def all_parents(self) -> ImmutableTaskList:
        """List of all parent tasks in hierarchy"""
        return ImmutableTaskList(self.__get_all_parents())

    def __get_all_parents(self) -> List['Task']:
        def get_parent(t):
            if t is not None and t.id != _ROOT_ID:
                yield t
                yield from get_parent(t.parent)

        return [t for t in get_parent(self.__parent)]

    def __set_children(self, lst):
        self.__children = lst

    @property
    def children(self) -> ChildrenList:
        """List of direct children tasks"""
        return ChildrenList(self, self.__children, self.__set_children)

    @children.setter
    def children(self, value: Union['Task', Iterable['Task']]):
        """Setter for children tasks"""
        value = _to_list(value)
        _check_no_nones_in_list(value, 'children')

        if self.__wbs is None:
            # If self.__wbs is None, all children wbs must be None
            if len([v for v in value if v.__wbs is not None]) > 0:
                raise RuntimeError('Children tasks must be from same WBS as parent task')

            # Check no ids intersection
            if _has_id_intersection(self, value):
                raise RuntimeError("Task tree ids intersects with children ids")

        else:
            # Is self.__wbs is not None, children wbs must be none or equals to self.__wbs
            if len([v for v in value if v.__wbs is not None and v.__wbs != self.__wbs]) > 0:
                raise RuntimeError('Children tasks must be from same WBS as parent task')

            if _has_id_intersection(self, value):
                raise RuntimeError(f"Id intersection detected")

        for ch in value:
            if self in ch.all_children:
                raise RuntimeError(f"Task {self.id} is a child of {ch.id}. Can't make child a parent of its parent")

        for v in self.__children:
            v.__parent = None

        self.__children.clear()

        for v in value:
            v.parent = self

    @property
    def all_children(self) -> ImmutableTaskList:
        """List of all children tasks: direct children, children of direct children etc."""
        return ImmutableTaskList(self.__get_all_children())

    def __get_all_children(self):
        def get_children(t):
            for ch in t.__children:
                yield ch
                yield from get_children(ch)

        return [t for t in get_children(self)]

    @property
    def predecessors(self) -> PredecessorsList:
        """List of direct predecessors"""
        return PredecessorsList(self, self.__predecessors)

    @predecessors.setter
    def predecessors(self, value: Union['Task', Iterable['Task']]):
        """
        Setter for predecessor tasks
        :param value: new predecessors
        """
        value = _to_list(value)
        _check_no_nones_in_list(value, 'predecessors')

        parents = self.all_parents
        for v in value:
            if v in parents:
                raise RuntimeError("Can't set parent as predecessor")

        for v in value:
            if self in v.all_predecessors:
                raise RuntimeError(f"{self.id} exists in {v.id} predecessors. Cyclic dependency")

        for v in self.__predecessors:
            if self in v.__successors:
                v.__successors.remove(self)

        self.__predecessors = [v for v in value]

        for v in value:
            if self not in v.__successors:
                v.__successors.append(self)

    @property
    def all_predecessors(self) -> ImmutableTaskList:
        """List of all predecessors: direct predecessors, predecessors of direct predecessors etc."""
        return ImmutableTaskList(self.__get_all_predecessors())

    def __get_all_predecessors(self):
        def get_predecessor(t):
            for pr in t.predecessors:
                yield pr
                yield from get_predecessor(pr)

        return [t for t in get_predecessor(self)]

    @property
    def successors(self) -> SuccessorsList:
        """List of direct successors"""
        return SuccessorsList(self, self.__successors)

    @successors.setter
    def successors(self, value: Union['Task', Iterable['Task']]):
        """
        Setter for direct successors
        :param value: new direct successors
        """
        value = _to_list(value)
        _check_no_nones_in_list(value, 'successors')

        parents = self.all_parents
        for v in value:
            if v in parents:
                raise RuntimeError("Can't set parent as successor")

        for v in value:
            if self in v.all_successors:
                raise RuntimeError(f"{self.id} exists in {v.id} successors. Cyclic dependency")

        for v in self.__successors:
            if self in v.__predecessors:
                v.__predecessors.remove(self)

        self.__successors = [v for v in value]

        for v in value:
            if self not in v.__predecessors:
                v.__predecessors.append(self)

    @property
    def all_successors(self) -> ImmutableTaskList:
        """List of all successors: direct successors, successors of direct successors, etc."""
        return ImmutableTaskList(self.__get_all_successors())

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
        """Creates copy of this task without parent/children/successors/predecessors"""
        cloned = Task(id=self.id, name=self.name)

        keys_to_gnore = {'_Task__parent', '_Task__children', '_Task__predecessors', '_Task__successors', '_Task__wbs'}

        for k in self.__dict__.keys():
            if k not in keys_to_gnore:
                cloned.__setattr__(k, self.__getattribute__(k))

        for k, v in kwargs.items():
            cloned.__setattr__(k, v)

        return cloned

    def __floordiv__(self, other: Union['Task', Iterable['Task']]):
        """Synonym for children.append(other) and childred += other"""
        self.children += other
        return other

    def __lshift__(self, other: Union['Task', Iterable['Task']]):
        """Synonym for predecessors.append(other) and predecessors += other"""
        self.predecessors += other
        return other

    def __rshift__(self, other: Union['Task', Iterable['Task']]):
        """Synonym for successors.append(other) или successors += other"""
        self.successors += other
        return other

    def __str__(self):
        return str(self.__to_dict())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __repr__(self):
        return _Repr.repr([self])

    def print(self, fields: Iterable[str] = None, children=True, theme=None):
        """
        Print task
        :param fields: fields to print
        :param children: show/hide child tasks
        :param theme: color theme

        Color theme specified by dict:
        {
          'header_color': '<header color>',
          'level_colors': ['<level 0 color>', '<level 1 color>', ...]
        }
        """
        return print(_Repr.repr([self], fields, children, theme))


class WBS:
    """Work Burn-down Structure"""

    # noinspection PyProtectedMember
    def __init__(self, tasks: Iterable[Task] = None, **kwargs):
        """
        Constructor
        :param tasks: list of tasks. New WBS will contain clones of this tasks
        :param kwargs: any additional WBS arguments
        """
        self.__root = Task(_ROOT_ID, **kwargs)
        self.__root._attach(self)

        if tasks:
            self.__root.children = [v.clone() for v in tasks]

    def _root(self):
        return self.__root

    @property
    def roots(self):
        """List of all root tasks in WBS"""
        return self.__root.children

    @roots.setter
    def roots(self, value):
        self.__root.children = value

    @property
    def start(self):
        """Returns min start date from all tasks in WBS"""
        starts = [t.start for t in self.roots if t.start is not None]
        if len(starts):
            return min(starts)
        return None

    @property
    def end(self):
        """Returns max end date from all tasks in WBS"""
        ends = [t.end for t in self.__root.children if t.end is not None]
        if len(ends):
            return max(ends)
        return None

    def append(self, task: Task):
        """Append task to root of WBS"""
        self.__root.children.append(task)

    def insert(self, index: int, task: Task) -> bool:
        return self.__root.children.insert(index, task);

    def __remove(self, task_to_remove: Task, current: Task):
        if task_to_remove is None:
            return False

        if current.children.remove(task_to_remove):
            return True

        for ch in current.children:
            if self.__remove(task_to_remove, ch):
                return True

        return False

    def remove(self, task: Task) -> bool:
        """
        Remove task from WBS
        :param task:
        """
        if not isinstance(task, Task):
            raise RuntimeError(f'{type(task)} is not Task')

        return self.__remove(task, self.__root)

    def remove_all(self, key: Union[int, Callable[['Task'], bool]] = None, **kwargs):
        """
        Remove all tasks matched to key from WBS.
        :param key: see TaskList.remove_all for details
        :param kwargs: see TaskList.remove_all for details
        :return: list of deleted tasks
        """
        tasks_to_delete = self(key, **kwargs)

        if not tasks_to_delete:
            return ImmutableTaskList([])

        for t in tasks_to_delete:
            self.__remove(t, self.__root)

        return tasks_to_delete

    def __len__(self):
        return len(self.__root.all_children)

    def __getitem__(self, item):
        return self.__root.all_children[item]

    def __iter__(self):
        return iter(self.__root.all_children)

    def __call__(self, key=None, **kwargs):
        return self.__root.all_children(key, **kwargs)

    def __floordiv__(self, other: Union['Task', Iterable['Task']]):
        return self.__root // other

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __clone(self, roots: Iterable[Task]) -> 'WBS':
        all_tasks_list = []
        for r in roots:
            all_tasks_list.append(r)
            all_tasks_list += [t for t in r.all_children]

        all_tasks = {task.id: task for task in all_tasks_list}

        cloned_tasks = {task.id: task.clone() for task in all_tasks.values()}

        # Some tasks in WBS can have predecessors or successors outside WBS (i.e. from another project).
        # This predecessors/successors should not be copied.
        for t in all_tasks.values():
            for pr in t.predecessors:
                if pr.wbs != self:
                    cloned_tasks.setdefault(pr.id, pr)
            for sc in t.successors:
                if sc.wbs != self:
                    cloned_tasks.setdefault(sc.id, sc)

        for t in all_tasks.values():
            c = cloned_tasks[t.id]
            c.parent = cloned_tasks.get(all_tasks[t.id].parent.id) if all_tasks[t.id].parent else None
            c.children = [cloned_tasks[ch.id] for ch in all_tasks[t.id].children]
            c.predecessors = [cloned_tasks[ch.id] for ch in all_tasks[t.id].predecessors if ch.id in cloned_tasks]
            c.successors = [cloned_tasks[ch.id] for ch in all_tasks[t.id].successors if ch.id in cloned_tasks]

        cloned_project = WBS()
        cloned_project.roots = [cloned_tasks[r.id] for r in roots]
        keys_to_gnore = {'_WBS__roots', '_WBS__root'}
        for k in self.__dict__.keys():
            if k not in keys_to_gnore:
                cloned_project.__setattr__(k, self.__getattribute__(k))

        return cloned_project

    def clone(self) -> 'WBS':
        """Returns copy of this WBS."""
        return self.__clone(self.roots)

    def subtree(self, roots: Union[Task, Iterable[Task]]) -> 'WBS':
        """
        Returns new WBS, contains subtree of this WBS with all children
        and successors/predecessors inside this subtree or outside WBS.

        :param roots: root tasks for new WBS
        :return: new WBS
        """
        return self.__clone(_to_list(roots))

    def __repr__(self):
        return _Repr.repr(self.roots)

    def print(self, fields: Iterable[str] = None, children=True, theme=None):
        """
        Print task sheet
        :param fields: fields to print
        :param children: show/hide child tasks
        :param theme: color theme

        Color theme specified by dict:
        {
          'header_color': '<header color>',
          'level_colors': ['<level 0 color>', '<level 1 color>', ...]
        }
        """
        return print(_Repr.repr(self.roots, fields, children, theme))
