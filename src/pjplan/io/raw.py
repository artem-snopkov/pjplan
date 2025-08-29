from datetime import datetime
from typing import List, Iterable, Any

from pjplan import Task, WBS


class TaskRaw:
    def __init__(
            self,
            id: Any,
            name: str,
            resource: str = None,
            start: datetime = None,
            end: datetime = None,
            milestone: bool = False,
            estimate: float = None,
            spent: float = None,
            parent_id: int = None,
            predecessor_ids: List[int] = None,
            **kwargs
    ):
        self.id = id
        self.name = name
        self.resource = resource
        self.start = start
        self.end = end
        self.milestone = milestone
        self.estimate = estimate
        self.spent = spent
        self.parent_id = parent_id
        self.predecessor_ids = predecessor_ids
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def to_dict(self) -> dict:
        res = {}
        for k in self.__dict__.keys():
            res[k] = self.__getattribute__(k)
        return res


def tasks_to_raws(tasks: Iterable[Task]) -> List[TaskRaw]:
    raws = []
    for t in tasks:
        raw = TaskRaw(
            id=t.id,
            name=t.name,
            resource=t.resource,
            start=t.start,
            end=t.end,
            estimate=t.estimate,
            spent=t.spent,
            milestone=t.milestone,
            parent_id=t.parent.id if t.parent and t.parent.id != 0 else None,
            predecessor_ids=[p.id for p in t.predecessors]
        )
        for k in t.__dict__.keys():
            if not k.startswith('_') and k not in raw.__dict__:
                raw.__setattr__(k, t.__getattribute__(k))

        raws.append(raw)

    return raws


def raws_to_wbs(raws: List[TaskRaw]) -> WBS:
    tasks_by_id = {}
    for raw in raws:
        t = Task(
            id=raw.id,
            name=raw.name,
            resource=raw.resource,
            start=raw.start,
            end=raw.end,
            estimate=raw.estimate,
            spent=raw.spent,
            milestone=raw.milestone
        )

        for k in raw.__dict__.keys():
            if k not in dir(t):
                t.__setattr__(k, raw.__getattribute__(k))

        tasks_by_id[t.id] = t

    roots = []
    for raw in raws:
        task = tasks_by_id[raw.id]

        if raw.parent_id is not None:
            parent_task = tasks_by_id.get(raw.parent_id)
            if parent_task is not None:
                parent_task.children.append(task)
                task.parent = parent_task
            else:
                roots.append(task)
        else:
            roots.append(task)

    wbs = WBS()
    for r in roots:
        wbs.roots.append(r)

    for raw in raws:
        task = wbs[raw.id]

        for predecessor_id in raw.predecessor_ids:
            predecessor_task = wbs[predecessor_id]
            if predecessor_task is not None:
                task.predecessors.append(predecessor_task)

    return wbs
