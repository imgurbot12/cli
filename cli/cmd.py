"""
CLI Command Implementation
"""
import sys
import inspect
import asyncio
from typing import (
    Awaitable, Callable, Coroutine, Dict, List, Literal, Optional, Type,
    TypeVar, Union, cast, overload)
from typing_extensions import NoReturn, TypedDict, Unpack

from .arg import Args
from .flag import Flags
from .style import Styling

#** Variables **#
__all__ = ['Action', 'Command', 'Commands']

C           = TypeVar('C', bound='Command')
Commands    = List['Command']

SyncAction  = Callable[..., None]
AsyncAction = Callable[..., Awaitable[None]]
Action      = Union[SyncAction, AsyncAction]

RunArgs = Optional[List[str]]

#** Classes **#

class RunKwargs(TypedDict, total=False):
    help:    'Help'
    parser:  Type['Parser']
    stdout:  'AnyIO'
    stderr:  'AnyIO'
    suggest: 'SuggestorCLS'
    styling: Styling

class Command:
    """
    """
    __slots__ = (
        'name', 'about', 'version', 'authors', 'category', 'hidden',
        'suggest', 'args', 'flags', 'commands', 'aliases', 'action',
        'invoke_without_command',)

    def __init__(self,
        name:                   str,
        about:                  Optional[str]       = None,
        version:                Optional[str]       = None,
        authors:                Optional[List[str]] = None,
        category:               Optional[str]       = None,
        hidden:                 bool                = False,
        suggest:                bool                = True,
        args:                   Optional[Args]      = None,
        flags:                  Optional[Flags]     = None,
        commands:               Optional[Commands]  = None,
        aliases:                Optional[List[str]] = None,
        action:                 Optional[Action]    = None,
        invoke_without_command: bool                = False,
    ):
        """
        """
        self.name                   = name
        self.about                  = about
        self.version                = version
        self.authors                = authors
        self.category               = category or '*'
        self.hidden                 = hidden
        self.suggest                = suggest
        self.args                   = args or []
        self.flags                  = flags or []
        self.commands               = commands or []
        self.aliases                = aliases or []
        self.action                 = action
        self.invoke_without_command = invoke_without_command

    def __repr__(self) -> str:
        return f'Command(name={self.name}, aliases={self.aliases!r})'

    @overload
    def __call__(self,
        args: RunArgs = None,
        *,
        standalone_mode: Literal[True] = True,
        **kwargs: Unpack[RunKwargs]
    ) -> NoReturn:
        ...

    @overload
    def __call__(self,
        args: RunArgs = None,
        *,
        standalone_mode: Literal[False] = False,
        **kwargs: Unpack[RunKwargs]
    ) -> None:
        ...

    def __call__(self,
        args: RunArgs = None,
        *,
        standalone_mode: bool = True,
        **kwargs: Unpack[RunKwargs]
    ):
        return self.run(args, #type: ignore[call-overload]
            standalone_mode=standalone_mode, **kwargs)

    def variants(self) -> List[str]:
        """
        """
        return [self.name, *self.aliases]

    @property
    def categories(self) -> Dict[str, List['Command']]:
        """
        Organize sub-commands into categories

        :return: dictionary of category names associated w/ sub-commands
        """
        categories: Dict[str, List[Command]] = {}
        for cmd in self.commands:
            categories.setdefault(cmd.category, [])
            categories[cmd.category].append(cmd)
        return categories

    def visible_flags(self) -> Flags:
        """
        Retrieve visable flags

        :return: all non hidden flags attached to this command
        """
        return [f for f in self.flags if not f.hidden]

    def visible_commands(self, category: Optional[str] = None) -> Commands:
        """
        Retrieve visable commands (of given category if specified)

        :param category: only return commands of the given category if specified
        :return:         commands not hidden
        """
        commands = [c for c in self.commands if not c.hidden]
        if category is not None:
            commands = [c for c in commands if c.category == category]
        return commands

    def visible_categories(self) -> List[str]:
        """
        retrieve category names
        """
        return [category for category in self.categories.keys()]

    @overload
    def command(self,
        name:     Optional[str] = None,
        about:    Optional[str] = None,
        category: Optional[str] = None,
        hidden:   bool          = False,
        cls:      None          = None,
    ) -> Callable[[Callable], 'Command']:
        ...

    @overload
    def command(self,
        name:     Optional[str] = None,
        about:    Optional[str] = None,
        category: Optional[str] = None,
        hidden:   bool          = False,
        *, cls: Type[C],
    ) -> Callable[[Callable], C]:
        ...

    @overload
    def command(self, name: Callable) -> 'Command':
        ...

    def command(self,
        name:     Union[str, Action, None] = None,
        about:    Optional[str]            = None,
        category: Optional[str]            = None,
        hidden:   bool                     = False,
        cls:      Optional[Type[C]]        = None,
    ) -> Union[Callable[[Action], 'Command'], C, 'Command']:
        """
        """
        cname = name if isinstance(name, str) else None
        def wrapper(action: Action) -> Command:
            cmd = into_command(action, cls or Command)
            cmd.name     = cname or cmd.name
            cmd.about    = about or cmd.about
            cmd.category = category or cmd.category
            cmd.hidden   = hidden or cmd.hidden
            self.commands.append(cmd)
            return cmd
        return wrapper(name) if callable(name) else wrapper

    def _validate_args(self):
        """
        """
        reserved = set()
        repeated = None
        for n, arg in enumerate(self.args, 0):
            if arg.repeat:
                if repeated is not None:
                    raise ValueError(
                        f'{self.name} arg({n}) cannot also be repeated.')
                repeated = arg.name
            if arg.name not in reserved:
                reserved.add(arg.name)
                continue
            raise ValueError(
                f'{self.name} arg({n}) has duplicate argument {arg.name!r}')

    def _validate_flags(self):
        """
        """
        reserved = set()
        for n, flag in enumerate(self.flags, 0):
            if flag.name in reserved:
                raise ValueError(
                    f'{self.name} flag({n}) has duplicate name {flag.name!r}')
            reserved.add(flag.name)
            for var in flag.variants():
                if var in reserved:
                    raise ValueError(
                        f'{self.name} flag({n}) has duplicate flag {var!r}')
                reserved.add(var)

    def _validate_commands(self):
        """
        """
        reserved = set()
        for n, cmd in enumerate(self.commands, 0):
            if cmd.name in reserved:
                raise ValueError(
                    f'{self.name} command({n}) has duplicate name {cmd.name!r}')
            reserved.add(cmd.name)
            for alias in cmd.aliases:
                if alias in reserved:
                    raise ValueError(
                        f'{self.name} command({n}) has duplicate alias {alias!r}')
                reserved.add(alias)

    def validate(self):
        """
        """
        self._validate_args()
        self._validate_flags()
        self._validate_commands()

    def parse(self,
        args: RunArgs = None,
        *,
        standalone_mode: bool = True,
        **kwargs: Unpack[RunKwargs]
    ) -> 'ParsedCmd':
        """
        """
        help   = kwargs.get('help') or Help()
        parser = kwargs.get('parser') or Parser
        engine = (parser or Parser)(self, help=help)
        try:
            return engine.parse(args or sys.argv[1:])
        except CliError as err:
            if not standalone_mode:
                raise err
            stderr = kwargs.get('stderr') or sys.stderr
            echo(err.show(help), file=stderr)
            sys.exit(err.exit_code)

    def _check_run(self, context: 'Context') -> bool:
        """
        """
        is_group = len(self.commands) > 0
        if is_group:
            return self.invoke_without_command \
                or len(context.parsed.commands) > 0
        return True

    def run_with(self, context: 'Context', action: Optional[SyncAction] = None):
        """
        """
        act = action or self.action
        if act is not None:
            if self._check_run(context):
                func = wrap_ctx(act)
                co   = func(context)
                if inspect.isawaitable(co):
                    asyncio.run(cast(Coroutine[None, None, None], co))
        for parsed in context.parsed.commands.values():
            context = context.stack(parsed)
            context.command.run_with(context)

    async def run_with_async(self,
        context: 'Context', action: Optional[AsyncAction] = None):
        """
        """
        act = action or self.action
        if act is not None:
            if self._check_run(context):
                async_act = wrap_async(act)
                await wrap_ctx(async_act)(context)
        for parsed in context.parsed.commands.values():
            context = context.stack(parsed)
            await context.command.run_with_async(context)

    @overload
    def run(self,
        args: RunArgs = None,
        *,
        standalone_mode: Literal[True] = True,
        **kwargs: Unpack[RunKwargs]
    ) -> NoReturn:
        ...

    @overload
    def run(self,
        args: RunArgs = None,
        *,
        standalone_mode: Literal[False] = False,
        **kwargs: Unpack[RunKwargs]
    ) -> None:
        ...

    def run(self,
        args: RunArgs = None,
        *,
        standalone_mode: bool = True,
        **kwargs: Unpack[RunKwargs]
    ):
        """
        """
        code   = 0
        result = self.parse(args, standalone_mode=standalone_mode, **kwargs)
        with new_context(result,
            standalone_mode=standalone_mode, **kwargs) as context:
            try:
                self.run_with(context)
            except Exit as err:
                if not standalone_mode:
                    raise err
                code = err.exit_code
        if standalone_mode:
            sys.exit(code)

    async def run_async(self,
        args: RunArgs = None, **kwargs: Unpack[RunKwargs]):
        """
        """
        result = self.parse(args, standalone_mode=False, **kwargs)
        with new_context(result, standalone_mode=False, **kwargs) as context:
            await self.run_with_async(context)

#** Imports **#
from .context import AnyIO, Context, new_context
from .errors import CliError, Exit
from .help import Help
from .parser import Parser, ParsedCmd
from .suggest import SuggestorCLS
from .wraps import into_command, wrap_ctx, wrap_async
from .utils import echo
