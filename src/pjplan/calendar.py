from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Union, Iterable, Callable

from pjplan.utils import GREEN, GREY, TextTable

_WEEK_DAY_NAMES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']


def _day_start(d: datetime) -> datetime:
    return datetime(d.year, d.month, d.day, 0, 0, 0, 0)


def _repr_units(hours) -> str:
    return f"{hours:.1f}"


def _repr_week_calendar(calendar: 'IWorkCalendar', start: datetime, end: datetime):
    week_dates = [
        datetime(2023, 4, 3),  # Mon
        datetime(2023, 4, 4),  # Tue
        datetime(2023, 4, 5),  # Wed
        datetime(2023, 4, 6),  # Thu
        datetime(2023, 4, 7),  # Fri
        datetime(2023, 4, 8),  # Sat
        datetime(2023, 4, 9),  # Sun
    ]

    res = 'Weekly: ' + _repr_interval(start, end) + '\n'

    table = TextTable()

    table.new_row()
    for i in range(0, 7):
        table.new_cell(_WEEK_DAY_NAMES[i], GREEN)

    table.new_row()
    for i in range(0, 7):
        units = calendar.get_available_units(week_dates[i])
        val = _repr_units(units)
        table.new_cell(val, GREY if units == 0 else None)

    return res + table.text_repr(True)


def _repr_direct_calendar(calendar: 'IWorkCalendar', dates: Iterable[datetime]):
    res = 'Direct:\n'

    table = TextTable()
    table.new_row()
    table.new_cell('DATE', GREEN)
    table.new_cell('UNITS', GREEN)

    for d in dates:
        table.new_row()
        table.new_cell(d.strftime('%Y-%m-%d'))

        units = calendar.get_available_units(d)
        val = _repr_units(units)
        table.new_cell(val, GREY if units == 0 else None)

    return res + table.text_repr(True)


def _repr_calendar_op(calendars: Iterable['IWorkCalendar'], op: str):
    cals = ''
    i = 1
    for cal in calendars:
        cals += '\n\nCal' + str(i) + ':\n'
        cals += cal.__repr__()
        i += 1

    header = (' ' + op + ' ').join(['Cal' + str(k) for k in range(1, i)])

    return header + cals


def _repr_standard_calendars(self, calendars: Iterable['IWorkCalendar'], op: str):
    cal_types = {}
    for cal in calendars:
        cal_types.setdefault(cal.__class__.__name__, []).append(cal)

    del cal_types['FixedCalendar']

    if len(cal_types) > 1:
        return _repr_calendar_op(calendars, op)

    k, v = list(cal_types.items())[0]

    if len(v) > 1:
        return _repr_calendar_op(calendars, op)
    if k == 'WeeklyCalendar':
        return _repr_week_calendar(self, v[0].start, v[0].end)
    elif k == 'DirectCalendar':
        return _repr_direct_calendar(self, v[0].dates)

    return _repr_calendar_op(calendars, op)


def _repr_interval(start: Optional[datetime], end: Optional[datetime]):
    res = '['
    res += start.strftime('%Y-%m-%d') if start is not None else '-'
    res += ', '
    res += end.strftime('%Y-%m-%d') if end is not None else '-'
    res += ']'
    return res


class IWorkCalendar(ABC):
    """Work calendar interface"""

    @abstractmethod
    def get_available_units(self, date: datetime) -> Optional[float]:
        """
        Returns number of work hours for date or None
        :param date: date
        :return: number of work hours
        """
        pass

    def apply(self, func: Callable[[float], float]) -> 'IWorkCalendar':
        return FuncCalendar(self, func)

    @staticmethod
    def __prepare_calendar(other):
        if type(other) in [int, float]:
            return FixedCalendar(other)
        return other

    def __or__(self, other):
        return WorkCalendarDisjunction([self, self.__prepare_calendar(other)])

    def __truediv__(self, other: Union[int, float, 'IWorkCalendar']):
        if other == 0:
            raise RuntimeError("Division by 0")

        return WorkCalendarDiv([self, self.__prepare_calendar(other)])

    def __mul__(self, other):
        return WorkCalendarsMul([self, self.__prepare_calendar(other)])

    def __add__(self, other):
        return WorkCalendarSum([self, self.__prepare_calendar(other)])

    def __sub__(self, other):
        return WorkCalendarSub([self, self.__prepare_calendar(other)])


class WorkCalendarDisjunction(IWorkCalendar):

    def __init__(
            self,
            calendars: Iterable[IWorkCalendar]
    ):
        self.__calendars = calendars if calendars is not None else []

    def get_available_units(self, date: datetime) -> Optional[float]:
        for c in self.__calendars:
            units = c.get_available_units(date)
            if units is not None and units > 0:
                return units
        return None

    def __repr__(self):
        return _repr_calendar_op(self.__calendars, '|')


class WorkCalendarSum(IWorkCalendar):

    def __init__(
            self,
            calendars: Iterable[IWorkCalendar]
    ):
        self.__calendars = calendars if calendars is not None else []

    def get_available_units(self, date: datetime) -> Optional[float]:
        units = None
        for c in self.__calendars:
            c_units = c.get_available_units(date)
            if c_units is None:
                continue
            if units is None:
                units = c_units
            else:
                units += c_units
        return units

    def __repr__(self):
        return _repr_standard_calendars(self, self.__calendars, '+')


class WorkCalendarSub(IWorkCalendar):

    def __init__(
            self,
            calendars: Iterable[IWorkCalendar]
    ):
        self.__calendars = calendars if calendars is not None else []

    def get_available_units(self, date: datetime) -> Optional[float]:
        units = None
        for c in self.__calendars:
            c_units = c.get_available_units(date)
            if c_units is None:
                continue
            if units is None:
                units = c_units
            else:
                units -= c_units
        if units is None or units < 0:
            return None
        return units

    def __repr__(self):
        return _repr_standard_calendars(self, self.__calendars, '-')


class WorkCalendarsMul(IWorkCalendar):

    def __init__(
            self,
            calendars: Iterable[IWorkCalendar]
    ):
        self.__calendars = calendars if calendars is not None else []

    def get_available_units(self, date: datetime) -> Optional[float]:
        units = None
        for c in self.__calendars:
            c_units = c.get_available_units(date)
            if c_units is None:
                continue
            if units is None:
                units = c_units
            else:
                units *= c_units
        return units

    def __repr__(self):
        return _repr_standard_calendars(self, self.__calendars, '*')


class WorkCalendarDiv(IWorkCalendar):

    def __init__(
            self,
            calendars: Iterable[IWorkCalendar]
    ):
        self.__calendars = calendars if calendars is not None else []

    def get_available_units(self, date: datetime) -> Optional[float]:
        units = None
        for c in self.__calendars:
            c_units = c.get_available_units(date)
            if c_units is None:
                continue
            if units is None:
                units = c_units
            else:
                units /= c_units
        return units

    def __repr__(self):
        return _repr_standard_calendars(self, self.__calendars, '/')


class FuncCalendar(IWorkCalendar):

    def __init__(self, calendar: IWorkCalendar, func: Callable[[float], float]):
        self.__calendar = calendar
        self.__func = func

    def get_available_units(self, date: datetime) -> Optional[float]:
        return self.__func(self.__calendar.get_available_units(date))

    def __repr__(self):
        res = 'Func: ' + str(self.__func) + '\n'
        res += '\n'
        res += self.__calendar.__repr__()
        return res


class FixedCalendar(IWorkCalendar):

    def __init__(self, units: float, start: Optional[datetime] = None, end: Optional[datetime] = None):
        if units < 0:
            raise RuntimeError("Value must be >= 0")

        self.__units = units
        self.__start = start
        self.__end = end

    def get_available_units(self, date: datetime) -> Optional[float]:
        if self.__start is not None and date < self.__start:
            return 0
        if self.__end is not None and date > self.__end:
            return 0

        return self.__units

    def __repr__(self):
        return "Fixed: " + _repr_units(self.__units) + ' ' + _repr_interval(self.__start, self.__end)


class DirectCalendar(IWorkCalendar):

    def __init__(
            self,
            units: Optional[Dict[datetime, float]] = None
    ):
        if units is not None:
            self.__units = {_day_start(k): v for k, v in units.items()}
        else:
            self.__units = {}

    def get_available_units(self, date: datetime) -> Optional[float]:
        key = _day_start(date)
        if key in self.__units:
            return self.__units[key]
        else:
            return None

    def set_units(self, units: Dict[datetime, float]):
        self.__units = self.__units | units

    @property
    def dates(self):
        return list(self.__units.keys())

    def __repr__(self):
        return _repr_direct_calendar(self, self.__units.keys())


class WeeklyCalendar(IWorkCalendar):
    """
    IWorkCalendar implementation with following arguments:
    1. working_days - list of week working days 0 - monday, 1 - tuesday, etc.
    2. day_hours - number of working hours in working day
    """

    def __init__(
            self,
            start: Optional[datetime] = None,
            end: Optional[datetime] = None,
            days: List[int] = None,
            units_per_day: Union[int, float, Dict[int, float]] = None,
    ):
        WeeklyCalendar.__check_working_days(days)

        if units_per_day is None:
            raise RuntimeError("units_per_day not specified")

        if days is not None:
            if type(units_per_day) is float or type(units_per_day) is int:
                if units_per_day < 0:
                    raise RuntimeError("units_per_day < 0")
                self.__day_hours = {}
                for i in range(0, 7):
                    self.__day_hours[i] = units_per_day if i in days else 0
            else:
                raise RuntimeError("If units_per_day specified as dict, working_days must be None")

        else:
            if type(units_per_day) is dict:
                self.__day_hours = {}
                for i in range(0, 7):
                    val = units_per_day[i] if i in units_per_day else 0
                    if val < 0:
                        raise RuntimeError("units_per_day < 0")
                    self.__day_hours[i] = val
            else:
                raise RuntimeError("If units_per_day specified as int or float, working_dates must be set")

        self.__start = start
        self.__end = end

    @staticmethod
    def __check_start_end(start: Optional[datetime], end: Optional[datetime]):
        if start is None or end is None:
            return

        if start > end:
            raise RuntimeError("Start after end")

    @staticmethod
    def __check_working_days(working_days: List[int]):
        if working_days is None:
            return
        for v in working_days:
            if v < 0 or v > 6:
                raise RuntimeError("Working days must be in range [0 (monday), 6(sunday]")

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end

    def get_week_day_hours(self) -> Dict[int, float]:
        return dict(self.__day_hours)

    def get_available_units(self, date: datetime) -> Optional[float]:
        if self.__start is not None and date < self.__start:
            return None

        if self.__end is not None and date > self.__end:
            return None

        return self.__day_hours[date.weekday()]

    def clone(self) -> 'WeeklyCalendar':
        return WeeklyCalendar(units_per_day=self.__day_hours)

    def __repr__(self):
        return _repr_week_calendar(self, self.__start, self.__end)


DEFAULT_CALENDAR = WeeklyCalendar(
    days=[0, 1, 2, 3, 4],
    units_per_day=8
)
"""Default calendar monday-friday with 8 hours per day"""
