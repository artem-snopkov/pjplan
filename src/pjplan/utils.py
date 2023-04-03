WHITE = '37m'
RED = '91m'
GREEN = '92m'
YELLOW = '93m'
BLUE = '94m'
PINK = '95m'
TEAL = '96m'
GREY = '97m'


def colored(text, color):
    return '\033[' + color + text + '\033[0m'