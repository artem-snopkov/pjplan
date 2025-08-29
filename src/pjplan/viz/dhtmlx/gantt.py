import importlib.resources as pkg_resources
import json
from dataclasses import dataclass
from datetime import datetime
from html import escape
from string import Template
from typing import Tuple

from pjplan import WBS


@dataclass
class DhtmlxGanttColumn:
    field: str
    width: int
    label: str = None
    tree: bool = False


class DhtmlxGantt:

    def __init__(
            self,
            wbs: WBS,
            height=300,
            row_height=25,
            today_marker=True,
            columns=None,
            scale: str = "day"
    ):
        self.wbs = wbs
        self.height = height
        self.row_height = row_height
        self.today_marker = today_marker
        self.columns = columns
        self.scale = scale

    @staticmethod
    def __js(val):
        if type(val) is bool:
            return str(val).lower()
        if type(val) is str:
            return f'"{val}"'
        return str(val)

    @staticmethod
    def __map_column_name(name: str) -> str:
        name = name.lower()
        if name == 'name':
            return 'text'
        if name == 'start':
            return 'start_date'
        if name == 'end':
            return 'end_date'
        return name

    def __columns(self):
        if self.columns is None:
            return '[]'

        res = []
        for c in self.columns:
            d = {
                'name': self.__map_column_name(c.field),
                'tree': c.tree,
                'width': c.width,
                'resize': True
            }
            if c.label:
                d['label'] = c.label
            res.append(d)
        return json.dumps(res, ensure_ascii=False).replace('True', 'true').replace('False', 'false')

    def __task_classes(self) -> Tuple[str, dict]:

        bar_styles = {}
        for t in self.wbs.tasks:
            if 'gantt_bar_style' in t.__dict__:
                bar_styles.setdefault(str(t.gantt_bar_style), (t.gantt_bar_style, []))[1].append(t.id)

        res = ''

        task_classes = {}
        idx = 0
        for v in bar_styles.values():
            style_dict, task_ids = v
            css_class_name = f'dhtmlx_bar_{idx}'

            for tid in task_ids:
                task_classes[tid] = css_class_name

            bar_css = '{'
            for k, s in style_dict.items():
                if k == 'progress':
                    continue
                bar_css += f'{k}:{s}!important;'
            bar_css += '}\n'

            res += '.' + css_class_name + bar_css

            if 'progress' in style_dict:
                progress_css = '{'
                for k, s in style_dict['progress'].items():
                    progress_css += f'{k}:{s}!important;'
                progress_css += '}\n'

                res += '.' + css_class_name + ' .gantt_task_progress' + progress_css

            idx += 1

        return res, task_classes

    def __data(self, task_classes: dict[int, str]):

        data = []
        links = []

        link_id = 0
        for _root in self.wbs.roots:
            for t in _root.all_children + [_root]:

                progress = 0
                if t.end < datetime.now():
                    progress = 1
                elif t.estimate > 0 and t.spent is not None:
                    progress = 1 - (max(t.estimate - t.spent, 0))/t.estimate

                data_val = {
                    'id': t.id,
                    'text': t.name,
                    'type': 'milestone' if t.milestone else 'task',
                    'start_date': t.start.strftime("%d-%m-%Y %H:%M"),
                    'end_date': t.end.strftime("%d-%m-%Y %H:%M"),
                    'resource': t.resource,
                    'estimate': t.estimate,
                    'spent': t.spent,
                    'open': t.gantt_open if 'gantt_open' in t.__dict__ else 'true',
                    'parent': t.parent.id if t.parent and t.parent in self.wbs.tasks else 0,
                    'progress': progress,
                    'css_class': task_classes.get(t.id)
                }

                for k, v in t.__dict__.items():
                    if k not in data_val and not k.startswith('_Task'):
                        data_val[k] = str(v)

                data.append(data_val)

                for p in t.predecessors:
                    link_id += 1
                    links.append({
                        'id': link_id,
                        'source': p.id,
                        'target': t.id,
                        'type': "0"
                    })

        return json.dumps(
            {
                "data": data,
                "links": links
            },
            ensure_ascii=False,
            indent=2
        )

    def to_html(self):

        template = pkg_resources.read_text('pjplan.viz.dhtmlx.templates', 'gantt.html')

        task_classes_def, task_classes = self.__task_classes()

        if self.scale == 'day':
            scale = 2
        elif self.scale == 'month':
            scale = 1
        elif self.scale == 'year':
            scale = 0
        else:
            scale = 3

        return Template(template).substitute(
            readonly='true',
            row_height=self.__js(self.row_height),
            today_marker=self.__js(self.today_marker),
            columns=self.__columns(),
            scale=scale,
            task_classes_def=task_classes_def,
            gantt_data=self.__data(task_classes)
        )

    def _repr_html_(self):
        return ('<iframe srcdoc="{html}" width="100%" height="{height}" '
                'style="border:none !important;" '
                'allowfullscreen webkitallowfullscreen mozallowfullscreen>'
                '</iframe>').format(html=escape(self.to_html()), height=self.height)
