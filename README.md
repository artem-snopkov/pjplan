# pjplan: Python library for project schedule and analysis

## What is it?

**pjplan** turns your Jupyter Notebook into project management software. 
This Python package gives you a simple API with following possibilities:
- Describe Work Burndown Structure (WBS) of your project
- Assign resources and estimates to tasks
- Link tasks each other as successors/predecessors
- Define work calendars for each resource
- Calculate project schedule in several ways
- Calculate critical path
- Visualize schedule as Gantt diagramm
- Save/Load your projects to csv files

**pjplan** created specially for use inside Jupyter Notebook or similar software, 
but of course in can be used in any other python applications.

## Installation

```bash
pip install pjplan
```

## Getting started

Let's define simple project WBS:
```python
from pjplan import WBS, Task

with WBS() as prj:
  prj // Task(1, 'Task 1', estimate=40, resource='Developer')
  prj // Task(2, 'Task 2', predecessors=[prj[1]], estimate=20, resource='Developer')
  with prj // Task(3, 'Task 3') as t3:
    t3 // Task(4, 'Task 4', predecessors=[prj[2]], estimate=100, resource='Tester')
    t3 // Task(5, 'Task 5', predecessors=[prj[2]], estimate=50, resource='Tester')
```

Let's define resources:
```python
from pjplan import Resource, WeeklyCalendar

work_calendar = WeeklyCalendar(days=[0,1,2,3,4], units_per_day=8)

developer = Resource(name='Developer', calendar=work_calendar)
tester = Resource(name='Tester', calendar=work_calendar)
```

Now we can create schedule for out project:
```python
from datetime import datetime
from pjplan import ForwardScheduler

schedule = ForwardScheduler(
    start=datetime.now(), 
    resources=[developer, tester]
).calc(prj)
```

and visualise it as Mermaid Gantt:
```python
from pjplan import MermaidGantt

MermaidGantt(schedule.schedule)
```
![Иллюстрация к проекту](https://github.com/artem-snopkov/pjplan/raw/master/docs/_static/img/readme/mermaid.png)
## More examples

More examples you can find at [examples](/examples) directory.