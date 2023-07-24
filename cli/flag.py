"""
all possible flags allowed to be passed into application and parsed from args
"""
from contextlib import contextmanager
from datetime import timedelta
from typing import Optional, Any, Union, Type, List, ClassVar

from pyderive import dataclass, field

from .abc import *
from .argument import *

#** Variables **#
__all__ = [
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

#** Functions **#

@contextmanager
def capture_errors():
    """simple context-manager to capture any conversion errors"""
    try:
        yield None
    except Exception:
        pass

#** Classes **#

#TODO: move flag validation to app setup and execution

@dataclass(slots=True)
class Flag(AbsFlag[T]):
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
    type:      Type[T]
    usage:     Optional[str]      = field(default=None,  kw_only=True)
    default:   Any                = field(default=None,  kw_only=True)
    hidden:    bool               = field(default=False, kw_only=True)
    required:  bool               = field(default=False, kw_only=True)
    has_value: bool               = field(default=True,  kw_only=True)
    parser:    Optional[TypeFunc] = field(default=None,  kw_only=True) #type: ignore

    def __post_init__(self):
        self.parser: TypeFunc = self.parser or self.type

    def parse(self, value: str) -> T:
        """convert cli-value into the correct-type"""
        with capture_errors():
            return self.parser(value)

@dataclass(slots=True)
class BoolFlag(Flag[bool]):
    """implementation for supporting boolean flags"""
    type:      ClassVar[Type] = bool
    default:   bool           = False
    has_value: bool           = False

@dataclass(slots=True)
class IntFlag(Flag[int]):
    """implementation for supporting integer flags"""
    type: ClassVar[Type] = int

@dataclass(slots=True)
class StringFlag(Flag[str]):
    """implementation for supporting string flags"""
    type: ClassVar[Type] = str

@dataclass(slots=True)
class FloatFlag(Flag[float]):
    """implementation for supporting flag flags"""
    type: ClassVar[Type] = float

@dataclass(slots=True)
class DecimalFlag(Flag[float]):
    """
    implementation for supporting controlable decimal flags

    :param decimal: number of allowed decimal places
    """
    type:    ClassVar[Type] = float
    decimal: int            = 2

    def parse(self, value: str):
        """handle float founding based on decimal setting"""
        with capture_errors():
            return parse_decimal(value, self.decimal)

@dataclass(slots=True)
class ListFlag(Flag[List[str]]):
    """implementatin for supporting list flags"""
    type: ClassVar[Type] = list

    def parse(self, value: str):
        """convert value into list object"""
        with capture_errors():
            return [c.strip() for c in value.split(',')]

@dataclass(slots=True)
class DurationFlag(Flag[timedelta]):
    """implementation for supporting time-duration flags"""
    type: ClassVar[Type] = timedelta

    def parse(self, value: str):
        """convert string-value into timedelta"""
        with capture_errors():
            return parse_duration(value)

@dataclass(slots=True)
class EnumFlag(Flag[Any]):
    """
    implementation for supporting enum-value flags

    :param enum: enumeration allowed of allowed values in flag
    """
    type: ClassVar[Type] = Any
    enum: Union[set, dict]
    
    def parse(self, value: str) -> Optional[Any]:
        """ensure the specified value is included in the enum"""
        with capture_errors():
            if value not in self.enum:
                return
            return self.enum[value] if isinstance(self.enum, dict) else value

@dataclass(slots=True)
class FilePathFlag(Flag[str]):
    """
    implementation for supporting existing/new file-paths

    :param exists: ensure file exists if true
    """
    type:   ClassVar[Type] = str
    exists: bool           = True

    def parse(self, value: str) -> str:
        """ensure filepath exists or doesn't exist based on `exists` setting"""
        if self.exists:
            return parse_existing_file(value)
        return parse_new_file(value)
