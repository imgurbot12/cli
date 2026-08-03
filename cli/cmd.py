"""
CLI Command Implementation
"""
import sys
import asyncio
from collections import UserList
from typing import (
    Any, Awaitable, Callable, Dict, List, Literal, Optional, Type,
    TypeVar, Union, overload)
from typing_extensions import NoReturn, TypedDict, Unpack

from .arg import Args
from .flag import Flags
from .style import Styling

#** Variables **#
__all__ = ['Action', 'Command', 'Commands']

C           = TypeVar('C', bound='Command')
Commands    = List['Command']

SyncAction  = Callable[..., Any]
AsyncAction = Callable[..., Awaitable[Any]]
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
    extra:   Dict[str, Any]
    loop:    asyncio.AbstractEventLoop

class ResultList(UserList):
    """
    Special list subtype to denote a result collection
    """

class Results:
    """
    Command Return Result Accumulator
    """
    __slots__ = ('results', )

    def __init__(self):
        self.results = ResultList()

    def add_result(self, result: Any):
        """
        add a new result to the collection
        """
        if result is None:
            return
        if isinstance(result, ResultList):
            self.results.extend(result)
        else:
            self.results.append(result)

    def result(self) -> Any:
        """
        return finalized result from collection
        """
        if not self.results:
            return
        if len(self.results) == 1:
            return self.results[0]
        return self.results

class Command:
    """
    CLI Command Configuration Object
    """
    __slots__ = (
        'name', 'about', 'version', 'authors', 'category', 'hidden',
        'suggest', 'args', 'flags', 'commands', 'aliases', 'action',
        'chain', 'repeat', 'invoke_without_command',)

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
        chain:                  bool                = False,
        repeat:                 bool                = False,
        invoke_without_command: bool                = False,
    ):
        """
        :param name:                   namme of command
        :param about:                  description of command
        :param version:                version of command
        :param authors:                authors of command / program
        :param category:               category linked to command
        :param hidden:                 hide command if true
        :param suggest:                allow inclusion for suggestion
        :param args:                   configured command arguments
        :param flags:                  configured command options/flags
        :param commands:               configured sub-commands
        :param aliases:                aliases of the command
        :param action:                 function to call on command
        :param chain:                  allow chaining subcommands
        :param repeat:                 allow repeating the same command (in chain)
        :param invoke_without_command: allow command to run without subcommand
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
        self.chain                  = chain
        self.repeat                 = repeat
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
    ) -> Any:
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
        list of name and aliases of command
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
        chain:    bool          = False,
        repeat:   bool          = False,
        cls:      None          = None,
    ) -> Callable[[Callable], 'Command']:
        ...

    @overload
    def command(self,
        name:     Optional[str] = None,
        about:    Optional[str] = None,
        category: Optional[str] = None,
        hidden:   bool          = False,
        chain:    bool          = False,
        repeat:   bool          = False,
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
        chain:    bool                     = False,
        repeat:   bool                     = False,
        cls:      Optional[Type[C]]        = None,
    ) -> Union[Callable[[Action], 'Command'], C, 'Command']:
        """
        subcommand function wrapper

        :param name:     name of command
        :param about:    description of command
        :param category: category linked to command
        :param hidden:   hide this command if true
        :param chain:    allow chaining subcommands
        :param repeat:   allow repeating the same command (in chain)
        :param cls:      command subclass type
        """
        cname = name if isinstance(name, str) else None
        def wrapper(action: Action) -> Command:
            cmd = into_command(action, cls or Command)
            cmd.name     = cname or cmd.name
            cmd.about    = about or cmd.about
            cmd.category = category or cmd.category
            cmd.hidden   = hidden or cmd.hidden
            cmd.chain    = chain or cmd.chain
            cmd.repeat   = repeat or cmd.repeat
            self.commands.append(cmd)
            return cmd
        return wrapper(name) if callable(name) else wrapper

    def _validate_args(self):
        """
        validate arguments and their configuration in command
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
        validate flags and their configuration in command
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
        validate subcommands and their configuration in command
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
        validate this command and its configuration
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
        parse the given arguments and return the parsed context object

        :param args:            arguments to parse
        :param standalone_mode: exit after completion if true
        :param kwargs:          additional contextual arguments
        :return:                parsed command structure
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
        check if the next command action should run
        """
        is_group = len(self.commands) > 0
        if is_group:
            return self.invoke_without_command \
                or len(context.parsed.commands) > 0
        return True

    def run_with(self, context: 'Context', action: Optional[SyncAction] = None):
        """
        run this command with the specified context/action

        :param context: command runtime context
        :param action:  command action override
        """
        act    = action or self.action
        result = Results()
        if act is not None:
            if self._check_run(context):
                func = wrap_ctx(act)
                co   = func(context)
                ret  = call_async(co, loop=context.loop)
                result.add_result(ret)
        for plist in context.parsed.commands.values():
            for parsed in plist:
                context = context.stack(parsed)
                ret     = context.command.run_with(context)
                result.add_result(ret)
        return result.result()

    async def run_with_async(self,
        context: 'Context', action: Optional[AsyncAction] = None):
        """
        run this command with the specified context/action asyncly

        :param context: command runtime context
        :param action:  command action override
        """
        act    = action or self.action
        result = Results()
        if act is not None:
            if self._check_run(context):
                async_act = wrap_async(act)
                ret       = await wrap_ctx(async_act)(context)
                result.add_result(ret)
        for plist in context.parsed.commands.values():
            for parsed in plist:
                context = context.stack(parsed)
                ret     = await context.command.run_with_async(context)
                result.add_result(ret)
        return result.result()

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
    ) -> Any:
        ...

    def run(self,
        args: RunArgs = None,
        *,
        standalone_mode: bool = True,
        **kwargs: Unpack[RunKwargs]
    ) -> Any:
        """
        parse the given arguments and run the relevant command actions

        :param args:            arguments to parse
        :param standalone_mode: exit after completion if true
        """
        code   = 0
        parsed = self.parse(args, standalone_mode=standalone_mode, **kwargs)
        result = None
        with new_context(parsed,
            standalone_mode=standalone_mode, **kwargs) as context:
            try:
                result = self.run_with(context)
            except Exit as err:
                if not standalone_mode:
                    raise err
                code = err.exit_code
        if standalone_mode:
            sys.exit(code)
        return result

    async def run_async(self,
        args: RunArgs = None, **kwargs: Unpack[RunKwargs]) -> Any:
        """
        parse the given arguments and run the relevant command actions asyncly

        :param args:            arguments to parse
        :param standalone_mode: exit after completion if true
        """
        parsed = self.parse(args, standalone_mode=False, **kwargs)
        async with new_context_async(parsed,
            standalone_mode=False, **kwargs) as context:
            return await self.run_with_async(context)

#** Imports **#
from .context import AnyIO, Context, new_context, new_context_async
from .errors import CliError, Exit
from .help import Help
from .parser import Parser, ParsedCmd
from .suggest import SuggestorCLS
from .wraps import call_async, into_command, wrap_ctx, wrap_async
from .utils import echo
