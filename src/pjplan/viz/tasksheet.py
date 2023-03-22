from datetime import datetime
from typing import Iterable, List

from pjplan import Task, WBS

__bold = '\033[1m'
__red = '\033[91m'
__green = '\033[92m'
__yellow = '\033[93m'
__blue = '\033[94m'
__pink = '\033[95m'
__teal = '\033[96m'
__grey = '\033[97m'

__LEVEL_COLORS = [__blue, __teal, __yellow, __pink, __red, __grey]


def __calc_max_title_len(task: Task, level, _current_max):
    _current_max = max(_current_max, len('   ' * level) + len(task.name))
    for ch in task.children:
        _current_max = __calc_max_title_len(ch, level + 1, _current_max)
    return _current_max


def __get_field_value(t: Task, field: str) -> str:
    if field == 'predecessors':
        return '[' + ','.join([str(p.id) for p in t.predecessors]) + ']'
    if field == 'successors':
        return '[' + ','.join([str(p.id) for p in t.successors]) + ']'
    if field == 'parent':
        return str(t.parent.id) if t.parent else ''

    if field not in t.__dict__:
        return ''

    v = t.__getattribute__(field)
    if isinstance(v, datetime):
        return v.strftime('%d.%m.%Y %H:%M')

    if v is None:
        return '-'

    return str(v)


def __max_field_len(tasks: Iterable[Task], field: str) -> int:
    max_len = len(field) + 1
    for t in tasks:
        max_len = max(max_len, len(__get_field_value(t, field)))
        max_len = max(max_len, __max_field_len(t.children, field))

    return max_len


def __print_task_subtree(task: Task, fields: List[str], level, fmt):
    values = [task.id, '   ' * level + task.name]
    for f in fields:
        values.append(__get_field_value(task, f))

    print(__LEVEL_COLORS[level] + fmt.format(*values) + '\033[0m')
    for ch in task.children:
        __print_task_subtree(ch, fields, level + 1, fmt)


def task_sheet(project: WBS, root_id=None, fields=None):
    if root_id is not None:
        tasks = [project(root_id)]
    else:
        tasks = project.roots

    if fields is None:
        fields = ['start', 'end', 'predecessors']

    max_title_len = 0
    for _t in tasks:
        max_title_len = max(max_title_len, __calc_max_title_len(_t, 0, 0))

    fmt = f"{{:6}} {{:{max_title_len}}}"
    for f in fields:
        fmt += f"  {{:{__max_field_len(tasks, f)}}}"

    title = ["ID", "NAME"] + [s.upper() for s in fields]
    print(__green + fmt.format(*title) + '\033[0m')

    for _task in tasks:
        __print_task_subtree(_task, fields, 0, fmt)