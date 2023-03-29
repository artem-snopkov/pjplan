import re
from datetime import datetime
from typing import List, Optional, Union, Iterable, Callable


def _to_list(val: Union['Task', List['Task']]) -> List['Task']:
    if type(val) is Task:
        return [val]
    elif type(val) is list or type(val) is tuple or type(val) is set:
        return val
    else:
        raise RuntimeError("Unsupported type", type(val))


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
        _current_max = max(_current_max, len('   ' * level) + len(task.name))
        for ch in task.children:
            _current_max = _Repr.__calc_max_title_len(ch, level + 1, _current_max)
        return _current_max

    @staticmethod
    def __get_field_value(t: 'Task', field: str) -> str:
        if field == 'predecessors':
            return '[' + ','.join([str(p.id) for p in t.predecessors]) + ']'
        if field == 'successors':
            return '[' + ','.join([str(p.id) for p in t.successors]) + ']'
        if field == 'parent':
            return str(t.parent.id) if t.parent else ''

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
    def __print_task_subtree(task: 'Task', fields: List[str], level, fmt, children, theme):
        values = []
        for f in fields:
            if f == 'name':
                values.append('   ' * level + task.name)
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
    def repr(tasks: Iterable['Task'], fields: List[str] = None, children=True, theme: dict = None):
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
        self.__list = _list

    def index(self, task: 'Task') -> int:
        """
        Returns index of task in list
        :param task: task
        :return: index in list
        :raises RuntimeError if task does not exists in list
        """
        return self.__list.index(task)

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
            return ImmutableTaskList([t for t in self.__list])

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
        return iter(self.__list)

    def __setattr__(self, key, value):
        """
        Set attribute to all tasks in list
        :param key: attribute name
        :param value: attribute value
        :return:
        """
        if key.find('__') > 0:
            super().__setattr__(key, value)
        else:
            for t in self:
                t.__setattr__(key, value)

    def __len__(self) -> int:
        """
        Returns len of list
        :return: len of list
        """
        return len(self.__list)

    def __add__(self, other):
        """
        Concatenate this list with other
        :param other: other task list
        :return:
        """
        vals = [v for v in other if v not in self.__list]
        return self.__list.__add__(vals)

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
        return _Repr.repr(self)

    def print(self, fields: List[str] = None, children=True, theme: dict = None) -> None:
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


class TaskList(ImmutableTaskList):
    """Mutable task list implementation"""

    def __init__(self, _list: List['Task'], setter=None):
        super().__init__(_list)
        self.__list = _list
        self.__setter = setter

    def append(self, task: 'Task') -> bool:
        """
        Append task to the end of list if task not already in list
        :param task: task
        :return: True, if task added to list. False, if task already exists in list
        """
        if task not in self.__list:
            self.__list.append(task)
            return True
        return False

    def remove(self, task: 'Task') -> bool:
        """
        Remove task from list
        :param task: task
        :return: True, if task removed. False, if task does not exists in list
        """
        if task in self.__list:
            self.__list.remove(task)
            return True
        return False

    def insert(self, index: int, task: 'Task') -> bool:
        """
        Insert task before index
        :param index: index
        :param task: task
        :return: True, if task added to list. False, if task already exists in list
        """
        if task not in self.__list:
            self.__list.insert(index, task)
            return True
        return False

    def move(self, task: 'Task', before: Optional['Task'] = None, after: Optional['Task'] = None) -> None:
        """
        Move task before or after another task
        :param task: task to move
        :param before: task
        :param after: task
        :raises RuntimeError if task/before/after does not exists in list
        """
        if task not in self.__list:
            raise RuntimeError("'Task' not found in list")
        if before is not None and before not in self.__list:
            raise RuntimeError("'Before' not found in list")
        if after is not None and after not in self.__list:
            raise RuntimeError("After not found in list")
        if before is not None and after is not None:
            raise RuntimeError("'Before' and 'After' is not None. Only one parameter must be set")

        self.__list.remove(task)
        if before is not None:
            self.__list.insert(self.__list.index(before), task)
        elif after is not None:
            self.__list.insert(self.__list.index(after) + 1, task)
        else:
            raise RuntimeError("'Before' or 'After' must be not None")

    def remove_all(self, key: Union[int, Callable[['Task'], bool]] = None, **kwargs) -> 'TaskList':
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
            t.parent = None
            t.predecessors = []
            t.successors = []

        return tasks_to_delete

    def sort(self, key: Union[str, List[str]], reverse=False) -> None:
        """
        Sort tasks in list ascending by specified attribute
        :param key: attribute name or list of attribute names
        :param reverse: reverse sort
        """
        if self.__setter is None:
            raise RuntimeError("Unsupported operation")

        if type(key) is str:
            self.__list = sorted(self.__list, key=lambda x: x.__getattribute__(key), reverse=reverse)
        elif type(key) is list or type(key) is tuple or type(key) is set:
            self.__list = sorted(self.__list,
                                 key=lambda x: '-'.join([str(x.__getattribute__(k)) for k in key]),
                                 reverse=reverse)
        else:
            raise RuntimeError(f"Unsupported key type {type(key)}")

        self.__setter(self.__list)

    def reorder(self, ids: List[int]) -> None:
        """
        Put tasks with specified ids on top of list in order
        :param ids: list of task ids
        """
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


class ChildrenList(TaskList):

    def __init__(self, parent: 'Task', _list, _setter):
        super().__init__(_list, _setter)
        self.__parent = parent

    def append(self, task: 'Task'):
        task.parent = self.__parent

    def remove(self, task: 'Task'):
        task.parent = None

    def insert(self, index: int, task: 'Task'):
        super().insert(index, task)
        task.parent = self.__parent


class PredecessorsList(TaskList):
    def __init__(self, parent: 'Task', _list):
        super().__init__(_list)
        self.__parent = parent

    def append(self, task: 'Task'):
        self.__parent.predecessors = [v for v in self.__parent.predecessors] + [task]

    def remove(self, task: 'Task'):
        self.__parent.predecessors = [v for v in self.__parent.predecessors if v != task]

    def insert(self, index: int, task: 'Task'):
        raise RuntimeError("Unsupported operation")


class SuccessorsList(TaskList):
    def __init__(self, parent: 'Task', _list):
        super().__init__(_list)
        self.__parent = parent

    def append(self, task: 'Task'):
        self.__parent.successors = [v for v in self.__parent.successors] + [task]

    def remove(self, task: 'Task'):
        self.__parent.successors = [v for v in self.__parent.successors if v != task]

    def insert(self, index: int, task: 'Task'):
        raise RuntimeError("Unsupported operation")


class Task:
    """
    Task is a base Work Burndown Structure (WBS) element. A node in tasks graph.
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
        :param parent: parent task
        :param children: children tasks
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
        """Parent task"""
        return self.__parent

    @parent.setter
    def parent(self, value):
        if self.__parent and self in self.__parent.__children:
            self.__parent.__children.remove(self)

        self.__parent = value

        if value and self not in value.__children:
            value.__children.append(self)

    @property
    def parents(self) -> ImmutableTaskList:
        """List of all parent tasks in hierarchy"""
        return ImmutableTaskList(self.__get_all_parents())

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
        """List of direct children tasks"""
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
        """Creates copy of this task"""
        cloned = Task(id=self.id, name=self.name)

        keys_to_gnore = {'_Task__parent', '_Task__children', '_Task__predecessors', '_Task__successors'}

        for k in self.__dict__.keys():
            if k not in keys_to_gnore:
                cloned.__setattr__(k, self.__getattribute__(k))

        for k, v in kwargs.items():
            cloned.__setattr__(k, v)

        return cloned

    def __floordiv__(self, other: Union['Task', List['Task']]):
        """Synonym for children.append(other) and childred += other"""
        self.children += _to_list(other)
        return other

    def __lshift__(self, other: Union['Task', List['Task']]):
        """Synonym for predecessors.append(other) and predecessors += other"""
        self.predecessors += _to_list(other)
        return other

    def __rshift__(self, other: Union['Task', List['Task']]):
        """Synonym for successors.append(other) или successors += other"""
        self.successors += _to_list(other)
        return other

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __str__(self):
        return str(self.__to_dict())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __repr__(self):
        return _Repr.repr([self])

    def print(self, fields: List[str] = None, children=True, theme=None):
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
    """Work Burndown Structure, Project"""

    def __init__(self, name=None, tasks: List[Task] = None, **kwargs):
        """
        Constructor
        :param name: name of project
        :param tasks: list of tasks
        :param kwargs: any additional WBS arguments
        """
        self.__root = Task(0, name, children=tasks, **kwargs)

    @property
    def name(self):
        """Name of WBS"""
        return self.__root.name

    @name.setter
    def name(self, value):
        self.__root.name = value

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

    def append(self, task: Task) -> bool:
        """Append task to root of WBS"""
        return self.__root.children.append(task)

    def __remove(self, task_to_remove: Task, current: Task):
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

    def __floordiv__(self, other: Union['Task', List['Task']]):
        return self.__root // other

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def clone(self) -> 'WBS':
        """Returns copy of this WBS."""
        all_tasks = {task.id: task for task in self.__root.all_children + [self.__root]}

        cloned_tasks = {task.id: task.clone() for task in all_tasks.values()}

        # Some tasks in WBS can have predecessors or successors outside WBS (i.e. from another project).
        # This predecessors/successors should not be copied.
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

    def __repr__(self):
        return _Repr.repr(self.roots)

    def print(self, fields: List[str] = None, children=True, theme=None):
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
