"""
CLI Utility Functions
"""
from io import TextIOBase
from itertools import cycle
from collections import OrderedDict
from typing import (
    Any, Callable, List, Literal, Optional, Type,
    TypeVar, TypedDict, Union, cast, overload)
from typing_extensions import Unpack

from . import T, OptSuggest
from .flag import Short
from .cmd import C, Action, Command
from .context import AnyIO, get_current_context
from .style import Color, Style, Styling, AnsiTermStyle
from .wraps import ARG_ATTR, EXTRA_ATTR, FLAG_ATTR, into_command

#** Variables **#
__all__ = [
    'echo',
    'style',
    'secho',

    'extra',
    'argument',
    'option',
    'command',
    'group'
]

Func = TypeVar('Func', bound=Callable)

RAINBOW = [
    (255, 0,   0),   # Red
    (255, 127, 0),   # Orange
    (255, 255, 0),   # Yellow
    (0,   255, 0),   # Green
    (0,   0,   255), # Blue
    (75,  0,   130), # Indigo
    (148, 0,   211), # Violet
]

#** Classes **#

class StyleKwargs(TypedDict, total=False):
    color:     Union[Color, Literal['rainbow', 'party']]
    bold:      bool
    dim:       bool
    underline: bool
    overline:  bool
    italic:    bool
    blink:     bool
    reverse:   bool
    strike:    bool
    styling:   Styling
    reset:     bool

#** Functions **#

def _get_file(
    file: Optional[AnyIO], err: bool) -> AnyIO:
    """
    """
    if file is not None:
        return file
    ctx = get_current_context()
    return ctx.stderr if err else ctx.stdout

def echo(
    *data: Any,
    file:  Optional[AnyIO] = None,
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
    file      = _get_file(file, err)
    is_binary = not isinstance(file, TextIOBase)

    strip = lambda x: x
    if not file.isatty():
        ctx   = get_current_context()
        strip = ctx.styling.strip

    bin = []
    for arg in data:
        if not isinstance(arg, (str, bytes, bytearray)):
            arg = str(arg)
        if is_binary:
            arg = strip(arg).encode() if isinstance(arg, str) else arg
            bin.append(arg)
        else:
            arg = arg.decode() if not isinstance(arg, str) else arg
            bin.append(strip(arg))

    j = join.encode() if is_binary else join
    e = end.encode() if is_binary else end

    file.write(j.join(bin) + e) #type: ignore
    file.flush()

def style(text: Any, **kwargs: Unpack[StyleKwargs]) -> str:
    """
    add styling based on current command configuration to the given string

    :param text:   text content to style
    :param kwargs: styling to add to the text
    """
    text    = text if isinstance(text, str) else str(text)
    styling = kwargs.pop('styling', None)
    if styling is None:
        ctx     = get_current_context(silent=True)
        styling = ctx.styling if ctx is not None else AnsiTermStyle()

    reset = kwargs.pop('reset', True)
    color = kwargs.pop('color', None)
    start = []
    stop  = []
    for style, apply in kwargs.items():
        style = cast(Style, style)
        apply = cast(bool, apply)
        start.append(styling.toggle_style(style, apply))
        if reset and apply is True:
            stop.append(styling.reset_style(style))

    if color is not None:
        if color == 'rainbow' or color == 'party':
            text = ' '.join(
                styling.wrap_color(color, sec)
                for sec, color in zip(text.split(' '), cycle(RAINBOW)))
            if color == 'party':
                text = styling.wrap_style('blink', text)
        else:
            text = styling.wrap_color(color, text)

    start.append(text)
    start.extend(stop)
    return ''.join(start)

def secho(
    *data: Any,
    file: Optional[AnyIO] = None,
    err:  bool = False,
    join: str  = ' ',
    end:  str  = '\n',
    **kwargs: Unpack[StyleKwargs],
):
    """
    styling a string according to the confgiured settings and echo

    Acts as a simpler replacement for:

    ```python
    cli.echo(cli.style('hello world', color='blink'))
    ```
    """
    file    = _get_file(file, err)
    is_atty = file.isatty()
    items   = []
    for item in data:
        if is_atty and not isinstance(item, (bytes, bytearray)):
            item = style(item, **kwargs)
        items.append(item)
    return echo(*items, file=file, err=err, join=join, end=end)

def extra(name: str) -> Callable[[Func], Func]:
    """
    function decorator used to mark a parameter as extra
    """
    def wrapper(func: Func) -> Func:
        extra = getattr(func, EXTRA_ATTR, None) or set()
        extra.add(name)
        setattr(func, EXTRA_ATTR, extra)
        return func
    return wrapper

def argument(
    name: str,
    about:      Optional[str]                      = None,
    validators: Optional[List[Callable[[Any], T]]] = None,
    suggestor:  OptSuggest                         = None,
    required:   Optional[bool]                     = None,
) -> Callable[[Func], Func]:
    """
    Function decorator used to mark a parameter as an argument

    It also allows additional specification of attributes otherwise
    unable to be derived.
    """
    arg = dict(
        about=about,
        validators=validators,
        suggestor=suggestor,
        required=required,
    )
    def wrapper(func: Func) -> Func:
        args = getattr(func, ARG_ATTR, None) or OrderedDict()
        if name in args:
            raise RuntimeError(f'Arg: {name!r} already defined.')
        args[name] = arg
        setattr(func, ARG_ATTR, args)
        return func
    return wrapper

def option(
    name:       str,
    about:      Optional[str]                      = None,
    short:      Optional[Short]                    = None,
    long:       Optional[str]                      = None,
    hidden:     bool                               = False,
    validators: Optional[List[Callable[[Any], T]]] = None,
    suggestor:  OptSuggest                         = None,
    required:   bool                               = False,
) -> Callable[[Func], Func]:
    """
    Function decorator used to mark a parameter as an option/flag

    It also allows addiitonal specification of attributes otherwise
    unable to be derived.
    """
    flag = dict(
        about=about,
        short=short,
        long=long,
        hidden=hidden,
        validators=validators,
        suggestor=suggestor,
        required=required,
    )
    def wrapper(func: Func) -> Func:
        """
        """
        flags = getattr(func, FLAG_ATTR, None) or OrderedDict()
        if name in flags:
            raise RuntimeError(f'Flag: {name!r} already defined.')
        flags[name] = flag
        setattr(func, FLAG_ATTR, flags)
        return func
    return wrapper

@overload
def command(
    name:     Optional[str]      = None,
    about:    Optional[str]      = None,
    category: Optional[str]      = None,
    hidden:   bool               = False,
    cls:      None               = None,
    invoke_without_command: bool = False,
) -> Callable[[Callable], Command]:
    ...

@overload
def command(
    name:     Optional[str] = None,
    about:    Optional[str] = None,
    category: Optional[str] = None,
    hidden:   bool          = False,
    *, cls:   Type[C],
    invoke_without_command: bool = False,
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
    invoke_without_command: bool       = False,
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
        cmd.invoke_without_command = invoke_without_command
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
    *, cls:   Type[C],
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
