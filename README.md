# pjplan: Python library for project planning and analysis

## What is it?

**pjplan** turns your [Jupyter Notebook](https://jupyter.org/) into project management software. 
This Python package gives you a simple API with following features:
- Describe Work Burn-down Structure (WBS) of your project in code or load it from external source.
- Manipulate tasks: link them as successors/predecessors, find, delete, reorder, etc. A lot of batch operations are supported via simple commands.
- Assign resources and estimates to tasks
- Define work calendars for each resource
- Calculate project schedule in several ways
- Find critical path
- Visualize WBS as Gantt or Network diagram
- Save/Load your WBS to/from csv files
- Export WBS to [pandas](https://pandas.pydata.org/)

## Why to use it?
There are several use cases for pjplan:
- Work with project plan as code with your favourite IDE, VSC, etc.
- Load tasks data from your tracker (Jira, Asure Devops, Trello, etc.) to pjplan, 
link/modify/reorder/delete tasks using rich pjplan API, then create schedule and Gantt for them.
- Create several schedules for same project and find optimal one.

## Where to use it?

**pjplan** created specially for use inside [Jupyter Notebook](https://jupyter.org/) 
or similar software. All library objects (WBS, Task, Schedule, Calendar) have great visualisations 
so you can easily work with them in notebooks. 

But, of course, you can use pjplan in any other python applications.

## Installation

```bash
pip install pjplan
```

## Getting started

Let's define simple project WBS:

```python
from pjplan import WBS, Task

with WBS() as prj:
    prj // Task(1, 'Task 1', estimate=40, resource_name='Developer')
    prj // Task(2, 'Task 2', predecessors=[prj[1]], estimate=20, resource_name='Developer')
    with prj // Task(3, 'Task 3') as t3:
        t3 // Task(4, 'Task 4', predecessors=[prj[2]], estimate=100, resource_name='Tester')
        t3 // Task(5, 'Task 5', predecessors=[prj[2]], estimate=50, resource_name='Tester')
```

Let's define resources:
```python
from pjplan import Resource, WeeklyCalendar

work_calendar = WeeklyCalendar(days=[0,1,2,3,4], units_per_day=8)

developer = Resource(name='Developer', calendar=work_calendar)
tester = Resource(name='Tester', calendar=work_calendar)
```

Now we can create schedule for our project:
```python
from datetime import datetime
from pjplan import ForwardScheduler

schedule = ForwardScheduler(
    start=datetime.now(), 
    resources=[developer, tester]
).calc(prj)
```

visualise it as [Mermaid](https://mermaid.js.org/) Gantt:
```python
from pjplan import MermaidGantt

MermaidGantt(schedule.schedule)
```
![Mermaid Gantt](https://raw.githubusercontent.com/artem-snopkov/pjplan/main/docs/_static/img/readme/mermaid_gantt.png)

or Network:
```python
from pjplan import MermaidNetwork

MermaidNetwork(schedule.schedule)
```
![Mermaid Network](https://raw.githubusercontent.com/artem-snopkov/pjplan/main/docs/_static/img/readme/mermaid_network.png)

save schedule to csv:
```python
from pjplan import write_csv

write_csv(schedule.schedule, "schedule.csv")
```

## More examples

More examples you can find at [examples](https://github.com/artem-snopkov/pjplan/tree/main/examples) directory.