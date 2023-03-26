import sys
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

sys.path.append('../../src')

from pjplan import Task, DefaultScheduler, WBS, MermaidGantt


def page(project: WBS):
    st.set_page_config(
        layout="wide",
        page_title='Mermaid Gantt Streamlit Example',
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

    gantt = MermaidGantt(project)

    components.html(gantt.to_html(), height=500)


if __name__ == '__main__':
    with WBS('Test project') as prj:
        prj // Task(1, 'Task 1', estimate=40, resource='Tester')
        prj // Task(2, 'Task 2', predecessors=[prj(1)], estimate=20, resource='Tester')
        with prj // Task(3, 'Task 3') as t:
            t // Task(4, 'Task 4', predecessors=[prj(2)], estimate=100)
            t // Task(5, 'Task 5', predecessors=[prj(2)], estimate=50)
        with prj // Task(6, 'Task 6') as t:
            t // Task(7, 'Task 7', predecessors=[prj(5)], estimate=16)
            t // Task(8, 'Task 8', predecessors=[prj(7)], estimate=16)

    plan, usage = DefaultScheduler(datetime.now()).calc(prj)

    page(plan)
