"""
CLI Action Context
"""
import sys
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Any, BinaryIO, Dict, Generator, List, Literal, Optional, TextIO, Type, Union, overload

from . import T

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
        'extra', 'stdout', 'stderr')

    def __init__(self,
        parsed: 'ParsedCmd',
        parent: Optional['Context'] = None,
        stdout: Optional[AnyIO] = None,
        stderr: Optional[AnyIO] = None,
    ):
        self.parsed  = parsed
        self.command = parsed.source
        self.args    = parsed.args
        self.flags   = parsed.flags
        self.parent  = parent
        self.extra   = parent.extra if parent else {}
        self.stdout  = stdout or sys.stdout
        self.stderr  = stderr or sys.stderr

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
        context = self.__class__(parsed, self, self.stdout, self.stderr)
        context_stack.get().append(context)
        return context

#** Imports **#
from .parser import ParsedCmd
