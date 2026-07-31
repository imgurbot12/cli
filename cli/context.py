"""
CLI Action Context
"""
import sys
import asyncio
import contextlib
from contextvars import ContextVar
from types import TracebackType
from typing import (
    Any, AsyncGenerator, Awaitable, BinaryIO, Callable, Dict, Generator, List, Literal,
    Optional, TextIO, Type, TypeVar, Union, cast, overload)
from typing_extensions import Annotated, get_origin, get_args

from . import T
from .style import Styling, AnsiTermStyle

#** Variables **#
__all__ = [
    'AnyIO',
    'MISSING',

    'new_context',
    'new_context_async',
    'get_current_context',

    'Context',
]

SyncCtx  = TypeVar('SyncCtx', bound=contextlib.AbstractContextManager)
AsyncCtx = TypeVar('AsyncCtx', bound=contextlib.AbstractAsyncContextManager)

AnyIO = Union[TextIO, BinaryIO]

SyncExitFunc = Callable[[
    Optional[Type[Exception]],
    Optional[Exception],
    Optional[TracebackType],
], Optional[bool]]

AsyncExitFunc = Callable[[
    Optional[Type[Exception]],
    Optional[Exception],
    Optional[TracebackType],
], Awaitable[Optional[bool]]]

ExitFunc = Union[AsyncExitFunc, SyncExitFunc]

context_stack: ContextVar[List['Context']] = ContextVar('context_stack')

#** Functions **#

@contextlib.contextmanager
def new_context(
    parsed: 'ParsedCmd', **kwargs) -> Generator['Context', None, None]:
    """
    start new context object stack for the current cli job
    """
    close   = kwargs.get('loop') is None
    context = Context(parsed, **kwargs)
    token   = context_stack.set([context])
    try:
        yield context
        context.close(None, None, None)
    except Exception as e:
        context.close(e.__class__, e, e.__traceback__)
    finally:
        context_stack.reset(token)
        if close:
            context.loop.close()

@contextlib.asynccontextmanager
async def new_context_async(
    parsed: 'ParsedCmd', **kwargs) -> AsyncGenerator['Context', None]:
    """
    asyncly start new context object stack for the current cli job
    """
    kwargs.setdefault('loop', asyncio.get_running_loop())
    context = Context(parsed, **kwargs)
    token   = context_stack.set([context])
    try:
        yield context
        await context.close_async(None, None, None)
    except Exception as e:
        await context.close_async(e.__class__, e, e.__traceback__)
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
        'extra', 'stdout', 'stderr', 'suggest', 'styling', 'help',
        'standalone_mode', 'loop', 'closed', 'closers')

    extra:   Dict[str, Any]
    stdout:  AnyIO
    stderr:  AnyIO
    styling: Styling
    closers: List[ExitFunc]
    loop:    asyncio.AbstractEventLoop

    def __init__(self,
        parsed:  'ParsedCmd',
        parent:  Optional['Context']      = None,
        help:    Optional['Help']         = None,
        stdout:  Optional[AnyIO]          = None,
        stderr:  Optional[AnyIO]          = None,
        suggest: Optional['SuggestorCLS'] = None,
        styling: Optional[Styling]        = None,
        extra:   Optional[Dict[str, Any]] = None,

        loop:            Optional[asyncio.AbstractEventLoop] = None,
        standalone_mode: bool                                = True,
    ):
        """
        :param parsed:          parsed command contents
        :param parent:          parent context of parent action
        :param help:            help formatter object
        :param stdout:          standard output file
        :param stderr:          standard error output file
        :param suggest:         auto-complete suggestion handler type
        :param styling:         format styling object
        :param extra:           extra data
        :param standalone_mode: label if actions are running in standalone
        :param loop:            event-loop to use for action/callback processing
        """
        self.parsed  = parsed
        self.command = parsed.source
        self.args    = parsed.args
        self.flags   = parsed.flags
        self.parent  = parent
        self.extra   = extra or (parent.extra if parent else {})
        self.stdout  = stdout or sys.stdout
        self.stderr  = stderr or sys.stderr
        self.suggest = suggest or Suggestor
        self.styling = styling or AnsiTermStyle()
        self.help    = help or Help(styling)
        self.standalone_mode = standalone_mode
        self.loop    = loop or (parent.loop if parent else asyncio.new_event_loop())
        self.closed  = False
        self.closers = []

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

    def on_close(self, closer: ExitFunc):
        """
        add exit function to be triggered on cleanup (LIFO queue)
        """
        self.closers.insert(0, closer)

    def with_resource(self, manager: SyncCtx) -> SyncCtx:
        """
        bind context-manager to context to ensure closing on exit
        """
        manager.__enter__()
        self.on_close(manager.__exit__)
        return manager

    async def with_async_resource(self, manager: AsyncCtx) -> AsyncCtx:
        """
        bind async context-manager to context to ensure closing on exit
        """
        await manager.__aenter__()
        self.on_close(manager.__aexit__)
        return manager

    def close(self,
        exc_type: Optional[Type[Exception]],
        exc_val:  Optional[Exception],
        exc_tb:   Optional[TracebackType],
    ):
        """
        run all configured closers
        """
        if self.closed:
            return
        for closer in self.closers:
            co = closer(exc_type, exc_val, exc_tb)
            call_async(co, loop=self.loop)
        self.closed = True

    async def close_async(self,
        exc_type: Optional[Type[Exception]],
        exc_val:  Optional[Exception],
        exc_tb:   Optional[TracebackType],
    ):
        """
        run all configured closers asyncly
        """
        if self.closed:
            return
        for closer in self.closers:
            func = wrap_async(closer)
            await func(exc_type, exc_val, exc_tb)
        self.closed = True

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

        loop  = asyncio._get_running_loop()
        close = context.close if loop is None else context.close_async
        self.on_close(close)
        return context

#** Imports **#
from .cmd import Command
from .help import Help
from .errors import Exit
from .parser import ParsedCmd
from .suggest import Suggestor, SuggestorCLS
from .wraps import call_async, wrap_async
