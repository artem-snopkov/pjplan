from typing import List, Optional

WHITE = '37m'
RED = '91m'
GREEN = '92m'
YELLOW = '93m'
BLUE = '94m'
PINK = '95m'
TEAL = '96m'
GREY = '97m'


def colored(text, color):
    if color is not None:
        return '\033[' + color + text + '\033[0m'
    else:
        return text


def colored_text(text, width, color, bg_color):
    c = color if color is not None else ''
    if bg_color is not None:
        c += ':' + bg_color

    text = text + ' ' * (width - len(text))

    if len(c) > 0:
        return '\033[' + color + text + '\033[0m'
    else:
        return text


class _TextTableCell:
    def __init__(self, text: str = None, color: str = None, bg_color: str = None):
        self.text = text
        self.color = color
        self.bg_color = bg_color


class _TextTableRow:

    def __init__(self, color: str = None, bg_color: str = None):
        self.color = color
        self.bg_color = bg_color
        self.cells = []

    def add_cell(self, text: str = None, color: str = None, bg_color: str = None):
        if color is None:
            color = self.color
        if bg_color is None:
            bg_color = self.bg_color

        self.cells.append(_TextTableCell(text, color, bg_color))

    def get_cell(self, idx) -> _TextTableCell:
        return self.cells[idx]

    def __len__(self):
        return len(self.cells)

    def repr(self, width: List[int], border: bool = False, border_color: str = None) -> str:
        res = ''
        if border:
            res += colored_text('|', 1, border_color, self.bg_color)

        for i in range(0, len(width)):
            if i < len(self.cells):
                cell = self.cells[i]
                text = colored_text(' ' + cell.text + ' ', width[i] + 2, cell.color, cell.bg_color)
            else:
                text = colored_text('  ', width[i] + 2, self.color, self.bg_color)

            res += text
            if border:
                res += colored_text('|', 1, border_color, self.bg_color)

        return res


class TextTable:

    def __init__(self):
        self.__rows: List[_TextTableRow] = []
        self.__current_row: Optional[_TextTableRow] = None

    def new_row(self, color: str = None, bg_color: str = None):
        self.__current_row = _TextTableRow(color, bg_color)
        self.__rows.append(self.__current_row)

    def new_cell(self, text: str = None, color: str = None, bg_color: str = None):
        self.__current_row.add_cell(text, color, bg_color)

    def text_repr(self, border: bool = False, border_color: str = None):
        # Calc widths
        widths_map = {}
        for r in self.__rows:
            for i in range(0, len(r)):
                widths_map[i] = max(len(r.get_cell(i).text), widths_map.setdefault(i, 0))

        widths = [v for v in widths_map.values()]

        # Print table
        res = ''
        for r in self.__rows:
            if len(res) > 0:
                res += '\n'
            res += r.repr(widths, border, border_color)

        return res
