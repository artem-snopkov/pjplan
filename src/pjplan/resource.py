from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from pjplan import IWorkCalendar, DEFAULT_CALENDAR, Task


class IResource(ABC):
    """Ресурс - человек, машина или любая другая сущность, которая необходима для выполнения работы (Task)"""

    def __init__(self, name: str):
        """
        :param name: уникальное название ресурса.
        """
        self.name = name

    @abstractmethod
    def get_available_units(self, date: datetime, task: Optional[Task] = None) -> float:
        """
        Возвращает количество доступных рабочих часов ресурса в указанную дату
        :param date: дата
        :param task: задача, под которую нужны ресурсы. None, если конкретной задачи нет
        :return: количество доступных часов ресурса
        """
        pass

    def get_nearest_availability_date(self, start_date: datetime, direction: int, max_days=100000) -> datetime:
        """
        Возвращает ближайшую дату доступности ресурса, начиная со start_date
        :param direction: 1 или -1
        :param start_date: дата начала поиска
        :param max_days: максимальный интервал поиска (в днях)
        :return: дата доступности
        """
        step = 0
        while step < max_days:
            if direction < 0:
                if self.get_available_units(start_date - timedelta(days=1), None) > 0.0:
                    return start_date
            else:
                if self.get_available_units(start_date, None) > 0.0:
                    return start_date
            start_date += timedelta(days=direction)
            step += 1

        raise RuntimeError(
            "Can't find nearest availability time for resource", self.name,
            "after", start_date.strftime('%Y-%m-%d')
        )

    def reserve(self, date: datetime, task: Task, units: float):
        pass


class Resource(IResource):

    def __init__(
            self,
            name: str,
            calendar: IWorkCalendar = DEFAULT_CALENDAR
    ):
        """
        :param name: уникальное наименование ресурса
        :param calendar: рабочий календарь

        Пример интервалов доступности:
        availability = [(datetime(2000, 1, 1), 50), (datetime(2000, 2, 1), 100)]
        означает, что:
        1. До 2000-01-01 ресурс недоступен
        2. В период с 2000-01-01 по 2000-02-01 ресурс доступен на 50%
        3. После 2000-02-01 ресурс доступен на 100%
        """
        super().__init__(name)
        self.calendar = calendar

    def get_available_units(self, date: datetime, task: Optional[Task] = None) -> float:
        units = self.calendar.get_available_units(date)
        return 0 if units is None else units

    def __str__(self):
        return self.name

    def __repr__(self):
        res = f'{self.name}\n'
        res += self.calendar.__repr__()
        return res


DEFAULT_RESOURCE = Resource("default")
