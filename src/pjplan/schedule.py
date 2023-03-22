from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Union

from pjplan import Task, WBS, IResource, DEFAULT_RESOURCE


class ResourceUsage:
    """Отчет об использовании ресурсов"""

    def __init__(self):
        self.__usage: Dict[str, Dict[datetime, float]] = {}

    @staticmethod
    def __get_key(date: datetime):
        return datetime(date.year, date.month, date.day, 0, 0, 0, 0)

    def reserve(self, resource_name: str, date: datetime, amount: float) -> float:
        resource_usage_dict = self.__usage.setdefault(resource_name, {})
        key = self.__get_key(date)
        resource_usage_dict[key] = resource_usage_dict.setdefault(key, 0) + amount
        return amount

    def usage(self, resource_name: str, date: datetime = None) -> Union[float, Dict[datetime, float]]:
        resource_usage_dict = self.__usage.setdefault(resource_name, {})
        if not date:
            return resource_usage_dict
        return resource_usage_dict.setdefault(self.__get_key(date), 0)


class IScheduler(ABC):
    """Планировщик проектов. Строит расписание проекта"""

    @abstractmethod
    def calc(self, wbs: WBS) -> (WBS, ResourceUsage):
        """
        Строит расписание проекта
        :param wbs: структура работ
        :return: Tuple (<копия wbs с установленными start и end у всех Task>, <Отчет об использовании ресурсов>)
        """
        pass


@dataclass
class Sprint:
    name: str = None
    start_date: datetime = None


class DefaultScheduler(IScheduler):
    def __init__(
            self,
            start: datetime = None,
            resources: List[IResource] = None,
            default_estimate: int = 0
    ):
        self.__start = start if start is not None else datetime.now()
        self.__resources = {} if resources is None else {r.name: r for r in resources}
        self.__default_estimate = default_estimate

    @staticmethod
    def __get_resource_nearest_available_date(
            resource: IResource,
            resource_usage: ResourceUsage,
            start_date: datetime
    ) -> datetime:
        d = resource.get_nearest_availability_date(start_date)

        for i in range(0, 1000):
            available = resource.available_hours_for_date(d) - resource_usage.usage(resource.name, d)
            if available > 0:
                percent = 1 - available / resource.available_hours_for_date(d)
                d = datetime(d.year, d.month, d.day, 0, 0, 0, 0) + timedelta(hours=24 * percent)
                return d
            d += timedelta(days=1)

        raise RuntimeError(
            "Can't find nearest availability time for resource", resource.name,
            "after", start_date.strftime('%Y-%m-%d')
        )

    @staticmethod
    def __shift_by_resource_usage_and_calendar(
            resource: IResource,
            resource_usage: ResourceUsage,
            start_date: datetime,
            left_hours: float
    ) -> datetime:
        if left_hours == 0:
            return start_date

        date = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0) - timedelta(days=1)
        days = 0
        while left_hours > 0:
            date += timedelta(days=1)
            max_available = resource.available_hours_for_date(date) - resource_usage.usage(resource.name, date)
            if max_available > 0:
                left_hours -= resource_usage.reserve(resource.name, date, min(left_hours, max_available))
            days += 1

            if days > 1000:
                raise RuntimeError("Can't calculate")

        reserved = resource_usage.usage(resource.name, date)
        percent = reserved / resource.available_hours_for_date(date)
        date += timedelta(hours=24 * percent)

        return date

    def __calc_task_dates(
            self,
            _task: Task,
            min_date: datetime,
            resource_usage: ResourceUsage,
            calculated: List[int]
    ):
        if _task.id in calculated:
            return

        for pred in _task.predecessors:
            self.__calc_task_dates(pred, min_date, resource_usage, calculated)

        max_predecessor_ends = max([t.end for t in _task.predecessors if t.end is not None] + [min_date])

        for ch in _task.children:
            self.__calc_task_dates(ch, max_predecessor_ends, resource_usage, calculated)

        resource = self.__resources.get(_task.resource, DEFAULT_RESOURCE)

        is_leaf = len(_task.children) == 0

        if _task.milestone:
            _task.start = _task.end = max_predecessor_ends
            _task.estimate = 0
            _task.spent = 0
        else:
            if _task.start is None:
                if is_leaf:
                    _task.start = max(max_predecessor_ends, datetime.now())
                    _task.start = self.__get_resource_nearest_available_date(resource, resource_usage, _task.start)
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
                    _task.spent = sum([min(ch.estimate, ch.spent) for ch in _task.children])

            if _task.end is None:
                if is_leaf:
                    left_hours = max(_task.estimate - _task.spent, 0)
                    start = max(_task.start, datetime.now())
                    _task.end = max(
                        self.__shift_by_resource_usage_and_calendar(resource, resource_usage, start, left_hours),
                        datetime.now()
                    )
                else:
                    _task.end = max([t.end for t in _task.children if t.end is not None])

        calculated.append(_task.id)

    @staticmethod
    def __prepare_tasks(project: WBS):
        for t in project:
            if len(t.children) > 0:
                t.start = t.end = None

    def calc(self, project: WBS) -> (WBS, ResourceUsage):
        res = project.clone()

        self.__validate_graph_isolation(res)
        self.__check_loops(res)
        self.__prepare_tasks(res)
        resource_usage = ResourceUsage()
        calculated = []
        for t in res.roots:
            self.__calc_task_dates(t, self.__start, resource_usage, calculated)
        return res, resource_usage

    @staticmethod
    def __validate_graph_isolation(project: WBS):
        all_tasks = {task.id: task for task in project}

        for t in all_tasks.values():
            for pr in t.predecessors:
                if pr.id not in all_tasks and (not pr.start or not pr.end):
                    raise RuntimeError(f"Task {t.id} ({t.name}) has predecessor {pr.id} ({pr.name}) w/o dates outside wbs")

    def __check_loops(self, project: WBS):
        for t in project:
            self.__check_loops_from_task(t, [])

    def __check_loops_from_task(self, task: Task, visited_tasks: List):
        if task in visited_tasks:
            raise RuntimeError(
                "Found circle",
                [str(t.id) + ":" + t.name + "-->" for t in visited_tasks] + [str(task.id) + ":" + task.name]
            )

        if task.predecessors is None:
            return

        visited_tasks.append(task)
        for s in task.predecessors:
            self.__check_loops_from_task(s, list(visited_tasks))