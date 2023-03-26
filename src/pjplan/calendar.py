from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple


class IWorkCalendar(ABC):
    """
    Рабочий календарь
    """

    @abstractmethod
    def get_available_hours(self, date: datetime) -> float:
        """
        Возвращает количество рабочих часов в указанную дату
        :param date: дата
        :return: количество рабочих часов
        """
        pass


@dataclass
class GenericCalendar(IWorkCalendar):
    """
    Реализация IWorkCalendar, в которой календарь задается следующими параметрами:
    1. working_days - список рабочих дней в неделе 0 - пнд, 1 - вт и т.д.
    2. day_hours - количество рабочих часов в каждом рабочем дне
    3. days_off - список дат недоступности
    """
    working_days: List[int] = None,
    day_hours: int = None
    days_off: List[datetime] = None

    def get_available_hours(self, date: datetime) -> float:
        if date.weekday() not in self.working_days:
            return 0

        if self.days_off and date not in self.days_off:
            return 0

        return self.day_hours


class CapacityCalendar(IWorkCalendar):
    """
    Реализация IWorkCalendar, в которой календарь задается следующими параметрами:
    1. capacities - список пар (дата, количество рабочих часов)
    2. working_days - список рабочих дней в неделе 0 - пнд, 1 - вт и т.д.

    Определение доступного времени в определенную дату работает так:
    1. Если дата есть в списке capacities, то возвращается соответствующее значение из capacities
    2. Иначе проверяется, входит ли дата в working_days. Если входит, возвращается 8, иначе 0
    """

    def __init__(self, capacities: List[Tuple[datetime, float]], working_days=None):
        self.capacities = {self.__key(c[0]): c[1] for c in capacities}
        self.__calc_min_max_dates()

        if working_days is None:
            working_days = [0, 1, 2, 3, 4]

        self.working_days = working_days

    @staticmethod
    def __key(d: datetime) -> str:
        return d.strftime('%Y-%m-%d')

    def __calc_min_max_dates(self):
        if len(self.capacities) == 0:
            self.max_date = datetime(1970, 1, 1)
            self.min_date = datetime(1970, 1, 1)
        else:
            self.max_date = max([datetime.strptime(c, '%Y-%m-%d') for c in self.capacities.keys()])
            self.min_date = min([datetime.strptime(c, '%Y-%m-%d') for c in self.capacities.keys()])

    def set_capacities(self, from_date: datetime, to_date: datetime, value: float):
        d = from_date
        while d <= to_date:
            self.capacities[self.__key(d)] = value
            d += timedelta(days=1)

        self.__calc_min_max_dates()

    def get_available_hours(self, date):
        if date > self.max_date or date < self.min_date:
            if date.weekday() not in self.working_days:
                return 0
            return 8

        capacity = self.capacities.get(self.__key(date))
        return capacity if capacity is not None else 0

    def __repr__(self) -> str:
        return f'min={self.min_date}, max={self.max_date}'


DEFAULT_CALENDAR = GenericCalendar(
    working_days=[0, 1, 2, 3, 4],
    day_hours=8
)