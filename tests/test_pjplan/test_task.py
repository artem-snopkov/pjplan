from datetime import datetime
from unittest import TestCase

from pjplan import Task
# noinspection PyProtectedMember
from pjplan.task import _ImmutableTaskList


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

    # noinspection PyPropertyAccess
    def test_set_id(self):
        t = Task(1)
        try:
            t.id = 2
            self.fail("AttributeError expected")
        except AttributeError:
            pass

    def test_set_name(self):
        t = Task(1)
        t.name = "Task 1"

        self.assertEqual("Task 1", t.name)

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

        t.spent = 4
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

    def test_set_parent_not_unique_id(self):
        t1 = Task(1)
        self.assertRaises(RuntimeError, lambda: Task(1, parent=t1))

    def test_parents(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1.children.append(t2)
        t2.children.append(t3)

        self.assertEqual(2, len(t3.all_parents))
        self.assertEqual(2, t3.all_parents[0].id)
        self.assertEqual(1, t3.all_parents[1].id)

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

    def test_all_children(self):
        t1 = Task(id=1, name='1')
        t2 = Task(id=2, name='2')
        t3 = Task(id=3, name='3')
        t1.children.append(t2)
        t2.children.append(t3)

        self.assertEqual(2, len(t1.all_children))
        self.assertEqual(2, t1.all_children[0].id)
        self.assertEqual(3, t1.all_children[1].id)

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

    # noinspection PyTypeChecker
    def test_set_successors_none(self):
        t1 = Task(1, successors=[None])

        self.assertEqual(0, len(t1.successors))

    def test_all_successors(self):
        t1 = Task(id=1)
        t2 = Task(id=2, successors=[t1])
        t3 = Task(id=3, successors=[t2])

        self.assertEqual(2, len(t3.all_successors))
        self.assertEqual(2, t3.all_successors[0].id)
        self.assertEqual(1, t3.all_successors[1].id)

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

    # noinspection PyTypeChecker
    def test_set_predecessors_none(self):
        t1 = Task(1, predecessors=[None])

        self.assertEqual(0, len(t1.successors))

    def test_all_predecessors(self):
        t1 = Task(id=1)
        t2 = Task(id=2, predecessors=[t1])
        t3 = Task(id=3, predecessors=[t2, t1])

        self.assertEqual(2, len(t3.all_predecessors))
        self.assertEqual(2, t3.all_predecessors[0].id)
        self.assertEqual(1, t3.all_predecessors[1].id)


class TaskOperationsTestCase(TestCase):

    def test_clone(self):
        t = Task(id=1, name='2', arg1=1)
        t1 = t.clone()

        self.assertEqual(t.id, t1.id)
        self.assertEqual(t.name, t1.name)

        t1.start = datetime.now()

    def test_to_dict(self):
        t = Task(1, "name")

        d = t.to_dict()

        self.assertEqual(1, d['id'])
        self.assertEqual("name", d['name'])


# noinspection PyUnresolvedReferences
class ImmutableListTestCase(TestCase):

    @staticmethod
    def create_list():
        return _ImmutableTaskList([
            Task(1), Task(2), Task(3), Task(4)
        ])

    def test_get_by_index(self):
        lst = self.create_list()
        self.assertEqual(1, lst[0].id)
        self.assertEqual(2, lst[1].id)
        self.assertEqual(3, lst[2].id)
        self.assertEqual(4, lst[3].id)

    def test_index(self):
        lst = self.create_list()
        self.assertEqual(2, lst.index(lst[2]))

    def test_get_attribute(self):
        lst = _ImmutableTaskList([Task(1, attr=1), Task(2, attr=2)])

        self.assertEqual([1, 2], lst.id)
        self.assertEqual([1, 2], lst.attr)

    def test_set_attribute(self):
        t1 = Task(1)
        t2 = Task(2)

        lst = _ImmutableTaskList([t1, t2])
        lst.attr = 3

        self.assertEqual(3, t1.attr)
        self.assertEqual(3, t2.attr)

    def test_search(self):
        t1 = Task(1)
        t2 = Task(2, resource="R1")
        t3 = Task(3, resource="R2")

        lst = _ImmutableTaskList([t1, t2, t3])

        self.assertEqual([t1], lst(id=1))
        self.assertEqual([t1, t2], lst(id_in_=[1, 2]))
        self.assertEqual([t3], lst(id_not_in_=[1, 2]))
        self.assertEqual([t2, t3], lst(id_gt_=1))
        self.assertEqual([t2, t3], lst(id_ge_=2))
        self.assertEqual([t1, t2], lst(id_lt_=3))
        self.assertEqual([t1, t2], lst(id_le_=2))
        self.assertEqual([t1, t3], lst(id_ne_=2))

        self.assertEqual([t2, t3], lst(resource_like_="R*"))

    def test_search_not_like(self):
        t1 = Task(1)
        t2 = Task(2, name="1 MVP 3123123")
        t3 = Task(3, name="R2")

        lst = _ImmutableTaskList([t1, t2, t3])

        print(lst(name_not_like_="MVP"))

    def test_order_by(self):
        t1 = Task(1)
        t2 = Task(2, resource="R1")
        t3 = Task(3, resource="R1")

        lst = _ImmutableTaskList([t1, t2, t3])

        self.assertEqual([t3, t2, t1], lst.order_by('id', reverse=True))
        self.assertEqual([t2, t3, t1], lst.order_by(['resource'], reverse=True))


class ChildrenListTestCase(TestCase):

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

