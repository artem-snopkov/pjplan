# pjplan: Python library for project planning and analysis
=============================

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

## Getting started

```{toctree}
---
caption: Following articles will help you to install pjplan and help you to understant it's concepts
maxdepth: 1
---

installation
getting-started/getting-started