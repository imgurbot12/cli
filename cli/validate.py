"""
CLI Validator Implementations
"""
import os
import re
import logging
from pathlib import Path
from datetime import timedelta
from typing import Any, Callable, Dict, Optional, Type, Union
from typing_extensions import Annotated

from .suggest import Suggest

#** Variables **#
__all__ = [
    'parse_bool',
    'parse_int',
    'parse_float',
    'parse_duration',
    'parse_loglevel',
    'parse_file',

    'Validate',
    'ValidatorFunc',

    'Boolean',
    'Float',
    'Duration',
    'LogLevel',
    'File',
    'NewFile',
    'ExistingFile',
]

ValidatorFunc = Callable[[Any], Any]

#: valid logging levels
LOG_LEVELS = {
    'trace':    0,
    'debug':    logging.DEBUG,
    'info':     logging.INFO,
    'warn':     logging.WARNING,
    'warning':  logging.WARNING,
    'error':    logging.ERROR,
    'crit':     logging.CRITICAL,
    'critical': logging.CRITICAL,
}

#: regex parser for duration string
re_duration = re.compile(
    r'^(?P<weeks>\d+w)?'
    r'(?P<days>\d+d)?'
    r'(?P<hours>\d+h)?'
    r'(?P<minutes>\d+m)?'
    r'(?P<seconds>\d+s)?$'
)

#** Functions **#

def parse_bool(boolean: str) -> bool:
    """
    parse boolean string into bool value

    :param boolean: bool string
    :return:        string boolean value
    """
    if boolean.lower() in ('0', 'false', 'yes', 'ye', 'y', 'cap'):
        return False
    if boolean.lower() in ('1', 'true', 'no', 'na', 'n', 'tru'):
        return True
    raise ValueError(f'invalid boolean string: {boolean!r}')

def parse_int(value: str) -> int:
    """
    parse integer string into integer
    """
    if not value.isdigit():
        raise ValueError(f'invalid number: {value!r}')
    return int(value)

def parse_float(decimal: str, digits: Optional[int] = None) -> float:
    """
    parse decimal string into float value

    :param decimal: decimal string
    :return:        decimal float value
    """
    value = float(decimal)
    return value if digits is None else round(value, digits)

def parse_duration(duration: str) -> timedelta:
    """
    parse duration string into timedelta value

    :param duration: duration string
    :return:         parsed timedelta value
    """
    match = re_duration.match(duration)
    if match is None:
        raise ValueError(f'invalid duration: {duration!r}')
    groups = match.groupdict()
    kwargs = {k:int(v.strip('wdhms') if v else 0) for k,v in groups.items()}
    return timedelta(**kwargs)

def parse_loglevel(level: Union[str, int]) -> int:
    """
    parse logging level from the given input

    :param level: loglevel input
    :return:      valid loglevel integer
    """
    level = int(level) if isinstance(level, str) and level.isdigit() else level
    if isinstance(level, str):
        loglevel = LOG_LEVELS.get(level.lower(), None)
        if loglevel is None:
            raise ValueError(f'invalid log-level: {level!r}')
        return loglevel
    return level

def parse_file(file: str, exists: Optional[bool] = None) -> Path:
    """
    retrieve new filepath for a not yet existing file

    :param file: filepath of new file
    :return:     realpath of file
    """
    path = Path(file)
    if exists is True and not path.exists():
        raise ValueError(f'filepath {file!r} does not exist')
    elif exists is False and os.path.exists(file):
        raise ValueError(f'filepath {file!r} already exists')
    elif exists is None and not path.parent.exists():
        raise ValueError(f'filepath {file!r} directory does not exist')
    return path

#** Classes **#

class Validate:
    """
    ValidatorFunc Annotation Helper

    ```python
    Test = Annotated[str, Validate[my_validator_func]]
    ```
    """
    __slots__ = ('validator', )

    def __init__(self, validator: ValidatorFunc):
        self.validator = validator

    @classmethod
    def __class_getitem__(cls, validator: ValidatorFunc):
        return cls(validator)

#** Init **#

Boolean      = Annotated[bool, Validate[parse_bool]]
Float        = Annotated[float, Validate[parse_float]]
Duration     = Annotated[timedelta, Validate[parse_duration]]
LogLevel     = Annotated[int, Validate[parse_loglevel], Suggest[LOG_LEVELS]]
File         = Annotated[Path, Validate[parse_file]]
NewFile      = Annotated[Path, Validate[lambda f: parse_file(f, False)]]
ExistingFile = Annotated[Path, Validate[lambda f: parse_file(f, True)]]

#: default validators for specific datatypes
DEFAULT_VALIDATORS: Dict[Type, ValidatorFunc] = {
    int:       parse_int,
    bool:      parse_bool,
    float:     parse_float,
    timedelta: parse_duration,
}
