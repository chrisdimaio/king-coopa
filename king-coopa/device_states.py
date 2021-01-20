from enum import Enum, auto


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class States(AutoName):
    OFF = auto()
    ON = auto()
    OPEN = auto()
    OPENING = auto()
    CLOSED = auto()
    CLOSING = auto()
