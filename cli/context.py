"""
CLI Action Context
"""
import sys
from contextvars import ContextVar
from contextlib import contextmanager
from typing import (
    Any, BinaryIO, Dict, Generator, List, Literal, Optional, TextIO,
    Type, Union, cast, overload)

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

#** Classes **#

class MISSING:
    pass

class Context:
    """
    """
    __slots__ = ('parsed', 'command', 'args', 'flags', 'parent',
        'extra', 'stdout', 'stderr', 'styling', 'help')

    def __init__(self,
        parsed:  'ParsedCmd',
        parent:  Optional['Context'] = None,
        help:    Optional[Help]      = None,
        stdout:  Optional[AnyIO]     = None,
        stderr:  Optional[AnyIO]     = None,
        styling: Optional[Styling]   = None,
    ):
        self.parsed  = parsed
        self.command = parsed.source
        self.args    = parsed.args
        self.flags   = parsed.flags
        self.parent  = parent
        self.extra   = parent.extra if parent else {}
        self.stdout  = stdout or sys.stdout
        self.stderr  = stderr or sys.stderr
        self.styling = styling or AnsiTermStyle()
        self.help    = help or Help(styling)

    def __repr__(self) -> str:
        """
        """
        return f'Context(args={self.args}, flags={self.flags}, extra={self.extra})'

    @property
    def path(self) -> List['Command']:
        """
        """
        path = []
        ctx  = self
        while ctx is not None:
            path.insert(0, ctx.command)
            ctx = ctx.parent if ctx else None
        return path

    @property
    def invoked_subcommands(self) -> Optional[List[str]]:
        """
        """
        commands = list(self.parsed.commands.keys())
        return commands if commands else None

    def _get(self, dict: Dict[str, Any], name: str, ctype: Optional[Type[T]]) -> T:
        """
        """
        value = dict[name]
        if ctype is not None and not isinstance(value, ctype):
            t1 = type(value).__name__
            t2 = ctype.__name__
            raise TypeError(f'{name!r} ({t1}) is not a {t2}')
        return value

    def get(self, name: str,
        ctype: Optional[Type[T]] = None, default: Any = MISSING) -> T:
        """
        """
        value = self.args.get(name, MISSING)
        value = self.flags.get(name, MISSING) if value is MISSING else value
        value = self.extra.get(name, MISSING) if value is MISSING else value
        value = default if value is MISSING else value
        if value is MISSING:
            if ctype is not None and issubclass(ctype, self.__class__):
                return cast(T, self)
            raise KeyError(name)
        if ctype is not None and not isinstance(value, ctype):
            t1 = type(value).__name__
            t2 = ctype.__name__
            raise TypeError(f'{name!r} ({t1}) is not a {t2}')
        return value

    def get_arg(self, name: str, ctype: Optional[Type[T]] = None) -> T:
        """
        """
        return self._get(self.args, name, ctype)

    def get_flag(self, name: str, ctype: Type[T]) -> T:
        """
        """
        return self._get(self.flags, name, ctype)

    def get_extra(self, name: str, ctype: Type[T]) -> T:
        """
        """
        return self._get(self.extra, name, ctype)

    def stack(self, parsed: 'ParsedCmd') -> 'Context':
        """
        """
        context = self.__class__(
            parsed=parsed,
            parent=self,
            stdout=self.stdout,
            stderr=self.stderr,
            styling=self.styling,
            help=self.help)
        context_stack.get().append(context)
        return context

#** Imports **#
from .cmd import Command
from .help import Help
from .parser import ParsedCmd
