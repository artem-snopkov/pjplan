from datetime import datetime
from typing import List, Dict, Any, Iterable, Optional

from pjplan.task import Task, _ImmutableTaskList


def _find_clusters(tasks: List['Task']) -> List[List['Task']]:
    task_ids = set((t.id for t in tasks))
    visited = set()
    clusters = []

    for t in tasks:
        if t.id in visited:
            continue

        all_deps = t.all_successors(id_in_=task_ids) + t.all_predecessors(id_in_=task_ids) + [t]
        for d in all_deps:
            visited.add(d.id)

        clusters.append(all_deps)

    return clusters


class _PNode:
    def __init__(self):
        self.forward_links: List['_PLink'] = []
        self.backward_links: List['_PLink'] = []

        self.start_units = None
        self.end_units = None


class _PLink:
    def __init__(self, units: float, start: _PNode, end: _PNode):
        self.start = start
        self.end = end
        self.units = units


class CriticalPathCalculator:

    def __init__(self, tasks: Iterable[Task], end_date: Optional[datetime]):
        self.__nodes: List[_PNode] = []
        self.__links: Dict[Any, _PLink] = {}
        self.__tasks: Dict[Any, Task] = {}
        self.__end_date = end_date

        for t in tasks:
            if end_date is not None:
                if t.end == end_date:
                    self.__insert_task(t)
            else:
                self.__insert_task(t)

    def __insert_task(self, task: Task):
        if len(task.children) > 0:
            return

        if task.id in self.__tasks:
            return

        self.__tasks[task.id] = task

        p_ids = []
        for p in task.predecessors:
            p_ids.append(p.id)
            self.__insert_task(p)

        estimate = task.estimate if task.estimate is not None else 0
        spent = task.spent if task.spent is not None else 0

        self.__add_work(task.id, max(estimate - spent, 0), p_ids)

    def __new_node(self) -> _PNode:
        res = _PNode()
        self.__nodes.append(res)
        return res

    @staticmethod
    def __connect(start: _PNode, end: _PNode, units: float):
        link = _PLink(units, start, end)
        start.forward_links.append(link)
        end.backward_links.append(link)
        return link

    def __add_work(self, id: Any, units: float, predecessors: List[Any]):
        start = self.__new_node()
        end = self.__new_node()
        link = self.__connect(start, end, units)

        self.__links[id] = link

        for p in predecessors:
            link = self.__links[p]
            self.__connect(link.end, start, 0)

    def __forward(self, node: _PNode):
        if node.start_units is None:
            max_start = 0
            for link in node.backward_links:
                if link.start.start_units is None:
                    self.__forward(link.start)
                max_start = max(max_start, link.start.start_units + link.units)

            node.start_units = max_start

    def __backward(self, node: _PNode):

        if node.end_units is None:
            min_end = None
            for link in node.forward_links:
                if link.end.end_units is None:
                    self.__backward(link.end)
                if min_end is None:
                    min_end = link.end.end_units - link.units
                else:
                    min_end = min(min_end, link.end.end_units - link.units)

            if min_end is None:
                min_end = node.start_units

            node.end_units = min_end

    def calc(self) -> _ImmutableTaskList:

        start_nodes = [n for n in self.__nodes if len(n.backward_links) == 0]
        end_nodes = [n for n in self.__nodes if len(n.forward_links) == 0]

        begin = _PNode()
        begin.start_units = 0
        for n in start_nodes:
            self.__connect(begin, n, 0)

        end = _PNode()
        for n in end_nodes:
            self.__connect(n, end, 0)

        for n in self.__nodes + [end]:
            self.__forward(n)

        for n in self.__nodes:
            self.__backward(n)

        res = []
        for k, v in self.__links.items():
            # print(k, f"{v.start.start_units} - {v.start.end_units}", f"{v.end.start_units} - {v.end.end_units}")
            r = v.end.end_units - v.start.start_units - v.units
            if r == 0:
                res.append(self.__tasks[k])

        if self.__end_date is None:
            return _ImmutableTaskList(res)
        else:
            critical_tasks_clusters = _find_clusters(res)

            res = []
            for cluster in critical_tasks_clusters:
                for t in cluster:
                    if t.end == self.__end_date:
                        res += cluster
                        break

            res = sorted(res, key=lambda x: x.start)
            return _ImmutableTaskList(res)

