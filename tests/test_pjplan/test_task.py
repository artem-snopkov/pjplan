from datetime import datetime
from unittest import TestCase

from pjplan import Task, WBS


class TaskCreateTestCase(TestCase):
    """Test for creation of Task"""

    # noinspection PyUnresolvedReferences
    def test_create(self):
        t = Task(
            id='Some id',
            name='task 1',
            resource='res',
            start=datetime(2023, 1, 1),
            end=datetime(2024, 1, 1),
            milestone=True,
            estimate=8,
            spent=4,
            attr1="attr1",
            attr2=[1],
            attr3=10
        )

        self.assertEqual("Some id", t.id)
        self.assertEqual("task 1", t.name)
        self.assertEqual("res", t.resource)
        self.assertEqual(datetime(2023, 1, 1), t.start)
        self.assertEqual(datetime(2024, 1, 1), t.end)
        self.assertEqual(True, t.milestone)
        self.assertEqual(8, t.estimate)
        self.assertEqual(4, t.spent)
        self.assertEqual("attr1", t.attr1)
        self.assertEqual([1], t.attr2)
        self.assertEqual(10, t.attr3)

    def test_create_parent(self):
        t1 = Task(1)
        t2 = Task(2, parent=t1)

        self.assertEqual(t1, t2.parent)
        self.assertEqual(t2, t1.children[0])

    def test_create_children(self):
        t1 = Task(1)
        t2 = Task(2, children=[t1])

        self.assertEqual(t1, t2.children[0])
        self.assertEqual(t2, t1.parent)

    def test_create_successors(self):
        t1 = Task(1)
        t2 = Task(2, successors=[t1])

        self.assertEqual(t1, t2.successors[0])
        self.assertEqual(t2, t1.predecessors[0])

    def test_create_predecessors(self):
        t1 = Task(1)
        t2 = Task(2, predecessors=[t1])

        self.assertEqual(t1, t2.predecessors[0])
        self.assertEqual(t2, t1.successors[0])

    def test_create_negative_estimate(self):
        self.assertRaises(RuntimeError, lambda: Task(1, estimate=-1))

    def test_create_negative_spent(self):
        self.assertRaises(RuntimeError, lambda: Task(1, spent=-1))

    def test_create_parent_cant_be_successor(self):
        t1 = Task(1)
        t2 = Task(2, parent=t1)
        self.assertRaises(RuntimeError, lambda: Task(3, parent=t2, successors=[t1]))

    def test_create_parent_cant_be_predecessor(self):
        t1 = Task(1)
        t2 = Task(2, parent=t1)
        self.assertRaises(RuntimeError, lambda: Task(3, parent=t2, predecessors=[t1]))

    def test_create_parent_cant_be_child(self):
        t1 = Task(1)
        t2 = Task(2, parent=t1)
        self.assertRaises(RuntimeError, lambda: Task(3, parent=t2, children=[t1]))

    def test_create_unique_id_in_subtree(self):
        t1 = Task(1)
        self.assertRaises(RuntimeError, lambda: Task(1, parent=t1))


class TaskAttributesTestCase(TestCase):
    """Test for task attributes getters/setters"""

    def test_set_id(self):
        t = Task(1)
        try:
            t.id = 2
            self.fail("AttributeError expected")
        except AttributeError:
            pass

    def test_set_estimate(self):
        t = Task(1)

        t.estimate = 8
        self.assertEqual(8, t.estimate)

        try:
            t.estimate = -1
            self.fail("RuntimeError expected")
        except RuntimeError:
            pass

    def test_set_spent(self):
        t = Task(1)

        t.spent=4
        self.assertEqual(4, t.spent)

        try:
            t.spent = -1
            self.fail("RuntimeError expected")
        except RuntimeError:
            pass

    def test_set_parent(self):
        t1 = Task(1)
        t2 = Task(2)

        t2.parent = t1

        self.assertEqual(t1, t2.parent)
        self.assertEqual(t2, t1.children[0])

    def test_set_parent_none(self):
        t1 = Task(1)
        t2 = Task(2, parent=t1)

        t2.parent = None

        self.assertIsNone(t2.parent)
        self.assertEqual(0, len(t1.children))

    def test_set_children(self):
        t1 = Task(1)
        t2 = Task(2)
        t3 = Task(3)

        t1.children += [t2, t3]

        self.assertEqual(t1, t2.parent)
        self.assertEqual(t1, t3.parent)
        self.assertEqual(t2, t1.children[0])
        self.assertEqual(t3, t1.children[1])

    def test_set_children_none(self):
        t1 = Task(1)

        t1.children = None

        self.assertEqual(0, len(t1.children))

    def test_set_children_none_in_list(self):
        t1 = Task(1)

        t1.children = [None]

        self.assertEqual(0, len(t1.children))

    def test_set_children_append(self):
        t1 = Task(1)
        t2 = Task(2)

        t1.children.append(t2)

        self.assertEqual(t1, t2.parent)
        self.assertEqual(t2, t1.children[0])

    def test_set_children_floordiv(self):
        t1 = Task(1)
        t2 = Task(2)

        t1 // t2

        self.assertEqual(t1, t2.parent)
        self.assertEqual(t2, t1.children[0])

    def test_set_children_not_unique_id(self):
        t1 = Task(1)
        t2 = Task(2)
        t2_ = Task(2)

        try:
            t1.children += [t2, t2_]
            self.fail("RuntimeError expected")
        except RuntimeError:
            pass

    def test_set_successors(self):
        t1 = Task(1)
        t2 = Task(2)

        t1.successors = [t2]

        self.assertEqual(t2, t1.successors[0])
        self.assertEqual(t1, t2.predecessors[0])

    def test_set_successors_append(self):
        t1 = Task(1)
        t2 = Task(2)

        t1.successors.append(t2)

        self.assertEqual(t2, t1.successors[0])
        self.assertEqual(t1, t2.predecessors[0])

    def test_set_successors_rshift(self):
        t1 = Task(1)
        t2 = Task(2)

        t1 >> t2

        self.assertEqual(t2, t1.successors[0])
        self.assertEqual(t1, t2.predecessors[0])

    def test_set_predecessors(self):
        t1 = Task(1)
        t2 = Task(2)

        t1.predecessors = [t2]

        self.assertEqual(t2, t1.predecessors[0])
        self.assertEqual(t1, t2.successors[0])

    def test_set_predecessors_append(self):
        t1 = Task(1)
        t2 = Task(2)

        t1.predecessors.append(t2)

        self.assertEqual(t2, t1.predecessors[0])
        self.assertEqual(t1, t2.successors[0])

    def test_set_predecessors_lshift(self):
        t1 = Task(1)
        t2 = Task(2)

        t1 << t2

        self.assertEqual(t2, t1.predecessors[0])
        self.assertEqual(t1, t2.successors[0])


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
        self.assertEqual(2, t1.all_children[0].id)
        self.assertEqual(3, t1.all_children[1].id)

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
        self.assertEqual(2, t4.predecessors[0].id)
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
        self.assertEqual(2, t4.all_predecessors[1].id)

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

    def test_to_dict(self):
        t = Task(1, "name")

        d = t.to_dict()

        self.assertEqual(1, d['id'])
        self.assertEqual("name", d['name'])
