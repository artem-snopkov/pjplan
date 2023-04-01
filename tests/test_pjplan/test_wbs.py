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
        prj = WBS()
        with prj // Task(1, "1") as first:
            with first // Task(2, "2", start=datetime.now(), end=datetime(2022, 11, 1)) as second:
                second // Task(3, "3", start=datetime(2022, 11, 1), end=datetime(2022, 12, 1), resource='Test')

        prj2 = prj.clone()
        prj2(1).name = 'n1'

        self.assertEqual('1', prj(1).name)
        self.assertEqual(1, len(prj2.roots))
        self.assertEqual(len(prj), len(prj2))
        self.assertIsNotNone(prj2(1))
        self.assertIsNotNone(prj2(2))
        self.assertIsNotNone(prj2(3))

    def test_append(self):
        prj = WBS()
        prj // Task(1)

        self.assertEqual(1, len(prj))

    def test_append_duplicate_id(self):
        prj = WBS()
        prj // Task(1)
        self.assertEqual(1, len(prj))
        self.assertRaises(RuntimeError, lambda: prj // Task(1))

    def test_append_duplicate_ids(self):
        prj = WBS()
        self.assertRaises(RuntimeError, lambda: prj // [Task(1), Task(1)])

    def test_insert(self):
        prj = WBS()
        prj // Task(1, '1')
        prj // Task(2, '2')

        prj.roots.insert(0, Task(3, '3'))

        self.assertEqual(3, prj.roots[0].id)
        self.assertEqual(1, prj.roots[1].id)
        self.assertEqual(2, prj.roots[2].id)
        self.assertEqual(3, len(prj.roots))

    def test_set_children_make_child_a_parent_of_its_parent(self):
        with WBS() as wbs:
            with wbs // Task(1) as t1:
                t2 = t1 // Task(2)

        try:
            t2.children = [t1]
            self.fail("RuntimeError expected. Can't make child a parent of its parent")
        except RuntimeError:
            pass

    def test_set_children_hidden_remove_1(self):
        prj = WBS()
        prj // Task(1)
        prj // Task(2)

        prj.roots = [prj(1)]

        self.assertEqual(1, len(prj))
        self.assertEqual(1, prj[0].id)

    def test_children_set_parent(self):
        with WBS() as prj:
            with prj // Task(1) as t1:
                t1 // Task(2)
                with t1 // Task(3) as t3:
                    t3 // Task(4)
                    t3 // Task(5)

        prj.roots[0].children.parent = None
        self.assertIsNone(prj(1).parent)
        self.assertIsNone(prj(2).parent)
        self.assertIsNone(prj(3).parent)

    def test_set_parent_none(self):
        prj = WBS()
        t1 = prj // Task(1)
        t2 = t1 // Task(2)

        self.assertEqual(1, len(prj.roots))

        t2.parent = None
        self.assertEqual(2, len(prj.roots))

    def test_set_parent(self):
        wbs = WBS()
        t1 = wbs // Task(1)

        Task(2).parent = t1

        self.assertEqual(2, len(wbs))
        self.assertEqual(2, wbs(2).id)

    def test_set_parent_from_children(self):
        with WBS() as wbs:
            with wbs // Task(1) as t1:
                t2 = t1 // Task(2)

        try:
            t1.parent = t2
            self.fail("RuntimeError expected. Can't set child a parent of int parent")
        except RuntimeError:
            pass

    def test_set_parent_outside_wbs(self):
        wbs1 = WBS()
        t1 = wbs1 // Task(1)

        wbs2 = WBS()
        t2 = wbs2 // Task(2)

        try:
            t2.parent = t1
            self.fail("RuntimeError expected")
        except RuntimeError:
            pass

    def test_set_parent_duplicate_id(self):
        wbs = WBS()
        t1 = wbs // Task(1)

        t2 = Task(1)

        try:
            t2.parent = t1
            self.fail("RuntimeError expected")
        except RuntimeError:
            pass

    def test_move_before(self):
        prj = WBS()
        prj // Task(1, '1')
        prj // Task(2, '2')

        prj.roots.move(prj(2), before=prj(1))
        self.assertEqual(2, prj.roots[0].id)
        self.assertEqual(1, prj.roots[1].id)
        self.assertEqual(2, len(prj.roots))

    def test_move_after(self):
        prj = WBS()
        prj // Task(1, '1')
        prj // Task(2, '2')

        prj.roots.move(prj(1), after=prj(2))
        self.assertEqual(2, prj.roots[0].id)
        self.assertEqual(1, prj.roots[1].id)
        self.assertEqual(2, len(prj.roots))

    def test_remove(self):
        prj = WBS()
        prj // Task(1, '1')
        prj // Task(2, '2')

        self.assertTrue(prj.remove(prj(2)))
        self.assertEqual(1, len(prj))

    def test_detached_2(self):
        with WBS() as prj0:
            t1 = prj0 // Task(2)

        # Detached task
        t2 = Task(1, predecessors=[t1])

        self.assertEqual(1, len(t2.predecessors))

        # Attach task
        prj0 // t2

        self.assertEqual(1, len(t2.predecessors))
        self.assertEqual(1, len(t1.successors))

    def test_detached_3(self):
        with WBS() as prj0:
            t1 = prj0 // Task(2)

        try:
            t1.parent = Task(1)
            self.fail()
        except RuntimeError:
            pass

    def test_detached_6(self):
        t1 = Task(1)
        t1 // Task(2)

        wbs = WBS()
        wbs.append(t1)

        self.assertEqual(1, len(wbs.roots))
        self.assertEqual(2, len(wbs))
        self.assertEqual(1, wbs(2).parent.id)

    def test_detached_7(self):
        t1 = WBS() // Task(1)

        self.assertRaises(RuntimeError, lambda: WBS().append(t1))

    def test_subtree(self):
        with WBS() as wbs:
            wbs // Task(1)
            with wbs // Task(2) as t2:
                t3 = t2 // Task(3)
                t4 = t2 // Task(4)
            with wbs // Task(5) as t5:
                t6 = t5 // Task(6, predecessors=[t3])
                t5 // Task(7, predecessors=[t6])

        subtree = wbs.subtree(wbs(id_in_=[2, 5]))

        self.assertEqual(6, len(subtree))

        self.assertEqual(subtree, subtree(2).wbs)
        self.assertEqual(subtree, subtree(3).wbs)
        self.assertEqual(subtree, subtree(4).wbs)
        self.assertEqual(subtree, subtree(5).wbs)
        self.assertEqual(subtree, subtree(6).wbs)
        self.assertEqual(subtree, subtree(7).wbs)

        self.assertEqual(subtree(3), subtree(6).predecessors[0])
        self.assertEqual(subtree(6), subtree(7).predecessors[0])

        self.assertEqual(subtree, subtree(6).predecessors[0].wbs)
        self.assertEqual(subtree, subtree(7).predecessors[0].wbs)


