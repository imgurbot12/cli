"""
Command-Line-Interface Parsing Library
"""
from enum import Enum
from typing import (
    Annotated, Callable, Iterable, List, Optional, Type, TypeVar, Union,
    cast, get_args, get_origin, get_type_hints, overload)

#TODO: functions:  cli.group/cli.context/cli.echo
#TODO: decorators: cli.argument/cli.flag to override/enhance parsed details
#TODO: handle ValueError exceptions on data-type issues
#TODO: errors should be more precisce -> double flag, extra arg, etc...
#TODO: docstrings for all functions

#** Variables **#
__all__ = [
    'echo',
    'command',
    'get_current_context',

    'App',
    'Arg',
    'Args',
    'Command',
    'Context',
    'Flag',

    'Parser',
    'ParsedCmd',
    'Suggestor',
    'SuggestFunc',
]

E           = TypeVar('E', bound=Enum)
T           = TypeVar('T')
SuggestFunc = Callable[[str], Iterable[str]]

#TODO: use context-vars to pass around context!!

#** Functions **#

@overload
def command(
    name:     Optional[str]       = None,
    about:    Optional[str]       = None,
    category: Optional[str]       = None,
    hidden:   bool                = False,
    cls:      None                = None,
) -> Callable[[Callable], Command]:
    ...

@overload
def command(
    name:     Optional[str] = None,
    about:    Optional[str] = None,
    category: Optional[str] = None,
    hidden:   bool          = False,
    cls:      Type['C']     = ...,
) -> Callable[[Callable], 'C']:
    ...

@overload
def command(name: Callable) -> 'Command':
    ...

def command(
    name:     Union[str, 'Action', None] = None,
    about:    Optional[str]              = None,
    category: Optional[str]              = None,
    hidden:   bool                       = False,
    cls:      Optional[Type['C']]        = None,
) -> Union[Callable[['Action'], 'Command'], 'C', 'Command']:
    """
    Generate a new `Command` and uses the new decorated function as its action.

    :param name:     name of the command
    :param about:    command about description
    :param category: command category
    :param hidden:   hidden status of command
    """
    cname = name if isinstance(name, str) else None
    def wrapper(action: Action) -> Command:
        cmd          = into_command(action, cls or Command)
        cmd.name     = cname or cmd.name
        cmd.about    = about or cmd.about
        cmd.category = category or cmd.category
        cmd.hidden   = hidden or cmd.hidden
        return cmd
    return wrapper(name) if callable(name) else wrapper

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


#** Imports **#
from .app import App
from .arg import Arg, Args
from .cmd import C, Action, Command
from .context import Context, get_current_context
from .flag import Flag
from .parser import Parser, ParsedCmd
from .suggest import Suggestor
from .utils import echo
from .validate import DEFAULT_VALIDATORS, Validator, ValidatorFunc
from .wraps import into_command
