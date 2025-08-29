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

### Simple Task Creation

For simpler projects, you can create tasks directly without the WBS context manager:

```python
import pjplan

# Create tasks with dependencies
kickoff = pjplan.Task("A", name="Kickoff", estimate=2)
requirements = pjplan.Task("B", name="Requirements", estimate=5, predecessors=[kickoff])
design = pjplan.Task("C", name="Design", estimate=6, predecessors=[requirements])

# Schedule the tasks
wbs = pjplan.WBS([kickoff, requirements, design])
scheduler = pjplan.ForwardScheduler()
schedule = scheduler.calc(wbs)
```

### Export to JSON

Export your project schedule to JSON format for integration with other tools:

```python
import json
import pjplan

# Create a simple project
tasks = []
tasks.append(pjplan.Task("PROJ-1", name="Project Setup", estimate=3))
tasks.append(pjplan.Task("PROJ-2", name="Development", estimate=10, predecessors=[tasks[0]]))
tasks.append(pjplan.Task("PROJ-3", name="Testing", estimate=5, predecessors=[tasks[1]]))
tasks.append(pjplan.Task("PROJ-4", name="Deployment", estimate=2, predecessors=[tasks[2]]))

# Schedule and export
wbs = pjplan.WBS(tasks)
scheduler = pjplan.ForwardScheduler()
schedule = scheduler.calc(wbs)

# Export to JSON
task_data = []
for task in schedule.schedule.tasks:
    task_dict = {
        "id": task.id,
        "name": task.name,
        "estimate": getattr(task, 'estimate', None),
        "start": str(getattr(task, 'start', None)).split(' ')[0] if getattr(task, 'start', None) else None,
        "end": str(getattr(task, 'end', None)).split(' ')[0] if getattr(task, 'end', None) else None
    }
    task_data.append(task_dict)

project_json = {"project_name": "Sample Project", "tasks": task_data}
print(json.dumps(project_json, indent=2))
```

### Critical Path Analysis

Identify the critical path in your project to understand which tasks drive the overall timeline:

```python
import pjplan

# Create a project with parallel paths
task_a = pjplan.Task("A", name="Requirements", estimate=5)
task_b = pjplan.Task("B", name="UI Design", estimate=8, predecessors=[task_a])
task_c = pjplan.Task("C", name="Backend API", estimate=12, predecessors=[task_a])  # Longer path
task_d = pjplan.Task("D", name="Integration", estimate=4, predecessors=[task_b, task_c])
task_e = pjplan.Task("E", name="Testing", estimate=6, predecessors=[task_d])

# Schedule the project
wbs = pjplan.WBS([task_a, task_b, task_c, task_d, task_e])
scheduler = pjplan.ForwardScheduler()
schedule = scheduler.calc(wbs)

# Find critical path
critical_path = schedule.schedule.critical_path()
critical_task_ids = [task.id for task in critical_path] if critical_path else []
print(f"Critical path: {critical_task_ids}")

# Show critical status for all tasks
for task in schedule.schedule.tasks:
    is_critical = task in critical_path if critical_path else False
    status = "CRITICAL" if is_critical else "non-critical"
    print(f"Task {task.id} ({task.name}): {status}")
```

### Resource-Constrained Scheduling

Schedule tasks with different resource calendars and constraints:

```python
from datetime import datetime
import pjplan

# Create resources with different working schedules
full_time_calendar = pjplan.WeeklyCalendar(days=[0,1,2,3,4], units_per_day=8)  # Mon-Fri, 8 hours
part_time_calendar = pjplan.WeeklyCalendar(days=[0,2,4], units_per_day=4)       # Mon,Wed,Fri, 4 hours

developer = pjplan.Resource(name='Developer', calendar=full_time_calendar)
consultant = pjplan.Resource(name='Consultant', calendar=part_time_calendar)

# Create project with resource assignments
with pjplan.WBS() as project:
    project // pjplan.Task("T1", name="Analysis", estimate=16, resource_name='Developer')
    project // pjplan.Task("T2", name="Design", estimate=24, resource_name='Developer', predecessors=[project["T1"]])
    project // pjplan.Task("T3", name="Review", estimate=8, resource_name='Consultant', predecessors=[project["T2"]])
    project // pjplan.Task("T4", name="Implementation", estimate=40, resource_name='Developer', predecessors=[project["T3"]])

# Schedule with resource constraints
scheduler = pjplan.ForwardScheduler(
    start=datetime(2025, 9, 1),
    resources=[developer, consultant]
)
schedule = scheduler.calc(project)

# Display schedule
for task in schedule.schedule.tasks:
    resource = getattr(task, 'resource', 'Unassigned')
    start_date = getattr(task, 'start', None)
    end_date = getattr(task, 'end', None)
    if start_date and end_date:
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        print(f"{task.id}: {task.name} ({resource}) - {start_str} to {end_str}")
```

### Working with Milestones

Track important project milestones and deliverables:

```python
from datetime import datetime
import pjplan

# Create project phases with milestones
phase1_tasks = [
    pjplan.Task("P1T1", name="Requirements Gathering", estimate=8),
    pjplan.Task("P1T2", name="Stakeholder Approval", estimate=0, milestone=True),  # Milestone
]
phase1_tasks[1].predecessors = [phase1_tasks[0]]

phase2_tasks = [
    pjplan.Task("P2T1", name="System Design", estimate=16, predecessors=[phase1_tasks[1]]),
    pjplan.Task("P2T2", name="Design Review", estimate=0, milestone=True),  # Milestone
]
phase2_tasks[1].predecessors = [phase2_tasks[0]]

phase3_tasks = [
    pjplan.Task("P3T1", name="Development", estimate=32, predecessors=[phase2_tasks[1]]),
    pjplan.Task("P3T2", name="Code Complete", estimate=0, milestone=True),  # Milestone
]
phase3_tasks[1].predecessors = [phase3_tasks[0]]

# Schedule the complete project
all_tasks = phase1_tasks + phase2_tasks + phase3_tasks
wbs = pjplan.WBS(all_tasks)
scheduler = pjplan.ForwardScheduler(start=datetime(2025, 9, 1))
schedule = scheduler.calc(wbs)

# Show milestone dates
milestones = [task for task in schedule.schedule.tasks if getattr(task, 'milestone', False)]
print("Project Milestones:")
for milestone in milestones:
    date = getattr(milestone, 'start', None)
    date_str = date.strftime('%Y-%m-%d') if date else 'Not scheduled'
    print(f"  {milestone.name}: {date_str}")
```

## Additional Resources

More examples you can find at [examples](https://github.com/artem-snopkov/pjplan/tree/main/examples) directory.