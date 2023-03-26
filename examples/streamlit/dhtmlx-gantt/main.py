import sys
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

sys.path.append('../../src')

from pjplan import Task, DefaultScheduler, WBS, DhtmlxGantt, DhtmlxGanttColumn


def page(project: WBS):
    st.set_page_config(
        layout="wide",
        page_title='Диаграмма Ганта',
    )

    st.markdown(
        f'''
        <style>
            .block-container {{
                padding: 40px 10px 10px 10px;
            }}
        </style>
        ''',
        unsafe_allow_html=True,
    )

    project(resource='Tester').gantt_bar_style = {
        'background': '#23964d'
    }

    gantt = DhtmlxGantt(
        project,
        row_height=30,
        today_marker=False,
        columns=[
            DhtmlxGanttColumn('id', 50),
            DhtmlxGanttColumn('name', 200),
            DhtmlxGanttColumn('start', 100),
            DhtmlxGanttColumn('end', 100, label='End date'),
            DhtmlxGanttColumn('progress', 100),
        ]
    )

    components.html(gantt.to_html(), height=500)


if __name__ == '__main__':

    with WBS('Проект') as prj:
        prj // Task(2, 'Задача 1', estimate=40, spent=20, resource='Tester')
        prj // Task(3, 'Задача 2', predecessors=[prj(2)], estimate=20, resource='Tester')
        with prj // Task(4, 'Задача 4') as t:
            t // Task(5, 'Задача 5', predecessors=[prj(3)], estimate=100)
            t // Task(6, 'Задача 6', predecessors=[prj(3)], estimate=50)
        with prj // Task(7, 'Задача 7') as t:
            t // Task(8, 'Задача 8', predecessors=[prj(6)], estimate=16)
            t // Task(9, 'Задача 9', predecessors=[prj(6)], estimate=16)

    plan, usage = DefaultScheduler(datetime.now()).calc(prj)

    page(plan)
