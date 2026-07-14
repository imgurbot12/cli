"""
Command-Line-Interface Parsing Library
"""
from enum import Enum
from typing import (
    Annotated, Any, Callable, Dict, Iterable, List, Optional, Type, TypeVar,
    cast, get_args, get_origin, get_type_hints)

#TODO: assume anything with `-` before `--` is a flag and parse it as such
#TODO:   include tip on unexpected when flag could potentially act as an argument
#TODO: errors should be more precisce -> double flag, extra arg, etc...
#TODO: anything after -- is just an argument
#        include tip on unexpected when arg could be flag/command

#** Variables **#
__all__ = [
    'App',
    'Arg',
    'Args',
    'Command',
    'Flag',

    'Parser',
    'ParsedCmd',
    'Suggestor',

    'SuggestFunc',
]

E           = TypeVar('E', bound=Enum)
T           = TypeVar('T')
SuggestFunc = Callable[[str], Iterable[str]]

#** Functions **#

def get_type(self, ftype: Optional[Type[T]]) -> Type[T]:
    """
    """
    ftype = ftype or getattr(self, 'type', None)
    if ftype is not None:
        return ftype
    default = getattr(self, 'default', None)
    if default is not None:
        return type(self.default)
    validators = getattr(self, 'validators', None)
    if validators:
        for validator in validators[::-1]:
            hints = get_type_hints(validator)
            if 'return' in hints:
                return hints['return']
    return cast(Type, str)

def get_validator(type: Type,
    validators: List['ValidatorFunc']) -> List['ValidatorFunc']:
    """
    """
    validator = DEFAULT_VALIDATORS.get(type)
    if validator is not None:
        validators.append(validator)
        return validators
    if get_origin(type) is Annotated:
        for arg in get_args(type):
            if isinstance(arg, Validator):
                validators.append(arg.validator)
    if not validators and type is not str:
        return [type]
    return validators

#** Classes **#

class MISSING:
    pass

class Context:
    """
    """
    parsed:  'ParsedCmd'
    command: Command
    parent:  Optional['Context']
    args:    Dict[str, Any]
    flags:   Dict[str, Any]
    extra:   Dict[str, Any]

    def __init__(self, parsed: 'ParsedCmd', parent: Optional['Context'] = None):
        self.parsed  = parsed
        self.command = parsed.source
        self.args    = parsed.args
        self.flags   = parsed.flags
        self.parent  = parent
        self.extra   = parent.extra if parent else {}

    def _get(self, dict: Dict[str, Any], name: str, cast: Optional[Type[T]]) -> T:
        """
        """
        value = dict[name]
        if cast is not None and not isinstance(value, cast):
            t1 = type(value).__name__
            t2 = cast.__name__
            raise TypeError(f'{name!r} ({t1}) is not a {t2}')
        return value

    def get(self, name: str,
        cast: Optional[Type[T]] = None, default: Any = MISSING) -> T:
        """
        """
        value = self.args.get(name, MISSING)
        value = self.flags.get(name, MISSING) if value is MISSING else value
        value = self.extra.get(name, MISSING) if value is MISSING else value
        value = default if value is MISSING else value
        if value is MISSING:
            raise KeyError(name)
        if cast is not None and not isinstance(value, cast):
            t1 = type(value).__name__
            t2 = cast.__name__
            raise TypeError(f'{name!r} ({t1}) is not a {t2}')
        return value

    def get_arg(self, name: str, cast: Optional[Type[T]] = None) -> T:
        """
        """
        return self._get(self.args, name, cast)

    def get_flag(self, name: str, cast: Type[T]) -> T:
        """
        """
        return self._get(self.flags, name, cast)

    def get_extra(self, name: str, cast: Type[T]) -> T:
        """
        """
        return self._get(self.extra, name, cast)

    def stack(self, parsed: 'ParsedCmd') -> 'Context':
        """
        """
        return self.__class__(parsed, parent=self)

#** Imports **#
from .app import App
from .arg import Arg, Args
from .command import Command
from .flag import Flag
from .parser import Parser, ParsedCmd
from .suggest import Suggestor
from .validate import DEFAULT_VALIDATORS, Validator, ValidatorFunc
