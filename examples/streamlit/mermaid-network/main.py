import sys

import streamlit as st
import streamlit.components.v1 as components

sys.path.append('../../src')

from pjplan import Task, WBS, MermaidNetwork


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

    diagram = MermaidNetwork(project)

    components.html(diagram.to_html(), height=500)


if __name__ == '__main__':
    with WBS() as prj:
        prj // Task(1, 'Task 1', resource='Tester')
        prj // Task(2, 'Task 2', predecessors=[prj(1)], estimate=20, resource='Tester')
        prj // Task(3, 'Task 3', predecessors=[prj(1)], estimate=20)
        prj // Task(4, 'Task 4', predecessors=[prj(3)], estimate=20)

    page(prj)
