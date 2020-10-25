"""
application definition which determines behavior and handling of arguments
"""
import sys
import asyncio
from io import RawIOBase
from dataclasses import dataclass, field, InitVar
from typing import Callable, Optional, List

from .flag import Flags
from .context import Context
from .command import Action, Commands, CommandBase, Command
from .help import help_action, help_flag, help_command
from .parser import run_app

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

#: defintion for command-not-found error
NotFoundFunc = Callable[[Context, Command, str], None]

#** Classes **#

@dataclass
class App(CommandBase):
    """application determines handling of arguments and stores metadata"""

    name:        str
    usage:       str
    version:     str                 = '0.0.1'
    argsusage:   Optional[str]       = None
    description: Optional[str]       = None
    flags:       Flags               = field(default_factory=list, repr=False)
    commands:    Commands            = field(default_factory=list, repr=False)

    email:     Optional[str]       = None
    authors:   Optional[List[str]] = None
    copyright: Optional[str]       = None

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
        before: Action,
        action: Action,
        after:  Action,
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
        """"""
        print(f'Incorrect Usage: {error}\n', file=ctx.app.err_writer)
        help_action(ctx, cmd)
        raise SystemExit(4)

    def exit_with_error(ctx: Context, cmd: Command, err: str, code: int):
        """"""
        print(f"App-Error: {err}", file=ctx.app.err_writer)
        raise SystemExit(code)

    def not_found_error(ctx: Context, cmd: Command, arg: str):
        """"""
        if arg.startswith('-'):
            msg = f'Command: {cmd.name}, Invalid Flag: {arg}'
        else:
            msg = f'No Help topic for: {arg}'
        print(msg, file=ctx.app.err_writer)
        raise SystemExit(3)

    def run(self, args: List[str] = sys.argv) -> Optional[asyncio.Future]:
        """
        """
        loop   = asyncio.get_event_loop()
        future = asyncio.ensure_future(run_app(self, args))
        if self.run_async:
            return future
        loop.run_until_complete(future)
