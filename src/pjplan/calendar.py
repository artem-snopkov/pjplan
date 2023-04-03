from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Union, Iterable

from pjplan.utils import colored, GREEN, WHITE, GREY

_WEEK_DAY_NAMES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']


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


class WeeklyCalendar(IWorkCalendar):
    """
    IWorkCalendar implementation with following arguments:
    1. working_days - list of week working days 0 - monday, 1 - tuesday, etc.
    2. day_hours - number of working hours in working day
    3. exceptions - Dict[<date>, <number of working hours in this date>]
    """
    def __init__(
            self,
            working_week_days: List[int] = None,
            week_day_hours: Union[int, float, Dict[int, float]] = None,
            exceptions: Optional[Dict[datetime, float]] = None
    ):
        WeeklyCalendar.__check_working_days(working_week_days)
        WeeklyCalendar.__check_day_hours(week_day_hours)

        if working_week_days is not None:
            if week_day_hours is None:
                week_day_hours = 0

            if type(week_day_hours) is float or type(week_day_hours) is int:
                self.__day_hours = {}
                for i in range(0, 7):
                    self.__day_hours[i] = week_day_hours if i in working_week_days else 0
            else:
                raise RuntimeError("If day_hours specified as dict, working_days must be None")

        else:
            if type(week_day_hours) is dict:
                self.__day_hours = {}
                for i in range(0, 7):
                    self.__day_hours[i] = week_day_hours[i] if i in week_day_hours else 0
            else:
                raise RuntimeError("If day_hours specified as int or float, working_dates must be set")

        self.__exceptions = self.__prepare_exceptions(exceptions)

    @staticmethod
    def __check_working_days(working_days: List[int]):
        if working_days is None:
            return
        for v in working_days:
            if v < 0 or v > 6:
                raise RuntimeError("Working days must be in range [0 (monday), 6(sunday]")

    @staticmethod
    def __check_day_hours(
            day_hours: Union[int, float, Dict[int, float]]
    ):
        if day_hours is None:
            return

        if type(day_hours) is int or type(day_hours) is float:
            if day_hours < 0 or day_hours > 24:
                raise RuntimeError("day_hours must be in range [0, 24]")
            return

        for k, v in day_hours.items():
            if k < 0 or k > 6:
                raise RuntimeError("day_hours.keys() must be in range [0 (monday), 6(sunday]")
            if v < 0 or v > 24:
                raise RuntimeError("day_hours.values() must be in range [0, 24]")

    @staticmethod
    def __prepare_exceptions(exceptions: Optional[Dict[datetime, float]]) -> Dict[datetime, float]:
        if exceptions is None:
            return {}
        res = {}
        for k, v in exceptions.items():
            if v < 0 or v > 24:
                raise RuntimeError("exceptions.values() must be in range [0, 24]")
            res[WeeklyCalendar.__key(k)] = v
        return res

    @staticmethod
    def __key(d: datetime) -> datetime:
        return datetime(d.year, d.month, d.day, 0, 0, 0, 0)

    def add_days_off(self, dates: Union[datetime, Iterable[datetime]]):
        if isinstance(dates, datetime):
            dates = [dates]

        for d in dates:
            self.__exceptions[self.__key(d)] = 0

    def get_week_day_hours(self) -> Dict[int, float]:
        return dict(self.__day_hours)

    def get_exceptions(self) -> Dict[datetime, float]:
        return dict(self.__exceptions)

    def get_available_hours(self, date: datetime) -> float:
        key = self.__key(date)
        if key in self.__exceptions:
            return self.__exceptions[key]

        return self.__day_hours[date.weekday()]

    def clone(self) -> 'WeeklyCalendar':
        return WeeklyCalendar(week_day_hours=self.__day_hours, exceptions=self.__exceptions)

    @staticmethod
    def __repr_hours(hours) -> str:
        return f" {hours:.1f} "

    def __repr__(self):
        day_len = {}
        for i in range(0, 7):
            day_len[i] = max(5, len(self.__repr_hours(self.__day_hours[i])))

        res = "|"
        for i in range(0, 7):
            res += colored(f' {_WEEK_DAY_NAMES[i]} ' + ' '*max(day_len[i] - 5, 0), GREEN) + '|'
        res += '\n'

        res += '|'
        for i in range(0, 7):
            val = self.__repr_hours(self.__day_hours[i])
            vl = len(val)
            if self.__day_hours[i] == 0:
                val = colored(val, GREY)
            res += val + ' '*max(day_len[i] - vl, 0) + '|'

        if len(self.__exceptions) == 0:
            return res

        res += '\n\n'
        res += 'Exceptions:\n'

        res += '| ' + colored('DATE', GREEN) + '       | ' + colored('HOURS', GREEN) + ' |'
        for k, v in self.__exceptions.items():
            res += '\n| ' + k.strftime('%Y-%m-%d') + ' |'
            val = self.__repr_hours(v)
            vl = len(val)
            if v == 0:
                val = colored(val, GREY)
            res += val + ' '*max(7 - vl, 0) + '|'

        return res


DEFAULT_CALENDAR = WeeklyCalendar(
    working_week_days=[0, 1, 2, 3, 4],
    week_day_hours=8
)
"""Default calendar monday-friday with 8 hours per day"""
