"""
CLI Action Context
"""
import sys
from contextvars import ContextVar
from contextlib import contextmanager
from typing import (
    Any, BinaryIO, Dict, Generator, List, Literal, Optional, TextIO,
    Type, Union, cast, overload)
from typing_extensions import Annotated, get_origin, get_args

from . import T
from .style import Styling, AnsiTermStyle

#** Variables **#
__all__ = ['AnyIO', 'MISSING', 'Context', 'new_context', 'get_current_context']

AnyIO = Union[TextIO, BinaryIO]

context_stack: ContextVar[List['Context']] = ContextVar('context_stack')

#** Functions **#

@contextmanager
def new_context(
    parsed: 'ParsedCmd', **kwargs) -> Generator['Context', None, None]:
    """
    start new context object stack for the current cli job
    """
    context = Context(parsed, **kwargs)
    token   = context_stack.set([context])
    try:
        yield context
    finally:
        context_stack.reset(token)

@overload
def get_current_context(silent: Literal[False] = False) -> 'Context':
    ...

@overload
def get_current_context(silent: Literal[True] = True) -> Optional['Context']:
    ...

def get_current_context(silent: bool = False) -> Optional['Context']:
    """
    retrieve last stack from context-stack of current job
    """
    try:
        return context_stack.get()[-1]
    except LookupError as e:
        if silent: return None
        raise e

def typecheck(value: Any, typedef: Type) -> bool:
    """
    guarded isinstance check that handles specialized typedefs
    """
    origin = get_origin(typedef)
    args   = get_args(typedef)
    if origin in (list, dict, set, tuple):
        typedef = origin
    elif origin is Union:
        return any(typecheck(value, a) for a in args)
    elif origin is Annotated:
        typedef = args[0]
    return isinstance(value, typedef)

#** Classes **#

class MISSING:
    pass

class Context:
    """
    CLI Command Action Runtime Context
    """
    __slots__ = ('parsed', 'command', 'args', 'flags', 'parent',
        'extra', 'stdout', 'stderr', 'suggest', 'styling', 'help', 'standalone_mode')

    extra:   Dict[str, Any]
    stdout:  AnyIO
    stderr:  AnyIO
    styling: Styling

    def __init__(self,
        parsed:  'ParsedCmd',
        parent:  Optional['Context']      = None,
        help:    Optional['Help']         = None,
        stdout:  Optional[AnyIO]          = None,
        stderr:  Optional[AnyIO]          = None,
        suggest: Optional['SuggestorCLS'] = None,
        styling: Optional[Styling]        = None,
        standalone_mode: bool             = True,
    ):
        """
        :param parsed:          parsed command contents
        :param parent:          parent context of parent action
        :param help:            help formatter object
        :param stdout:          standard output file
        :param stderr:          standard error output file
        :param suggest:         auto-complete suggestion handler type
        :param styling:         format styling object
        :param standalone_mode: label if actions are running in standalone
        """
        self.parsed  = parsed
        self.command = parsed.source
        self.args    = parsed.args
        self.flags   = parsed.flags
        self.parent  = parent
        self.extra   = parent.extra if parent else {}
        self.stdout  = stdout or sys.stdout
        self.stderr  = stderr or sys.stderr
        self.suggest = suggest or Suggestor
        self.styling = styling or AnsiTermStyle()
        self.help    = help or Help(styling)
        self.standalone_mode = standalone_mode

    def __repr__(self) -> str:
        return f'Context(args={self.args}, flags={self.flags}, extra={self.extra})'

    @property
    def path(self) -> List['Command']:
        """
        retrieve heigharchical path of commands executed
        """
        path: List[Command] = []
        ctx:  Optional[Context] = self
        while ctx is not None:
            path.insert(0, ctx.command)
            ctx = ctx.parent if ctx else None
        return path

    @property
    def invoked_subcommands(self) -> Optional[List[str]]:
        """
        retrieve list of subcommands to be invoked next
        """
        commands = list(self.parsed.commands.keys())
        return commands if commands else None

    def suggestor(self) -> 'Suggestor':
        """
        generate auto-complete suggestor instance
        """
        return self.suggest(self.path[0])

    def exit(self, exit_code: int = 0):
        """
        force exit command execution early
        """
        raise Exit(exit_code)

    def _get(self, dict: Dict[str, Any], name: str, ctype: Optional[Type[T]]) -> T:
        """
        retrieve a value from a dictionarry and validate its type if given
        """
        value = dict[name]
        if ctype is not None and not typecheck(value, ctype):
            t1 = type(value).__name__
            t2 = ctype.__name__
            raise TypeError(f'{name!r} ({t1}) is not a {t2}')
        return value

    def get(self, name: str,
        ctype: Optional[Type[T]] = None, default: Any = MISSING) -> T:
        """
        retrieve a value from the first relevant context and valdiate its type

        heigharchy: arguments -> flags -> extra -> default

        :param name:    name of value to retrieve
        :param ctype:   type to validate
        :param default: default value if value is missing
        """
        value = self.args.get(name, MISSING)
        value = self.flags.get(name, MISSING) if value is MISSING else value
        value = self.extra.get(name, MISSING) if value is MISSING else value
        value = default if value is MISSING else value
        if value is MISSING:
            if ctype is not None and issubclass(ctype, self.__class__):
                return cast(T, self)
            raise KeyError(name)
        if ctype is not None and not typecheck(value, ctype):
            t1 = type(value).__name__
            t2 = ctype.__name__
            raise TypeError(f'{name!r} ({t1}) is not a {t2}')
        return value

    def get_arg(self, name: str, ctype: Optional[Type[T]] = None) -> T:
        """
        retrieve argument value of a specific name and validate type

        :param name:  name of argument
        :param ctype: type annotation/validation
        """
        return self._get(self.args, name, ctype)

    def get_flag(self, name: str, ctype: Type[T]) -> T:
        """
        retrieve flag/option value of a specific name and validate type

        :param name:  name of flag/option
        :param ctype: type annotation/validation
        """
        return self._get(self.flags, name, ctype)

    def get_extra(self, name: str, ctype: Type[T]) -> T:
        """
        retrieve extra value of a specific name and validate type

        :param name:  name of extra value
        :param ctype: type annotation/validation
        """
        return self._get(self.extra, name, ctype)

    def stack(self, parsed: 'ParsedCmd') -> 'Context':
        """
        generate child context object using parsed context
        """
        context = self.__class__(
            parsed=parsed,
            parent=self,
            stdout=self.stdout,
            stderr=self.stderr,
            suggest=self.suggest,
            styling=self.styling,
            help=self.help)
        context_stack.get().append(context)
        return context

#** Imports **#
from .cmd import Command
from .help import Help
from .errors import Exit
from .parser import ParsedCmd
from .suggest import Suggestor, SuggestorCLS
