"""
all possible flags allowed to be passed into application and parsed from args
"""
from datetime import timedelta
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Optional, Any, Union

from .argument import *

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
    'FilePathFlag',
]

#: defintion for list of flags
Flags = List['Flag']

#** Functions **#

@contextmanager
def capture_errors():
    """simple context-manager to capture any conversion errors"""
    try:
        yield None
    except Exception:
        pass

#** Classes **#

@dataclass
class Flag:
    """
    baseclass Flag declaration
    
    :param name:      name of flag
    :param usage:     usage description
    :param default:   default value
    :param hidden:    hide flag in help if true
    :param required:  ensure flag has value before allowing action
    :param type:      supported type for flag
    :param has_value: internal tracker if flag does not have a value
    """

    name:      str
    usage:     Optional[str] = None
    default:   Any           = None
    hidden:    bool          = False
    required:  bool          = False
    type:      Any           = str
    has_value: bool          = True

    def __post_init__(self):
        """ensure all flag settings are validated or raise error"""
        if self.default is not None and isinstance(self.type, type):
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
        with capture_errors():
            return self.type(value)

@dataclass
class BoolFlag(Flag):
    """implementation for supporting boolean flags"""
    type:      Any  = bool
    default:   Any  = False
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
    """
    implementation for supporting controlable decimal flags

    :param decimal: number of allowed decimal places
    """
    type:    Any = float
    decimal: int = 2

    def convert(self, value: str) -> Optional[float]:
        """handle float founding based on decimal setting"""
        with capture_errors():
            return parse_decimal(value)

@dataclass
class ListFlag(Flag):
    """implementatin for supporting list flags"""
    type: Any = list

    def convert(self, value: str) -> Optional[list]:
        """convert value into list object"""
        with capture_errors():
            return [c.strip() for c in value.split(',')]

@dataclass
class DurationFlag(Flag):
    """implementation for supporting time-duration flags"""
    type: Any = timedelta

    def convert(self, value: str) -> Optional[timedelta]:
        """convert string-value into timedelta"""
        with capture_errors():
            return parse_duration(value)

@dataclass
class EnumFlag:
    """
    implementation for supporting enum-value flags

    :param enum: enumeration allowed of allowed values in flag
    """
    enum: Union[set, dict]
    type: Any = str

    def convert(self, value: str) -> Optional[str]:
        """ensure the specified value is included in the enum"""
        with capture_errors():
            if value not in self.enum:
                return
            return self.enum[value] if isinstance(self.enum, dict) else value

@dataclass
class FilePathFlag(Flag):
    """
    implementation for supporting existing/new file-paths

    :param exists: ensure file exists if true
    """
    type:   Any  = str
    exists: bool = True

    def convert(self, value: str) -> str:
        """ensure filepath exists or doesn't exist based on `exists` setting"""
        if self.exists:
            return parse_existing_file(value)
        return parse_new_file(value)
