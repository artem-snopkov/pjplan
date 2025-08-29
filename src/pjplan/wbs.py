from datetime import datetime
from typing import Optional, Union, Iterable, Callable, Any, Dict

from pjplan.alg.critical_path import CriticalPathCalculator
from pjplan.task import Task, EMPTY_TASK_ID, _ChildrenList, _ImmutableTaskList, _to_list, _Repr


class WBS:
    """Work Burn-down Structure"""

    # noinspection PyProtectedMember
    def __init__(self, tasks: Iterable[Task] = None, **kwargs):
        """
        Constructor
        :param tasks: list of tasks. New WBS will contain clones of this tasks
        :param kwargs: any additional WBS arguments
        """
        self.__root = Task(EMPTY_TASK_ID, **kwargs)
        self.__root._attach(self)

        if tasks:
            self.__root.children = [v.clone() for v in tasks]

    def _root(self):
        return self.__root

    @property
    def roots(self) -> _ChildrenList:
        """List of all root tasks in WBS"""
        return self.__root.children

    @roots.setter
    def roots(self, value):
        self.__root.children = value

    @property
    def tasks(self) -> _ImmutableTaskList:
        """List of all tasks in WBS"""
        return self.__root.all_children

    @property
    def start(self) -> Optional[datetime]:
        """Returns min start date from all tasks in WBS"""
        starts = [t.start for t in self.roots if t.start is not None]
        if len(starts):
            return min(starts)
        return None

    @property
    def end(self) -> Optional[datetime]:
        """Returns max end date from all tasks in WBS"""
        ends = [t.end for t in self.__root.children if t.end is not None]
        if len(ends):
            return max(ends)
        return None

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

    def remove_all(self, key: Optional[Callable[['Task'], bool]] = None, **kwargs):
        """
        Remove all tasks matched to key from WBS.
        :param key: see TaskList.remove_all for details
        :param kwargs: see TaskList.remove_all for details
        :return: list of deleted tasks
        """
        tasks_to_delete = self.tasks(key, **kwargs)

        if not tasks_to_delete:
            return _ImmutableTaskList([])

        for t in tasks_to_delete:
            self.__remove(t, self.__root)

        return tasks_to_delete

    def __getitem__(self, task_id: Any):
        try:
            return next((t for t in self.__root.all_children if t.id == task_id))
        except StopIteration:
            raise RuntimeError(f"Task with id={task_id} not found")

    def __floordiv__(self, other: Union['Task', Iterable['Task']]):
        return self.__root // other

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __clone_tasks(self, roots: Iterable[Task]) -> Dict[int, Task]:
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

        return cloned_tasks

    def __clone(self, roots: Iterable[Task]) -> 'WBS':

        cloned_tasks = self.__clone_tasks(roots)

        cloned_project = WBS()
        cloned_project.roots = [cloned_tasks[r.id] for r in roots]

        for k in self.__dict__.keys():
            if not k.startswith('_'):
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

    def critical_path(self) -> _ImmutableTaskList:
        """
        Calculate critical path based on tasks dependencies, estimates and spent times.
        Resources are not taken into account
        :return: list of tasks from WBS at critical path
        """
        return CriticalPathCalculator(self.tasks, None).calc()

    def __repr__(self) -> str:
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
