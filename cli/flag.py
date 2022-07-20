"""
all possible flags allowed to be passed into application and parsed from args
"""
import re
from datetime import timedelta
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Any, Union

#** Variables **#
__all__ = [
    'Flags',

    'Flag',

    'BoolFlag',
    'IntFlag',
    'StringFlag',
    'FloatFlag',
    'DecimalFlag',
    'ListFlag',
    'DurationFlag',
    'EnumFlag',
]

#: defintion for list of flags
Flags = List['Flag']

_re_duration = re.compile(
    r'^(?P<weeks>\d+w)?'
    r'(?P<days>\d+d)?'
    r'(?P<hours>\d+h)?'
    r'(?P<minutes>\d+m)?'
    r'(?P<seconds>\d+s)?$'
)

#** Classes **#

@dataclass
class Flag:
    """baseclass Flag declaration"""

    name:      str
    usage:     Optional[str] = None
    default:   Any  = None
    hidden:    bool = False
    required:  bool = False

    type:      Any = str
    has_value: bool = True
    builtin:   bool = False

    def __post_init__(self):
        """ensure all flag settings are validated or raise error"""
        if self.default is not None:
            if not isinstance(self.default, self.type):
                raise ValueError('default=%r not type=%s' % (
                    self.default, self.type.__name__))

    def to_string(self) -> str:
        """convert flag names to string for help formatting"""
        return self.name

    @property
    def names(self) -> List[str]:
        """retrieve list of possible flag names"""
        return self.name.split(', ', 1)

    def index(self, values: List[str]) -> int:
        """
        return index of flag in values if found

        :param values: list of values to search
        :return:       index-num (if found); -1 (if missing)
        """
        names = self.names
        for n, value in enumerate(values, 0):
            if value.lstrip('-') in names and value.startswith('-'):
                return n
        return -1

    def convert(self, value: str) -> Any:
        """convert cli-value into the correct-type"""
        try:
            return self.type(value)
        except Exception:
            return None

@dataclass
class BoolFlag(Flag):
    """implementation for supporting boolean flags"""
    type: Any = bool
    default: Any = False
    has_value: bool = False

@dataclass
class IntFlag(Flag):
    """implementation for supporting integer flags"""
    type: Any = int

@dataclass
class StringFlag(Flag):
    """implementation for supporting string flags"""
    type: Any = str

@dataclass
class FloatFlag(Flag):
    """implementation for supporting flag flags"""
    type: Any = float

@dataclass
class DecimalFlag(Flag):
    """implementation for supporting controlable decimal flags"""
    type: Any = float
    decimal: int = 2

    def convert(self, value: str) -> Optional[float]:
        """handle float founding based on decimal setting"""
        try:
            return round(float(value), self.decimal)
        except Exception:
            return None

@dataclass
class ListFlag(Flag):
    """implementatin for supporting list flags"""
    type: Any = list

    def convert(self, value: str) -> Optional[list]:
        """convert value into list object"""
        try:
            return [c.strip() for c in value.split(',')]
        except Exception:
            return None

@dataclass
class DurationFlag(Flag):
    """implementation for supporting time-duration flags"""
    type: Any = timedelta

    def convert(self, value: str) -> Optional[timedelta]:
        """convert string-value into timedelta"""
        try:
            m = _re_duration.match(value).groupdict()
            d = {k:int(v.strip('wdhms') if v else 0) for k,v in m.items()}
            return timedelta(**d)
        except Exception:
            return None

@dataclass
class EnumFlag:
    """implementation for supporting enum-value flags"""
    enum: Union[set, dict]
    type: Any = str

    def convert(self, value: str) -> Optional[str]:
        """ensure the specified value is included in the enum"""
        try:
            # skip is value not in enum
            if value not in self.enum:
                return None
            # translate if dict, otherwise return value
            return self.enum[value] if isinstance(self.enum, dict) else value
        except Exception:
            return None
