from datetime import datetime
from unittest import TestCase

from pjplan import Task, WBS


class TestTask(TestCase):

    def test_clone(self):
        t = Task(id=1, name='2', arg1=1)
        t1 = t.clone()

        self.assertEqual(t.id, t1.id)
        self.assertEqual(t.name, t1.name)

        t1.start = datetime.now()

    def test_parent_in_init(self):
        """При указании parent в конструкторе у него автоматом проставляются children"""
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2', parent=t1)

        self.assertEqual(1, t2.parent.id)
        self.assertEqual(1, len(t1.children))
        self.assertEqual(2, t1.children[0].id)

    def test_parent_children(self):
        """При назначении parent автоматически заполняется children"""
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')

        t2.parent = t1

        self.assertEqual(1, len(t1.children))
        self.assertEqual(2, t1.children[0].id)

        t2.parent = t3
        self.assertEqual(0, len(t1.children))
        self.assertEqual(1, len(t3.children))
        self.assertEqual(2, t3.children[0].id)

    def test_children_parent(self):
        """При добавлении в children автоматически заполняется parent"""
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1.children.append(t2)
        t1.children += [t3]

        self.assertEqual(1, t3.parent.id)
        self.assertEqual(1, t2.parent.id)

        t1.children.remove(t3)

        self.assertIsNone(t3.parent)

        self.assertEqual(1, len(t1.children))

        t3.children = [t2]

        self.assertEqual(t3, t2.parent)
        self.assertEqual(0, len(t1.children))

    def test_children_init(self):
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1 = Task(id=1, name='1', children=[t2, t3])

        self.assertEqual(2, len(t1.children))
        self.assertEqual(t1.id, t2.parent.id)
        self.assertEqual(t1, t3.parent)

    def test_children_index(self):
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1 = Task(id=1, name='1', children=[t2, t3])

        self.assertEqual(1, t1.children.index(t3))

    def test_children_set(self):
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1 = Task(id=1, name='1', children=[t2, t3])

        t1.children = [t2]

        self.assertIsNone(t3.parent)

    def test_children_set_duplicate_ids(self):
        t2 = Task(2)
        t3 = Task(2)

        try:
            Task(1, children=[t2, t3])
            self.fail("RuntimeError expected")
        except RuntimeError:
            pass

    def test_parents(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1.children.append(t2)
        t2.children.append(t3)

        self.assertEqual(2, len(t3.all_parents))
        self.assertEqual(2, t3.all_parents[0].id)
        self.assertEqual(1, t3.all_parents[1].id)

    def test_parents_add_remove(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t1.children.append(t2)

    def test_children(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1.children.append(t2)
        t1.children.append(t3)

        # Поиск по индексу
        self.assertEqual(2, len(t1.children))
        self.assertEqual(2, t1.children[0].id)
        self.assertEqual(3, t1.children[1].id)

        # Поиск по айди
        v = t1.children(2)
        self.assertEqual(2, v.id)

        # Поиск по нескольким айди
        v2, v3 = t1.children(id_in_=[2, 3])
        self.assertEqual(2, v2.id)
        self.assertEqual(3, v3.id)

        # Поиск по лямбде
        v4 = t1.children(lambda t: t.name == '3')
        self.assertEqual(3, v4[0].id)

    def test_children_set_parent(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t4 = Task(id=4, name='4')
        t1.children.append(t2)
        t1.children.append(t3)

        t1.children(id_in_=[2, 3]).parent = t4

        self.assertEqual(2, len(t4.children))

    def test_children_sort(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1.children.append(t3)
        t1.children.append(t2)

        self.assertEqual(3, t1.children[0].id)
        self.assertEqual(2, t1.children[1].id)

        t1.children.sort("name")

        self.assertEqual(2, t1.children[0].id)
        self.assertEqual(3, t1.children[1].id)

    def test_children_reorder(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1.children.append(t3)
        t1.children.append(t2)

        self.assertEqual(3, t1.children[0].id)
        self.assertEqual(2, t1.children[1].id)

        t1.children.reorder([2, 3])

        self.assertEqual(2, t1.children[0].id)
        self.assertEqual(3, t1.children[1].id)

    def test_all_children(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1.children.append(t2)
        t2.children.append(t3)

        self.assertEqual(1, len(t1.children))
        self.assertEqual(2, len(t1.all_children))
        self.assertEqual(3, t1.all_children(3).id)

    def test_predecessors(self):
        with WBS() as wbs:
            t1 = wbs // Task(id=1, name='1')
            t2 = wbs // Task(id=2, name='2')
            t3 = wbs // Task(id=3, name='3')
            t4 = wbs // Task(id=4, name='4')
        t1.children.append(t2)
        t1.children.append(t3)
        t1.children.append(t4)
        t4.predecessors += [t2, t3]

        self.assertEqual(2, len(t4.predecessors))
        self.assertEqual(2, t4.predecessors(2).id)
        self.assertEqual(t4, t2.successors[0])
        self.assertEqual(t4, t3.successors[0])

        t4.predecessors.remove(t2)
        self.assertEqual(1, len(t4.predecessors))
        self.assertTrue(t4 not in t2.successors)

    def test_predecessors_set(self):
        with WBS() as wbs:
            t1 = wbs // Task(id=1, name='1')
            t2 = wbs // Task(id=2, name='2')

        t2.predecessors = [t1]

        self.assertEqual(t2, t1.successors[0])

        t2.predecessors = []

        self.assertEqual(0, len(t1.successors))

    def test_predecessors_cyclic(self):
        t1 = Task(1)
        t2 = Task(2, predecessors=[t1])

        try:
            t1.predecessors = t2
            self.fail("FuntimeError expected")
        except RuntimeError:
            pass

    def test_successors_cyclic(self):
        t1 = Task(1)
        t2 = Task(2, successors=[t1])

        try:
            t1.successors = [t2]
            self.fail("FuntimeError expected")
        except RuntimeError:
            pass

    def test_all_predecessors(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t4 = Task(id=4, name='4')

        t1 // t2
        t1 // t3
        t1 // t4
        t4 << t3
        t3 << t2

        self.assertEqual(1, len(t4.predecessors))
        self.assertEqual(3, t4.predecessors[0].id)

        self.assertEqual(2, len(t4.all_predecessors))
        self.assertEqual(2, t4.all_predecessors(2).id)

    def test_lshift(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')

        t1 << t2

        self.assertEqual(t2, t1.predecessors[0])

    def test_rshift(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')

        t1 >> t2

        self.assertEqual(t2, t1.successors[0])

    def test_floordiv(self):
        root = Task(1, '1')
        root // Task(2, '2') // Task(3, '3')

        with Task(4, '4') as t:
            with t // Task(5, '5') as t5:
                t5 // Task(6, '6')
                t5 // Task(7, '7')

        self.assertEqual(2, root.children[0].id)
        self.assertEqual(3, root.children[0].children[0].id)
