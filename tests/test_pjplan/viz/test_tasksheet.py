import unittest
from datetime import datetime

import pjplan.viz.tasksheet
from pjplan import WBS, Task


class TestTasksheet(unittest.TestCase):

    def test(self):
        p = WBS()
        with p // Task(1, "Task 1") as t1:
            t2 = t1 // Task(2, "Task 2", start=datetime(2022, 1, 1))
            t3 = t1 // Task(3, "Task 3", resource='Tester Test')
            t2.successors.append(t3)

        pjplan.viz.tasksheet.task_sheet(p, fields=['start', 'end', 'resource', 'predecessors'])


    def test1(self):
        l = ["Hello", "World"]
        print("{:10}  {:2}".format(*l))