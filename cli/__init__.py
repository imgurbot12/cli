"""
Command-Line-Interface Parsing Library
"""
from enum import Enum
from typing import (
    Callable, Iterable, List, Literal, NamedTuple, Optional, Tuple, Type, TypeVar, Union, cast)
from typing_extensions import Annotated, get_args, get_origin, get_type_hints

#DONE: handle ValueError exceptions on data-type issues
#TODO: functions:  cli.group/cli.context/cli.echo
#TODO: decorators: cli.argument/cli.flag/cli.pass_context to override/enhance parsed details
#TODO: errors should be more precisce -> double flag, extra arg, etc...
#TODO: docstrings for all functions

#DONE: pass `Context` with annotation present or @cli.pass_context wrapper
#DONE: moar unit-tests for parser
# - extra arg / missing arg / invalid arg / arg repeat
# - extra flag / missing flag / invalid flag / missing flag value / invalid flag value / flag repeat
# - repeated command
# - group / command tree (subcmd-required difference)

#DONE: suggestor unit-tests
#DONE: controls on stripping/ignoring styling when writing to file instead of tty
#DONE: help-page implementation (with colors)
#TODO: give indexing another shot (but count down rather than up)

#** Variables **#
__all__ = [
    'echo',
    'style',
    'secho',
    'option',
    'command',
    'group',
    'get_current_context',

    'Arg',
    'Command',
    'Context',
    'Flag',

    'CliError',
    'Validate',
    'Suggest',

    'Help',
    'Parser',
    'ParsedCmd',
    'Suggestor',
]

E = TypeVar('E', bound=Enum)
T = TypeVar('T')

SuggestFunc = Callable[[str], Iterable[str]]
OptSuggest  = Union['SuggestFunc', Literal[False], None]

#** Classes **#

class _Meta(NamedTuple):
    repeat:   bool = False

#** Functions **#

def get_type(self, ftype: Optional[Type[T]]) -> Tuple[Type[T], _Meta]:
    """
    """
    ftype = ftype or getattr(self, 'type', None)
    if ftype is not None:
        origin = get_origin(ftype)
        args   = get_args(ftype)
        if origin is None or origin is Annotated:
            return ftype, _Meta()
        if origin in (list, set):
            return args[0], _Meta(repeat=True)
        if origin is Union and len(args) == 2 and args[1] is type(None):
            return get_type(self, args[0])
        raise TypeError(ftype)
    default = getattr(self, 'default', None)
    if default is not None:
        return type(self.default), _Meta()
    validators = getattr(self, 'validators', None)
    if validators:
        for validator in validators[::-1]:
            hints = get_type_hints(validator)
            if 'return' in hints:
                return hints['return']
    return cast(Type, str), _Meta()

def get_suggestor(type: Type, suggest: OptSuggest) -> OptSuggest:
    """
    """
    if suggest is not None:
        return suggest
    if get_origin(type) is not Annotated:
        return
    for arg in get_args(type):
        if isinstance(arg, Suggest):
            return arg.suggestor

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
            if isinstance(arg, Validate):
                validators.append(arg.validator)
    if not validators and type is not str:
        return [type]
    return validators

#** Imports **#
from .arg import Arg
from .cmd import Command
from .context import Context, get_current_context
from .errors import CliError
from .flag import Flag
from .help import Help
from .parser import Parser, ParsedCmd
from .suggest import Suggest, Suggestor
from .utils import echo, style, secho, option, command, group
from .validate import DEFAULT_VALIDATORS, Validate, ValidatorFunc
