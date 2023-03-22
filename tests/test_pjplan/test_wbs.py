from datetime import datetime
from unittest import TestCase

from pjplan import WBS, Task


class TestWBS(TestCase):

    def test_start_end_none(self):
        wbs = WBS()

        self.assertIsNone(wbs.start)
        self.assertIsNone(wbs.end)

        wbs // Task(1, "1")
        wbs // Task(2, "2")

        self.assertIsNone(wbs.start)
        self.assertIsNone(wbs.end)

    def test_start_end(self):
        wbs = WBS()
        wbs // Task(1, "1", start=datetime(2022, 1, 1), end=datetime(2022, 2, 1))
        wbs // Task(2, "2", start=datetime(2023, 1, 1), end=datetime(2023, 2, 1))

        self.assertEqual(wbs(1).start, wbs.start)
        self.assertEqual(wbs(2).end, wbs.end)

    def test_iter(self):
        wbs = WBS()
        wbs // Task(1, "1")
        wbs // Task(2, "2")

        tasks = [t for t in wbs]
        self.assertEqual(2, len(tasks))

    def test_len(self):
        wbs = WBS()
        wbs // Task(1, "1")
        wbs // Task(2, "2")

        self.assertEqual(2, len(wbs))

    def test_clone(self):

        prj = WBS('0')
        t1 = prj // Task(1, '1')
        t2 = prj // Task(2, '2')

        prj2 = prj.clone()
        prj2(1).name = 'n1'

        self.assertEqual('1', t1.name)
        self.assertEqual(2, len(prj2.roots))
