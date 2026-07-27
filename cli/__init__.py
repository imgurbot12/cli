"""
Command-Line-Interface Parsing Library
"""
from enum import Enum
from typing import (
    Callable, Iterable, List, Literal, NamedTuple, Optional,
    Tuple, Type, TypeVar, Union, cast)
from typing_extensions import Annotated, get_args, get_origin, get_type_hints

#DONE: handle ValueError exceptions on data-type issues
#DONE: functions:  cli.group/cli.context/cli.echo
#DONE: decorators: cli.argument/cli.flag/cli.pass_context to override/enhance parsed details

#DONE: pass `Context` with annotation present or @cli.pass_context wrapper
#DONE: moar unit-tests for parser
# - extra arg / missing arg / invalid arg / arg repeat
# - extra flag / missing flag / invalid flag / missing flag value / invalid flag value / flag repeat
# - repeated command
# - group / command tree (subcmd-required difference)

#DONE: docs
# - simple hello world
# - `Context.extra` and pass via function args

#DONE: suggestor unit-tests
#DONE: controls on stripping/ignoring styling when writing to file instead of tty
#DONE: help-page implementation (with colors)

#DONE: docstrings for all functions
#TODO: give indexing another shot (but count down rather than up)
#TODO: errors should be more precisce -> double flag, extra arg, etc...

#TODO: command categories does nothing
#TODO: authors will never be displayed ever in help
#TODO: version will never be displayed ever (maybe add version flag with support for more info?)

#** Variables **#
__all__ = [
    'echo',
    'style',
    'secho',
    'argument',
    'extra',
    'option',
    'command',
    'group',
    'get_current_context',

    'Arg',
    'Command',
    'Context',
    'Flag',

    'CliError',
    'Extra',
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
    retrieve real type associated with arg/flag and update the relevant attrs

    :param ftype: type annotation assignment
    :return:      (true type, option metadata)
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
    get suggestor function or configuration based on type

    :param type:    arg/flag type
    :param suggest: suggestion setting
    :return:        suggestion
    """
    if suggest is not None:
        return suggest
    if get_origin(type) is not Annotated:
        return None
    for arg in get_args(type):
        if isinstance(arg, Suggest):
            return arg.suggestor
    return None

def get_validator(type: Type,
    validators: List['ValidatorFunc']) -> List['ValidatorFunc']:
    """
    retrieve validators based on arg/flag configuration

    :param type:       type assignment for arg/flag
    :param validators: list of established validators
    :return:           complete list of validators
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
from .utils import echo, style, secho, argument, extra, option, command, group
from .validate import DEFAULT_VALIDATORS, Validate, ValidatorFunc
from .wraps import Extra
