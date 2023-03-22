from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from pjplan import IWorkCalendar, DEFAULT_CALENDAR


class IResource(ABC):
    """Ресурс - человек, машина или любая другая сущность, которая необходима для выполнения работы (Task)"""

    def __init__(self, name: str):
        """
        :param name: уникальное название ресурса.
        """
        self.name = name

    @abstractmethod
    def available_hours_for_date(self, date: datetime) -> float:
        pass

    def get_nearest_availability_date(self, start_date: datetime, max_days=100) -> datetime:
        """
        Возвращает ближайшую дату доступности ресурса, начиная со start_date
        :param start_date: дата начала поиска
        :param max_days: максимальный интервал поиска (в днях)
        :return: дата доступности
        """
        step = 0
        while step < max_days:
            if self.available_hours_for_date(start_date) > 0:
                return start_date
            start_date += timedelta(days=1)
            step += 1

        raise RuntimeError(
            "Can't find nearest availability time for resource", self.resource,
            "after", start_date.strftime('%Y-%m-%d')
        )


class Resource(IResource):

    def __init__(
            self,
            name: str,
            calendar: IWorkCalendar = DEFAULT_CALENDAR,
            availability: List[Tuple[datetime, float]] = None
    ):
        """
        :param name: уникальное наименование ресурса
        :param calendar: рабочий календарь
        :param availability: процент доступности ресурса. Задается интервалами.

        Пример интервалов доступности:
        availability = [(datetime(2000, 1, 1), 50), (datetime(2000, 2, 1), 100)]
        означает, что:
        1. До 2000-01-01 ресурс недоступен
        2. В период с 2000-01-01 по 2000-02-01 ресурс доступен на 50%
        3. После 2000-02-01 ресурс доступен на 100%
        """
        super().__init__(name)
        self.calendar = calendar
        self.availability = availability

    def available_hours_for_date(self, date: datetime) -> float:
        """
        Возвращает количество доступных рабочих часов ресурса в указанную дату
        :param date: дата
        :return: количество доступных часов ресурса
        """

        available_hours = self.calendar.get_available_hours(date)
        if available_hours == 0:
            return 0

        # Определяем ближайший интервал доступности ресурса
        usage: Optional[Tuple[datetime, float]] = None
        for u in self.availability:
            if u[0] > date:
                continue
            if usage is None or usage[0] < u[0]:
                usage = u

        if usage is None:
            return 0

        return available_hours * usage[1] / 100


DEFAULT_RESOURCE = Resource("default", DEFAULT_CALENDAR, [(datetime(1970, 1, 1), 100)])
