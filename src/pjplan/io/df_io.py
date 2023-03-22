from typing import Iterable

import pandas as pd

from pjplan.io import tasks_to_raws


def to_df(tasks: Iterable) -> pd.DataFrame:
    raws = tasks_to_raws(tasks)
    lst = [r.to_dict() for r in raws]
    return pd.DataFrame(lst)


