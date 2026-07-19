"""
CLI Utility Functions
"""
from io import TextIOBase
from typing import (
    Any, BinaryIO, Callable, Optional, TextIO, Type, Union, cast, overload)

from .cmd import C, Action, Command
from .context import get_current_context
from .wraps import into_command

#** Variables **#
__all__ = ['echo', 'command', 'group']

#** Functions **#

def echo(
    *data: Any,
    file:  Union[TextIO, BinaryIO, None] = None,
    err:   bool = False,
    join:  str  = ' ',
    end:   str  = '\n'
):
    """
    cli context based echo command

    :param data: data to echo to configured stdout/stderr
    :param file: file override for echo location
    :param err:  default to stdout or stderr
    :param join: substring to join elements of data
    :param end:  ending suffix for echo
    """
    if file is None:
        ctx  = get_current_context()
        file = ctx.stderr if err else ctx.stdout

    is_binary = not isinstance(file, TextIOBase)
    file      = cast(Union[BinaryIO, TextIO], file)

    bin = []
    for arg in data:
        if not isinstance(arg, (str, bytes, bytearray)):
            arg = str(arg)
        if is_binary:
            arg = arg.encode() if isinstance(arg, str) else arg
            bin.append(arg)
        else:
            arg = arg.decode() if not isinstance(arg, str) else arg
            bin.append(arg)

    j = join.encode() if is_binary else join
    e = end.encode() if is_binary else end

    file.write(j.join(bin) + e) #type: ignore
    file.flush()

@overload
def command(
    name:     Optional[str] = None,
    about:    Optional[str] = None,
    category: Optional[str] = None,
    hidden:   bool          = False,
    cls:      None          = None,
) -> Callable[[Callable], Command]:
    ...

@overload
def command(
    name:     Optional[str] = None,
    about:    Optional[str] = None,
    category: Optional[str] = None,
    hidden:   bool          = False,
    cls:      Type[C]     = ...,
) -> Callable[[Callable], C]:
    ...

@overload
def command(name: Callable) -> Command:
    ...

def command(
    name:     Union[str, Action, None] = None,
    about:    Optional[str]            = None,
    category: Optional[str]            = None,
    hidden:   bool                     = False,
    cls:      Optional[Type[C]]        = None,
) -> Union[Callable[[Action], Command], C, Command]:
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

@overload
def group(
    name:     Optional[str]      = None,
    about:    Optional[str]      = None,
    category: Optional[str]      = None,
    hidden:   bool               = False,
    cls:      None               = None,
    invoke_without_command: bool = False,
) -> Callable[[Callable], Command]:
    ...

@overload
def group(
    name:     Optional[str]      = None,
    about:    Optional[str]      = None,
    category: Optional[str]      = None,
    hidden:   bool               = False,
    cls:      Type[C]            = ...,
    invoke_without_command: bool = False,
) -> Callable[[Callable], C]:
    ...

@overload
def group(name: Callable) -> Command:
    ...

def group(
    name:     Union[str, Action, None] = None,
    about:    Optional[str]            = None,
    category: Optional[str]            = None,
    hidden:   bool                     = False,
    cls:      Optional[Type[C]]        = None,
    invoke_without_command: bool       = False,
) -> Union[Callable[[Action], Command], C, Command]:
    """
    Generate a new `group` and uses the new decorated function as its action.

    :param name:     name of the group
    :param about:    group about description
    :param category: group category
    :param hidden:   hidden status of group
    """
    ctype = cls or Command
    cname = name if isinstance(name, str) else None
    def wrapper(action: Action) -> Command:
        cmd                     = ctype(action.__name__)
        cmd.action              = action
        cmd.name                = cname or cmd.name
        cmd.about               = about or cmd.about
        cmd.category            = category or cmd.category
        cmd.hidden              = hidden or cmd.hidden
        cmd.invoke_without_command = invoke_without_command
        return cmd
    return wrapper(name) if callable(name) else wrapper
