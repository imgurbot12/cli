"""
application definition which determines behavior and handling of arguments
"""
import sys
import asyncio
from io import RawIOBase
from dataclasses import dataclass, field, InitVar
from typing import Callable, Optional, List, Coroutine

from .flag import Flags
from .context import Context
from .command import Action, Commands, CommandBase, Command
from .help import help_action, help_flag, help_command
from .parser import run_app, EX_USAGE, EX_UNAVAILABLE

#** Variables **#
__all__ = [
    'UsageErrorFunc',
    'ExitErrorFunc',
    'NotFoundFunc',

    'App'
]

#: definition for usage-error function
UsageErrorFunc = Callable[[Context, Command, str], None]

#: definition for exit-error function
ExitErrorFunc  = Callable[[Context, Command, str, int], None]

#: defintion for command-not-found function
NotFoundFunc = Callable[[Context, Command, str], None]

#** Functions **#

def get_event_loop() -> asyncio.BaseEventLoop:
    """retrieve asyncio event loop"""
    try:
        loop = asyncio.get_running_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

#** Classes **#

@dataclass
class App(CommandBase):
    """
    application determines handling of arguments and stores metadata

    :param name:              name of application
    :param usage:             specified usage description
    :param version:           symantic version number
    :param argsusage:         argument usage description
    :param description:       long general description
    :param flags:             configured application flags
    :param commands:          configured application subcommands
    :param allow_parent:      allow parent command to run when children are
    :param authors:           list of author names
    :param email:             primary contact email
    :param copyright:         copyright info summary
    :param writer:            app standard output buffer
    :param err_writer:        app error output buffer
    :param help_app_template: jinja2 app help template
    :param help_cmd_template: jinja2 cmd help template
    :param before:            before-action function
    :param action:            primary app action function
    :param after:             after-action function
    :param on_usage_error:    override usage-error function
    :param exit_with_error:   override exit-with-error function
    :param not_found_error:   override not-found-error function
    :param run_async:         return co-routine on run if true
    """

    name:         str
    usage:        str
    version:      str           = '0.0.1'
    argsusage:    Optional[str] = None
    description:  Optional[str] = None
    flags:        Flags         = field(default_factory=list, repr=False)
    commands:     Commands      = field(default_factory=list, repr=False)
    allow_parent: bool          = False

    authors:   List[str]     = field(default_factory=list)
    email:     Optional[str] = None
    copyright: Optional[str] = None

    writer:     RawIOBase = field(default=sys.stdout, repr=False)
    err_writer: RawIOBase = field(default=sys.stderr, repr=False)

    help_app_template: Optional[str] = field(default=None, repr=False)
    help_cmd_template: Optional[str] = field(default=None, repr=False)

    before: InitVar[Action]
    action: InitVar[Action]
    after:  InitVar[Action]

    on_usage_error:  InitVar[UsageErrorFunc]
    exit_with_error: InitVar[ExitErrorFunc]
    not_found_error: InitVar[NotFoundFunc]

    run_async: bool = False

    def __post_init__(self,
        before:          Action,
        action:          Action,
        after:           Action,
        on_usage_error:  UsageErrorFunc,
        exit_with_error: ExitErrorFunc,
        not_found_error: NotFoundFunc,
    ):
        """make modifications to inputs after init"""
        super().__post_init__(before, action, after)
        self.on_usage_error  = on_usage_error or self.on_usage_error
        self.exit_with_error = exit_with_error or self.exit_with_error
        self.not_found_error = not_found_error or self.not_found_error
        # add help command/flag to system
        self.flags.insert(0, help_flag)
        self.commands.insert(0, help_command)

    def on_usage_error(ctx: Context, cmd: Command, error: str):
        """
        handles usage errors during parsing or from context

        :param ctx: context of command that raised a usage error
        :param cmd: command that raised a usage error
        :param err: message of usage error raised
        """
        print(f'Incorrect Usage: {error}\n', file=ctx.app.err_writer)
        help_action(ctx, cmd)
        raise SystemExit(EX_USAGE)

    def exit_with_error(ctx: Context, cmd: Command, err: str, code: int):
        """
        handles unrecoverable exceptions that must lead to complete exit

        :param ctx:  context of command that raised an exit error
        :param cmd:  command that raised an exit error
        :param err:  message of exit error
        :param code: exit-code of exit error
        """
        print(f"App-Error: {err}", file=ctx.app.err_writer)
        raise SystemExit(code)

    def not_found_error(ctx: Context, cmd: Command, arg: str):
        """
        handles issues with invalid flags and bad command paths on help

        :param ctx: context of command that raised a not-found error
        :param cmd: command that raised a not found error
        :param arg: argument that was not found
        """
        if arg.startswith('-'):
            msg = f'Command: {cmd.name}, Invalid Flag: {arg}'
        else:
            msg = f'No Help topic for: {arg}'
        print(msg, file=ctx.app.err_writer)
        raise SystemExit(EX_UNAVAILABLE)

    def run(self, 
        args:      Optional[List[str]] = None,
        run_async: Optional[bool]      = None,
    ) -> Optional[Coroutine[None, None, None]]:
        """
        run the relevant actions based on the arguments given and app defintions

        :param args:      args being parsed and passed into relevant actions
        :param run_async: override app run_async setting
        :return:          asyncio coroutine if run_async=True
        """
        args   = args if args is not None else sys.argv.copy()
        future = run_app(self, args)
        rasync = run_async if run_async is not None else self.run_async
        if rasync:
            return future
        # generate new loop and ensure closure reguardless of error
        try:
            loop = get_event_loop()
            loop.run_until_complete(future)
        finally:
            loop.close()

