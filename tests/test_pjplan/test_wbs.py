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

    def test_change_field(self):
        wbs = WBS()
        wbs // Task(1, "1", resource='1')
        wbs // Task(2, "2", resource='2')
        wbs // Task(3, "3", resource='2')

        wbs(resource='2').resource='1'

        self.assertEqual('1', wbs(2).resource)
        self.assertEqual('1', wbs(3).resource)

    def test_clone(self):

        prj = WBS('0')
        t1 = prj // Task(1, '1')
        t2 = prj // Task(2, '2')

        prj2 = prj.clone()
        prj2(1).name = 'n1'

        self.assertEqual('1', t1.name)
        self.assertEqual(2, len(prj2.roots))

    def test_insert(self):
        prj = WBS()
        prj // Task(1, '1')
        prj // Task(2, '2')

        prj.roots.insert(0, Task(3, '3'))

        self.assertEqual(3, prj.roots[0].id)
        self.assertEqual(1, prj.roots[1].id)
        self.assertEqual(2, prj.roots[2].id)
        self.assertEqual(3, len(prj.roots))

    def test_move_before(self):
        prj = WBS()
        prj // Task(1, '1')
        prj // Task(2, '2')

        prj.roots.move_before(prj(2), prj(1))
        self.assertEqual(2, prj.roots[0].id)
        self.assertEqual(1, prj.roots[1].id)
        self.assertEqual(2, len(prj.roots))

    def test_move_after(self):
        prj = WBS()
        prj // Task(1, '1')
        prj // Task(2, '2')

        prj.roots.move_after(prj(1), prj(2))
        self.assertEqual(2, prj.roots[0].id)
        self.assertEqual(1, prj.roots[1].id)
        self.assertEqual(2, len(prj.roots))