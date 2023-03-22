from datetime import datetime
from typing import List, Callable
from pjplan import Task, WBS


def __mermaid_task_state(task: Task):
    now = datetime.now()
    if task.milestone:
        return 'milestone,'
    if task.end <= now:
        return 'done,'
    if task.start < now:
        return 'active,'
    return ''


def mermaid_gantt(
        project: WBS,
        title: str = None,
        root_ids=None,
        subtree=False,
        sections: List[tuple] = None,
        weekends=False,
        tick_interval: str = None,
        task_styles: Callable[[Task], dict] = None,
        text_styles: Callable[[Task], dict] = None
):
    res = "gantt\n"
    res += "  dateFormat DD.MM.YYYY\n"
    if title is not None:
        res += "  title {}\n".format(title)
    if weekends:
        res += "  excludes weekends\n"
    if tick_interval:
        res += "  tickInterval {}\n".format(tick_interval)

    if root_ids is None:
        roots = project.roots
    else:
        if type(root_ids) is int:
            root_ids = [root_ids]
        roots = [project[root_id] for root_id in root_ids]

    if sections:
        sections_list = [(s, []) for s in sections] + [(('Other', lambda x: True), [])]

        for task in roots:
            for s in sections_list:
                if s[0][1](task):
                    s[1].append(task)
                    if subtree:
                        for subtask in task.all_children:
                            s[1].append(subtask)
                    break

        for s in sections_list:
            res += "  section {}\n".format(s[0][0])
            for t in s[1]:
                res += "    {}: {} {}, {}, {}\n".format(
                    t.name.replace(':', ''),
                    __mermaid_task_state(t),
                    'id_' + str(t.id),
                    t.start.strftime('%d.%m.%Y'),
                    t.end.strftime('%d.%m.%Y')
                )

    else:
        for t in roots:
            res += "  {}: {} {}, {}, {}\n".format(
                t.name.replace(':', ''),
                __mermaid_task_state(t),
                'id_' + str(t.id),
                t.start.strftime('%d.%m.%Y'),
                t.end.strftime('%d.%m.%Y')
            )
        res += '\n'

    if task_styles or text_styles:
        res += '-styles-\n'

        lst = roots
        for t in lst:
            if task_styles:
                t_style = task_styles(t)
                if t_style:
                    res += '#id_' + str(t.id) + str(t_style).replace(',', ';') + '\n'
            if text_styles:
                t_style = text_styles(t)
                if t_style:
                    res += '#id_' + str(t.id) + '-text' + str(t_style).replace(',', ';') + '\n'

    return res


def mermaid_network_diagram(
        project: WBS,
        root_id=None,
        done_task_style=None,
        inprogress_task_style=None
):
    if root_id is None:
        roots = project.roots
    else:
        roots = [project[root_id]]

    res = "flowchart LR\n"
    for t in roots:
        if len(t.predecessors) == 0:
            res += "  0(('')) --> {}{{{{'{}'}}}}\n".format(str(t.id), str(t.name).replace('"', ''))
        else:
            for p in t.predecessors:
                res += "  {}{{{{'{}'}}}} --> {}{{{{'{}'}}}}\n".format(str(p.id), str(p.name).replace('"', ''),
                                                                      str(t.id), str(t.name).replace('"', ''))

    now = datetime.now()
    for t in roots:
        if done_task_style and t.end is not None and t.end <= now:
            res += "style {} fill:#A1FB8E,stroke:#333,stroke-width:4px\n".format(str(t.id))
        elif inprogress_task_style and t.start is not None and t.start < now:
            res += "style {} fill:#FFFE91,stroke:#333,stroke-width:4px\n".format(str(t.id))

    return res