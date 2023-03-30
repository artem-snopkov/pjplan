from datetime import datetime
from unittest import TestCase

import pjplan as pl
from pjplan import Task, WBS


class TestDefaultScheduler(TestCase):

    def test_calc_1(self):
        p = WBS("project")
        with p // Task(1, "1") as first:
            with first // Task(2, "2", start=datetime.now(), end=datetime(2022, 11, 1)) as second:
                second // Task(3, "3", start=datetime(2022, 11, 1), end=datetime(2022, 12, 1), resource='Test')

        s, usage = pl.DefaultScheduler(start=datetime(2022, 1, 1)).calc(p)

        self.assertEqual(p(3).start, s(2).start)
        self.assertEqual(p(3).start, s(1).start)
        self.assertEqual(p(3).end, s(2).end)
        self.assertEqual(p(3).end, s(1).end)

    def test_calc_2(self):
        """
        В WBS две задачи на одного исполнителя.
        При расчете расписания сначала выполняется первая задача, затем вторая
        """
        p = WBS()
        p // Task(1, estimate=10, resource='default')
        p // Task(2, estimate=16, resource='default')

        s, usage = pl.DefaultScheduler(start=datetime(2025, 1, 1)).calc(p)

        print(usage.usage('default'))

        self.assertEqual(datetime(2025, 1, 1), s(1).start)
        self.assertEqual(datetime(2025, 1, 2, 6), s(1).end)
        self.assertEqual(datetime(2025, 1, 2, 6), s(2).start)
        self.assertEqual(datetime(2025, 1, 6, 6), s(2).end)

    def test_calc_3(self):
        """
        В WBS две задачи. У второй есть дата начала, у первой - нет.
        Исполнение второй прерывается на время, пока делается первая задача
        """
        p = WBS()
        p // Task(1, estimate=8, resource='default')
        p // Task(2, start=datetime(2025, 1, 1), estimate=8, resource='default')

        s, usage = pl.DefaultScheduler(start=datetime(2025, 1, 1)).calc(p)

        self.assertEqual(datetime(2025, 1, 1), s(1).start)
        self.assertEqual(datetime(2025, 1, 2), s(1).end)
        self.assertEqual(datetime(2025, 1, 1), s(2).start)
        self.assertEqual(datetime(2025, 1, 3), s(2).end)

    def test_calc_4(self):
        p = WBS()
        p // Task(1, estimate=8, resource='default')
        p(1) >> p // Task(2, 'ms', milestone=True)

        s, usage = pl.DefaultScheduler(start=datetime(2025, 1, 1)).calc(p)

        self.assertEqual(datetime(2025, 1, 2), s(1).end)
        self.assertEqual(datetime(2025, 1, 2), s(2).start)

    def test_calc_5(self):
        p = WBS()
        p // Task(1, estimate=8, resource='default')
        p // Task(2, estimate=8)

        p(2) >> p(1)

        s, usage = pl.DefaultScheduler(start=datetime(2025, 1, 1)).calc(p)

        self.assertEqual(datetime(2025, 1, 1), s(2).start)
        self.assertEqual(datetime(2025, 1, 2), s(1).start)

    def test_validate_isolation(self):
        p = WBS("test")
        t1 = p // Task(1, '1')

        t1 << Task(2, '2')

        self.assertRaises(RuntimeError, lambda: pl.DefaultScheduler(start=datetime(2022, 1, 1)).calc(p))

    def test_loops(self):
        p = WBS()
        t1 = p // Task(1, '1')
        t2 = p // Task(2, '2')
        t3 = p // Task(3, '3')

        t1.successors.append(t2)
        t2.successors.append(t3)
        t3.successors.append(t1)

        self.assertRaises(RuntimeError, lambda: pl.DefaultScheduler(start=datetime(2022, 1, 1)).calc(p))

    def test_calc_several_projects(self):
        # Есть проект с расписанием
        p1 = WBS("p1")
        t1 = p1 // Task(1, "1", start=datetime(2025, 1, 1), end=datetime(2025, 1, 10))

        # Создаем новый проект, задачи которого зависят от задач первого проекта
        p2 = WBS("p2")
        t2 = p2 // Task(2, "2", estimate=8, spent=8)
        t2.predecessors.append(t1)

        # Строим расписание нового проекта
        s, usage = pl.DefaultScheduler(start=datetime(2025, 1, 1)).calc(p2)

        self.assertEqual(datetime(2025, 1, 10), s(2).start)
