import csv
from datetime import datetime
from typing import List, Optional

from pjplan import WBS
from pjplan.io.raw import TaskRaw, raws_to_wbs, tasks_to_raws

__DATE_FORMAT = '%d.%m.%y'


def __parse_header(row) -> dict:
    res = {}
    for i in range(0, len(row)):
        name = row[i].replace('\ufeff', '')
        res[name] = i
    return res


def __parse_str(_val: str):
    if _val == '':
        return None
    return _val


def __parse_date(_date: str) -> Optional[datetime]:
    if len(_date) == 0:
        return None
    return datetime.strptime(_date, __DATE_FORMAT)


def __parse_predecessors(_val: str) -> List[int]:
    if len(_val) == 0:
        return []
    return [int(v) for v in _val.split(';')]


def __parse_float(_val: str) -> Optional[float]:
    if len(_val) == 0:
        return None
    return float(_val)


def __parse_int(_val: str) -> Optional[int]:
    if len(_val) == 0:
        return None
    return int(_val)


def __parse_bool(_val: str) -> bool:
    if len(_val) == 0:
        return False
    return _val == 'True'


__DEFAULT_FIELDS = [
    'id', 'name', 'resource', 'start', 'end', 'estimate', 'spent', 'milestone', 'parent_id', 'predecessor_ids'
]


def read_csv(path: str, encoding='utf-8', delimiter=';') -> WBS:
    raws: List[TaskRaw] = []
    with open(path, mode='r', encoding=encoding, newline='\n') as input_file:
        csvfile = csv.reader(input_file, delimiter=delimiter)
        header = __parse_header(next(csvfile))
        for row in csvfile:
            kwargs = {}
            for k, v in header.items():
                if k not in __DEFAULT_FIELDS:
                    kwargs[k] = row[v]

            raws.append(
                TaskRaw(
                    id=int(row[header['id']]),
                    name=__parse_str(row[header['name']]),
                    resource=__parse_str(row[header['resource']]),
                    start=__parse_date(row[header['start']]),
                    end=__parse_date(row[header['end']]),
                    estimate=__parse_float(row[header['estimate']]),
                    spent=__parse_float(row[header['spent']]),
                    milestone=__parse_bool(row[header['milestone']]),
                    parent_id=__parse_int(row[header['parent_id']]),
                    predecessor_ids=__parse_predecessors(row[header['predecessor_ids']]),
                    **kwargs
                )
            )

    return raws_to_wbs(raws)


def write_csv(wbs: WBS, path: str, encoding='utf-8', delimiter=';'):
    raws = tasks_to_raws(wbs.tasks)

    with open(path, mode='w', encoding=encoding, newline='\n') as output_file:
        csvwriter = csv.writer(output_file, delimiter=delimiter)
        fields = {}
        for t in raws:
            for k, v in t.__dict__.items():
                if k not in __DEFAULT_FIELDS:
                    fields[k] = type(v).__name__
        field_list = [f"{k}" for k in fields.keys()]
        csvwriter.writerow(__DEFAULT_FIELDS + field_list)

        for task in raws:
            csvwriter.writerow([
                task.id,
                task.name if task.name else '',
                task.resource if task.resource else '',
                task.start.strftime(__DATE_FORMAT) if task.start is not None else None,
                task.end.strftime(__DATE_FORMAT) if task.end is not None else None,
                task.estimate,
                task.spent,
                task.milestone,
                task.parent_id,
                ';'.join([str(pid) for pid in task.predecessor_ids])
            ] + [
                task.__getattribute__(k) if k in task.__dict__ and not k.startswith('_') else '' for k in field_list
            ])
