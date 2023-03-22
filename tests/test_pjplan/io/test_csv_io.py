import os
import shutil
from datetime import datetime
from unittest import TestCase

from pjplan import WBS, Task, read_csv, write_csv


class TestCsvIO(TestCase):

    TEST_DIR = './test_data'

    @classmethod
    def setUpClass(cls) -> None:
        if not os.path.exists(cls.TEST_DIR):
            os.mkdir('./test_data')

    @classmethod
    def tearDownClass(cls) -> None:
        # shutil.rmtree(cls.TEST_DIR)
        pass

    def assertTasksEqual(self, t1, t2):
        self.assertEqual(t1.name, t2.name)
        self.assertEqual(t1.resource, t2.resource)
        self.assertEqual(t1.start, t2.start)
        self.assertEqual(t1.end, t2.end)
        self.assertEqual(t1.estimate, t2.estimate)
        self.assertEqual(t1.spent, t2.spent)
        self.assertEqual(t1.milestone, t2.milestone)

        for k, v in t1.__dict__.items():
            self.assertTrue(k in t2.__dict__, f"{k} attr not found")
            self.assertEqual(t1.__getattribute__(k), t2.__getattribute__(k), f"{k} are not equals")

    # noinspection PyStatementEffect
    def test_read_write(self):
        p = WBS()
        t1 = p // Task(1)
        t2 = t1 // Task(2, "Name 2")
        t3 = t2 >> p // Task(3)
        t4 = p // Task(4, start=datetime(2025, 1, 1), end=datetime(2025, 2, 1))
        t5 = p // Task(5, estimate=10, spent=8)
        t6 = p // Task(6, milestone=True)
        t7 = p // Task(7, resource='Test')
        t8 = p // Task(8, attr1='Test1')
        t9 = p // Task(9, attr2='Test2')

        file = os.path.join(self.TEST_DIR, 'test.csv')

        write_csv(p, file)

        r = read_csv(file)

        self.assertTasksEqual(t1, r(1))

        self.assertTasksEqual(t2, r(2))
        self.assertTrue(r(2) in p(1).children)
        self.assertTrue(r(1) == r(2).parent)

        self.assertTasksEqual(t3, r(3))
        self.assertTrue(r(3) in r(2).successors)
        self.assertTrue(r(2) in r(3).predecessors)

        self.assertTasksEqual(t4, r(4))

        self.assertTasksEqual(t5, r(5))
        self.assertTasksEqual(t6, r(6))
        self.assertTasksEqual(t7, r(7))
        self.assertTasksEqual(t8, r(8))
        self.assertTasksEqual(t9, r(9))
