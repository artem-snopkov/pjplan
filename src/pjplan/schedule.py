import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Set, Callable

from pjplan import Task, WBS, IResource, Resource
from pjplan.utils import TextTable, GREEN, YELLOW, GREY, RED


def _validate_graph_isolation(project: WBS):
    all_tasks = {task.id: task for task in project.tasks}

    for t in all_tasks.values():
        for pr in t.predecessors:
            if pr.id not in all_tasks and (not pr.start or not pr.end):
                raise RuntimeError(
                    "Task {t.id} ({t.name}) has predecessor {pr.id} ({pr.name}) w/o dates and outside wbs"
                )


def _check_loops(project: WBS):
    validated = set()
    for t in project.tasks:
        _check_loops_from_task(t, set(), validated)


def _check_loops_from_task(task: Task, visited_tasks: Set[int], validated: Set[int]):
    if task.id in validated:
        return

    if task.id in visited_tasks:
        raise RuntimeError(
            "Found circle",
            [str(t) + "-->" for t in visited_tasks] + [str(task.id) + ":" + task.name]
        )

    visited_tasks.add(task.id)

    for s in task.predecessors:
        _check_loops_from_task(s, visited_tasks, validated)

    visited_tasks.remove(task.id)
    validated.add(task.id)


@dataclass(frozen=True)
class ResourceUsageRow:
    """Row at resource usage report"""
    resource: IResource
    """Resource"""
    date: datetime
    """Date"""
    task: Task
    """Task"""
    units: float
    """Units of resource reserved for this resource, task and date"""


class ResourceUsageReport:
    """Resource usage report"""

    def __init__(self, rows: List[ResourceUsageRow]):
        self.__rows = rows

    def rows(self, _filter: Callable[[ResourceUsageRow], bool] = None) -> List[ResourceUsageRow]:
        return [dataclasses.replace(r)
                for r in self.__rows
                if _filter is None or _filter(r)]

    def reserved(self, resource: IResource, date: datetime) -> float:
        units = [item.units
                 for item in self.__rows
                 if item.resource == resource and item.date == date]

        return sum(units, 0)

    def __repr__(self):
        if len(self.__rows) == 0:
            return "Empty"

        dates = [item.date for item in self.__rows]
        min_date = min(dates)
        max_date = max(dates)

        resources = set([item.resource for item in self.__rows])

        table = TextTable()
        table.new_row()
        table.new_cell('DATE', RED)
        for k in resources:
            name = k.name if k.name is not None else 'none'
            table.new_cell(name.upper(), RED)

        d = min_date
        while d <= max_date:
            table.new_row()
            table.new_cell(d.strftime('%y-%m-%d'))
            for k in resources:
                val = self.reserved(k, d)
                if val == 0:
                    color = GREY
                elif val == k.get_available_units(d):
                    color = GREEN
                else:
                    color = YELLOW
                table.new_cell(f"{val:.1f}", color)
            d += timedelta(days=1)

        return table.text_repr(True)


class _ResourceUsage:

    def __init__(self):
        self.rows: List[ResourceUsageRow] = []

    @staticmethod
    def __get_key(date: datetime):
        return datetime(date.year, date.month, date.day, 0, 0, 0, 0)

    def reserve(self, resource: IResource, date: datetime, task: Task, units: float) -> float:
        self.rows.append(ResourceUsageRow(resource, self.__get_key(date), task, units))
        resource.reserve(date, task, units)
        return units

    def reserved(self, resource: IResource, date: datetime, task: Task = None) -> float:
        if task is None:
            units = [item.units
                     for item in self.rows
                     if item.resource == resource and item.date == self.__get_key(date)]
        else:
            units = [item.units
                     for item in self.rows
                     if item.resource == resource and item.date == self.__get_key(date) and item.task == task]

        return sum(units, 0)


@dataclass(frozen=True)
class Schedule:
    """WBS schedule result"""
    schedule: WBS
    """Clone of original WBS with calculated start and end dates on each task"""
    resources: List[IResource]
    """List of resources"""
    resource_usage: ResourceUsageReport
    """Resource usage report"""


class IScheduler(ABC):
    """WBS schedule calculator"""

    @abstractmethod
    def calc(self, wbs: WBS) -> Schedule:
        """
        Calculate WBS schedule
        :param wbs: Work burndown structure
        :return: WBS schedule
        """
        pass


class ForwardScheduler(IScheduler):
    """Forward WBS scheduler"""

    def __init__(
            self,
            start: datetime = None,
            resources: List[IResource] = None,
            balance_resources: bool = True,
            default_estimate: int = 0
    ):
        self.__start = start if start is not None else datetime.now()
        self.__resources = {} if resources is None else {r.name: r for r in resources}
        self.__balance_resources = balance_resources
        self.__default_estimate = default_estimate

    def __get_resource_nearest_available_date(
            self,
            resource: IResource,
            resource_usage: _ResourceUsage,
            start_date: datetime,
            task: Task,
            max_steps: int = 100000
    ) -> datetime:
        d = resource.get_nearest_availability_date(start_date, 1)

        for i in range(0, max_steps):
            reserved = resource_usage.reserved(resource, d) if self.__balance_resources \
                else resource_usage.reserved(resource, d, task)

            available = resource.get_available_units(d, task) - reserved
            if available > 0:
                percent = 1 - available / resource.get_available_units(d, task)
                d = datetime(d.year, d.month, d.day, 0, 0, 0, 0) + timedelta(hours=24 * percent)
                return d
            d += timedelta(days=1)

        raise RuntimeError(
            "Can't find nearest availability time for resource", resource.name,
            "after", start_date.strftime('%Y-%m-%d')
        )

    def __shift_by_resource_usage_and_calendar(
            self,
            resource: IResource,
            resource_usage: _ResourceUsage,
            start_date: datetime,
            task: Task,
            left_hours: float,
            max_steps: int = 100000
    ) -> datetime:
        if left_hours == 0:
            return start_date

        date = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0) - timedelta(days=1)

        days = 0
        date_available_units = 0
        while left_hours > 0:
            date += timedelta(days=1)
            reserved = resource_usage.reserved(resource, date) if self.__balance_resources \
                else resource_usage.reserved(resource, date, task)

            date_available_units = resource.get_available_units(date, task)
            max_available = date_available_units - reserved
            if max_available > 0:
                left_hours -= resource_usage.reserve(resource, date, task, min(left_hours, max_available))
            days += 1

            if days > max_steps:
                raise RuntimeError(f"Can't calculate {resource}, {start_date}, {max_steps}, {left_hours}")

        reserved = resource_usage.reserved(resource, date) if self.__balance_resources \
            else resource_usage.reserved(resource, date, task)
        percent = reserved / date_available_units
        return date + timedelta(hours=24 * percent)

    def __forward_pass(
            self,
            _task: Task,
            min_date: datetime,
            resource_usage: _ResourceUsage,
            calculated: List[int]
    ):
        if _task.id in calculated:
            return

        for pred in _task.predecessors:
            self.__forward_pass(pred, min_date, resource_usage, calculated)

        max_predecessor_ends = max([t.end for t in _task.predecessors if t.end is not None] + [min_date])

        for ch in _task.children:
            self.__forward_pass(ch, max_predecessor_ends, resource_usage, calculated)

        resource = self.__resources.setdefault(_task.resource, Resource(_task.resource))

        is_leaf = len(_task.children) == 0

        if _task.milestone:
            _task.start = _task.end = max_predecessor_ends
            _task.estimate = 0
            _task.spent = 0
        else:
            if _task.start is None:
                if is_leaf:
                    task_min_start = _task.min_start or datetime(1970, 1, 1)
                    _task.start = max(max_predecessor_ends, datetime.now(), task_min_start)
                    _task.start = self.__get_resource_nearest_available_date(
                        resource, resource_usage, _task.start, _task
                    )
                else:
                    children_starts = [t.start for t in _task.children if t.start is not None]
                    if len(children_starts) == 0:
                        children_starts = [datetime(1970, 1, 1)]
                    _task.start = max(min(children_starts), min_date)

            if _task.estimate is None:
                if is_leaf:
                    _task.estimate = self.__default_estimate
                else:
                    _task.estimate = sum([ch.estimate for ch in _task.children])

            if _task.spent is None:
                if is_leaf:
                    _task.spent = 0
                else:
                    _task.spent = sum([ch.spent for ch in _task.children])

            if _task.end is None:
                if is_leaf:
                    left_hours = max(_task.estimate - _task.spent, 0)
                    start = max(_task.start, datetime.now())
                    _task.end = max(
                        self.__shift_by_resource_usage_and_calendar(
                            resource, resource_usage, start, _task, left_hours
                        ),
                        datetime.now()
                    )
                else:
                    _task.end = max([t.end for t in _task.children if t.end is not None])

        calculated.append(_task.id)

    def calc(self, wbs: WBS) -> Schedule:
        _validate_graph_isolation(wbs)
        _check_loops(wbs)
        self.__check_no_end_dates_in_future(wbs)

        forward = wbs.clone()
        self.__prepare_tasks(forward)

        forward_resource_usage = _ResourceUsage()
        calculated = []
        for t in forward.roots:
            self.__forward_pass(t, self.__start, forward_resource_usage, calculated)

        return Schedule(
            forward,
            list(self.__resources.values()),
            ResourceUsageReport(forward_resource_usage.rows)
        )

    @staticmethod
    def __check_no_end_dates_in_future(project: WBS):
        now = datetime.now()
        for t in project.tasks:
            if t.end is not None and t.end > now:
                raise RuntimeError(f"Task {t.id} has end date in future. Can't schedule this task.")

    @staticmethod
    def __prepare_tasks(project: WBS):
        for t in project.tasks:
            if len(t.children) > 0:
                t.start = t.end = t.estimate = t.spent = None


class BackwardScheduler(IScheduler):
    def __init__(
            self,
            end: datetime = None,
            resources: List[IResource] = None,
            balance_resources: bool = True,
            default_estimate: int = 0
    ):
        self.__end = end if end is not None else datetime.now()
        self.__resources = {} if resources is None else {r.name: r for r in resources}
        self.__balance_resources = balance_resources
        self.__default_estimate = default_estimate

    def __get_resource_nearest_available_date(
            self,
            resource: IResource,
            resource_usage: _ResourceUsage,
            start_date: datetime,
            task: Task,
            max_steps: int = 1000
    ) -> datetime:
        d = resource.get_nearest_availability_date(start_date, -1) - timedelta(days=1)

        for i in range(0, max_steps):
            reserved = resource_usage.reserved(resource, d) if self.__balance_resources \
                else resource_usage.reserved(resource, d, task)

            available = resource.get_available_units(d, task) - reserved
            if available > 0:
                percent = 1 - available / resource.get_available_units(d, task)
                d = datetime(d.year, d.month, d.day, 0, 0, 0, 0) - timedelta(hours=24 * percent)
                return d
            d += timedelta(days=-1)

        raise RuntimeError(
            "Can't find nearest availability time for resource", resource.name,
            "after", start_date.strftime('%Y-%m-%d')
        )

    def __shift_by_resource_usage_and_calendar(
            self,
            resource: IResource,
            resource_usage: _ResourceUsage,
            start_date: datetime,
            task: Task,
            left_hours: float,
            max_steps: int = 100000
    ) -> datetime:
        if left_hours == 0:
            return start_date

        date = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0)

        days = 0
        while left_hours > 0:
            date += timedelta(days=-1)
            reserved = resource_usage.reserved(resource, date) if self.__balance_resources \
                else resource_usage.reserved(resource, date, task)

            max_available = resource.get_available_units(date, task) - reserved
            if max_available > 0:
                left_hours -= resource_usage.reserve(resource, date, task, min(left_hours, max_available))
            days += 1

            if days > max_steps:
                raise RuntimeError("Can't calculate")

        reserved = resource_usage.reserved(resource, date)
        percent = reserved / resource.get_available_units(date, task)

        return date + timedelta(days=1) - timedelta(hours=24 * percent)

    def __backward_pass(
            self,
            _task: Task,
            min_date: datetime,
            resource_usage: _ResourceUsage,
            calculated: List[int]
    ):
        if _task.id in calculated:
            return

        for pred in _task.successors:
            self.__backward_pass(pred, min_date, resource_usage, calculated)

        min_successor_starts = min([t.start for t in _task.successors if t.start is not None] + [min_date])

        for ch in reversed(_task.children):
            self.__backward_pass(ch, min_successor_starts, resource_usage, calculated)

        resource = self.__resources.setdefault(_task.resource, Resource(_task.resource))

        is_leaf = len(_task.children) == 0

        if _task.milestone:
            _task.start = _task.end = min_successor_starts
            _task.estimate = 0
            _task.spent = 0
        else:
            if _task.end is None:
                if is_leaf:
                    _task.end = min_successor_starts
                    _task.end = self.__get_resource_nearest_available_date(resource, resource_usage, _task.end, _task)
                    _task.end += timedelta(days=1)
                else:
                    children_ends = [t.end for t in _task.children if t.end is not None]
                    if len(children_ends) == 0:
                        _task.end = min_date
                    else:
                        _task.end = min(max(children_ends), min_date)

            if _task.estimate is None:
                if is_leaf:
                    _task.estimate = self.__default_estimate
                else:
                    _task.estimate = sum([ch.estimate for ch in _task.children])

            if _task.spent is None:
                if is_leaf:
                    _task.spent = 0
                else:
                    _task.spent = sum([ch.spent for ch in _task.children])

            if is_leaf:
                left_hours = max(_task.estimate - _task.spent, 0)
                end = min(_task.end, min_date)
                start = self.__shift_by_resource_usage_and_calendar(
                    resource, resource_usage, end, _task, left_hours
                )
                if _task.start is not None:
                    start = min(_task.start, start)
                _task.start = start
            else:
                _task.start = min([t.start for t in _task.children if t.start is not None])

        calculated.append(_task.id)

    @staticmethod
    def __prepare_tasks(project: WBS):
        for t in project.tasks:
            if len(t.children) > 0:
                t.start = t.end = t.estimate = t.spent = None

    def calc(self, project: WBS) -> Schedule:
        _validate_graph_isolation(project)
        _check_loops(project)

        backward = project.clone()
        self.__prepare_tasks(backward)

        backward_resource_usage = _ResourceUsage()
        backward_roots = backward.roots

        calculated = []
        for i in range(len(backward_roots) - 1, -1, -1):
            self.__backward_pass(backward_roots[i], self.__end, backward_resource_usage, calculated)

        return Schedule(
            backward,
            list(self.__resources.values()),
            ResourceUsageReport(backward_resource_usage.rows)
        )
