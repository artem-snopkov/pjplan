import unittest
from datetime import datetime

from pjplan import WeeklyCalendar


class TestWeeklyCalendar(unittest.TestCase):

    def test_create_bad_params(self):
        # Empty
        self.assertRaises(RuntimeError, lambda: WeeklyCalendar())
        # No hour_per_days
        self.assertRaises(RuntimeError, lambda: WeeklyCalendar(days=[0, 1, 2, 3, 4]))
        # No days
        self.assertRaises(RuntimeError, lambda: WeeklyCalendar(units_per_day=8))
        # days out of range
        self.assertRaises(RuntimeError, lambda: WeeklyCalendar(days=[9], units_per_day=8))
        self.assertRaises(RuntimeError, lambda: WeeklyCalendar(days=[-1], units_per_day=8))
        # hours out of range
        self.assertRaises(RuntimeError, lambda: WeeklyCalendar(days=[1], units_per_day=-1))
        # hours_per_pay is map and days
        self.assertRaises(RuntimeError, lambda: WeeklyCalendar(days=[1], units_per_day={1: 8}))
        # start after end
        self.assertRaises(RuntimeError, lambda: WeeklyCalendar(start=datetime(2023, 1, 1), end=datetime(2022, 1, 1)))

    def test_get_available_hours_1(self):
        cal = WeeklyCalendar(days=[0, 1, 2, 3, 4], units_per_day=8)

        self.assertEqual(8, cal.get_available_units(datetime(2023, 4, 3)))
        self.assertEqual(8, cal.get_available_units(datetime(2023, 4, 4)))
        self.assertEqual(8, cal.get_available_units(datetime(2023, 4, 5)))
        self.assertEqual(8, cal.get_available_units(datetime(2023, 4, 6)))
        self.assertEqual(8, cal.get_available_units(datetime(2023, 4, 7)))
        self.assertEqual(0, cal.get_available_units(datetime(2023, 4, 8)))
        self.assertEqual(0, cal.get_available_units(datetime(2023, 4, 9)))

    def test_get_available_hours_2(self):
        cal = WeeklyCalendar(units_per_day={0: 1, 1: 2, 2: 3, 3: 4, 4: 5})

        self.assertEqual(1, cal.get_available_units(datetime(2023, 4, 3)))
        self.assertEqual(2, cal.get_available_units(datetime(2023, 4, 4)))
        self.assertEqual(3, cal.get_available_units(datetime(2023, 4, 5)))
        self.assertEqual(4, cal.get_available_units(datetime(2023, 4, 6)))
        self.assertEqual(5, cal.get_available_units(datetime(2023, 4, 7)))
        self.assertEqual(0, cal.get_available_units(datetime(2023, 4, 8)))
        self.assertEqual(0, cal.get_available_units(datetime(2023, 4, 9)))
