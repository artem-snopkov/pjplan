from html import escape
from string import Template
import importlib.resources as pkg_resources
from pjplan import WBS


class MermaidNetwork:

    def __init__(
            self,
            wbs: WBS,
            height: int = 300
    ):
        self.wbs = wbs
        self.height = height

    @staticmethod
    def __dict_to_style(d: dict) -> str:
        return ','.join([f'{k}:{v}' for k, v in d.items()])

    def __src(self):

        res = "flowchart LR\n"
        for t in self.wbs.tasks:
            t_name = t.name.replace('"', '')
            if len(t.predecessors) == 0:
                res += f"  0((Start)) --> {t.id}{{{{{t_name}}}}}\n"
            else:
                for p in t.predecessors:
                    p_name = p.name.replace('"', '')
                    res += f"  {p.id}{{{{{p_name}}}}} --> {t.id}{{{{{t_name}}}}}\n"

        for t in self.wbs.tasks:
            if 'network_bar_style' in t.__dict__:
                res += f'style {t.id} {self.__dict_to_style(t.network_bar_style)}\n'

        return res

    def to_html(self):
        template = pkg_resources.read_text('pjplan.viz.mermaid.templates', 'network.html')

        return Template(template).substitute(
            src=self.__src()
        )

    def _repr_html_(self):
        return ('<iframe srcdoc="{html}" width="100%" height="{height}" '
                'style="border:none !important;" '
                'allowfullscreen webkitallowfullscreen mozallowfullscreen>'
                '</iframe>').format(html=escape(self.to_html()), height=self.height)
