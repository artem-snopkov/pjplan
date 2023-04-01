from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple


class IWorkCalendar(ABC):
    """Work calendar interface"""

    @abstractmethod
    def get_available_hours(self, date: datetime) -> float:
        """
        Returns number of work hours for date
        :param date: date
        :return: number of work hours
        """
        pass


@dataclass
class GenericCalendar(IWorkCalendar):
    """
    IWorkCalendar implementation with following arguments:
    1. working_days - list of week working days 0 - monday, 1 - tuesday, etc.
    2. day_hours - number of working hours in working day
    3. dates_off - list of dates off
    """
    working_days: List[int] = None,
    day_hours: int = None
    dates_off: List[datetime] = None

    def get_available_hours(self, date: datetime) -> float:
        if date.weekday() not in self.working_days:
            return 0

        if self.dates_off and date not in self.dates_off:
            return 0

        return self.day_hours

    def __repr__(self):
        # TODO визуализировать в виде таблицы
        return f"""
        Working days: {self.working_days}
        Day hours: {self.day_hours}
        Dates off: {self.dates_off}
        """

class CapacityCalendar(IWorkCalendar):
    """
    IWorkCalendar implementation with following parameters:
    1. capacities - list of pairs (date, number of working hours)
    2. working_days - list of working week days 0 - monday, 1 - tuesday etc.
    3. day_hours - number of working hours in working day

    get_available_hours uses following algorithm:
    1. if date in capacities, return working hours from this capacity
    2. Else check if date in working_days. If yes, returns day_hours. Else returns 0
    """

    def __init__(self, capacities: List[Tuple[datetime, float]], working_days=None, day_hours=8):
        self.capacities = {self.__key(c[0]): c[1] for c in capacities}
        self.__calc_min_max_dates()

        if working_days is None:
            working_days = [0, 1, 2, 3, 4]

        self.working_days = working_days
        self.day_hours = day_hours

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
        """
        Upsert capacities to calendar
        :param from_date: from date
        :param to_date: to date
        :param value: day_hours
        """
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
        # TODO визуализировать в виде таблицы
        return f'min={self.min_date}, max={self.max_date}'


DEFAULT_CALENDAR = GenericCalendar(
    working_days=[0, 1, 2, 3, 4],
    day_hours=8
)
"""Default calendar monday-friday with 8 hours per day"""
