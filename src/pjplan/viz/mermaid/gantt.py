import importlib.resources as pkg_resources
from datetime import datetime
from html import escape
from string import Template

from pjplan import Task, WBS


class MermaidGantt:

    def __init__(
            self,
            wbs: WBS,
            height: int = 300,
            weekends: bool = False,
            tick_interval: str = None,
            title: str = None
    ):
        self.wbs = wbs
        self.weekends = weekends
        self.tick_interval = tick_interval
        self.title: str = title if title else None
        self.height = height

    @staticmethod
    def __dict_to_css(style_dict: dict):
        res = '{'
        for k, v in style_dict.items():
            res += f'{k}:{v}!important;'
        res += '}'
        return res

    def __styles(self):
        bar_styles = {}
        text_styles = {}
        for t in self.wbs.tasks:
            if 'gantt_bar_style' in t.__dict__:
                bar_styles.setdefault(self.__dict_to_css(t.gantt_bar_style), []).append(t.id)
            if 'gantt_text_style' in t.__dict__:
                text_styles.setdefault(self.__dict_to_css(t.gantt_text_style), []).append(t.id)

        res = ""
        for k, v in bar_styles.items():
            res += ', '.join([f'#id_{tid}' for tid in v]) + k + '\n'

        for k, v in text_styles.items():
            res += ', '.join([f'#id_{tid}-text' for tid in v]) + k + '\n'

        return res

    @staticmethod
    def __mermaid_task_state(task: Task):
        now = datetime.now()
        if task.milestone:
            return 'milestone,'
        if task.end <= now:
            return 'done,'
        if task.start < now:
            return 'active,'
        return ''

    def __mermaid_task(self, t: Task) -> str:
        return "    {}: {} {}, {}, {}\n".format(
            t.name.replace(':', ''),
            self.__mermaid_task_state(t),
            'id_' + str(t.id),
            t.start.strftime('%d.%m.%Y %H:%M'),
            t.end.strftime('%d.%m.%Y %H:%M')
        )

    def __src(self):
        res = "gantt\n"
        res += "  dateFormat DD.MM.YYYY HH:mm\n"
        if self.title is not None:
            res += "  title {}\n".format(self.title)
        if self.weekends:
            res += "  excludes weekends\n"
        if self.tick_interval:
            res += "  tickInterval {}\n".format(self.tick_interval)

        tasks = self.wbs.tasks

        sections = set([task.gantt_section if 'gantt_section' in task.__dict__ else '-' for task in tasks])
        if len(sections) == 1:
            sections = None

        if sections:
            sections_map = {}
            for task in tasks:
                task_section = task.gantt_section if 'gantt_section' in task.__dict__ else '-'
                sections_map.setdefault(task_section, []).append(task)

            for k, v in sections_map.items():
                res += f"  section {k}\n"
                for task in v:
                    res += self.__mermaid_task(task)

        else:
            for task in tasks:
                res += self.__mermaid_task(task)

        return res

    def to_html(self):
        template = pkg_resources.read_text('pjplan.viz.mermaid.templates', 'gantt.html')

        return Template(template).substitute(
            styles=self.__styles(),
            src=self.__src()
        )

    def _repr_html_(self):
        return ('<iframe srcdoc="{html}" width="100%" height="{height}" '
                'style="border:none !important;" '
                'allowfullscreen webkitallowfullscreen mozallowfullscreen>'
                '</iframe>').format(html=escape(self.to_html()), height=self.height)
