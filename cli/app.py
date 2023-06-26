"""
CLI Application Definition/Implementation
"""
import sys
import asyncio
from typing import Callable, Optional, List, TextIO

from .abc import *
from .flag import Flags
from .command import Command
from .help import help_action, help_flag, help_command
from .parser import run_app, EX_USAGE, EX_UNAVAILABLE, EX_CONFIG

#** Variables **#
__all__ = [
    'UsageErrorFunc',
    'ExitErrorFunc',
    'NotFoundFunc',

    'App'
]

#: definition for usage-error function
UsageErrorFunc = Callable[[UsageError], None]

#: definition for exit-error function
ExitErrorFunc  = Callable[[ExitError], None]

#: defintion for command-not-found function
NotFoundFunc = Callable[[NotFoundError], None]

#** Functions **#

def get_event_loop() -> asyncio.AbstractEventLoop:
    """retrieve asyncio event loop"""
    try:
        loop = asyncio.get_running_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

#** Classes **#

class App(Command, AbsApplication):
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

    def __init__(self,
        name:              str,
        version:           str                      = '0.0.1',
        usage:             Optional[str]            = None,
        argsusage:         Optional[str]            = None,
        description:       Optional[str]            = None,
        flags:             Optional[Flags]          = None,
        commands:          Optional[Commands]       = None,
        allow_parent:      bool                     = False,
        authors:           Optional[List[str]]      = None,
        email:             Optional[str]            = None,
        copyright:         Optional[str]            = None,
        writer:            TextIO                   = sys.stdout,
        err_writer:        TextIO                   = sys.stderr,
        help_app_template: Optional[str]            = None,
        help_cmd_template: Optional[str]            = None,
        before:            OptAction                = None,
        action:            OptAction                = None,
        after:             OptAction                = None,
        on_usage_error:    Optional[UsageErrorFunc] = None,
        exit_with_error:   Optional[ExitErrorFunc]  = None,
        not_found_error:   Optional[NotFoundFunc]   = None,
    ):
        super().__init__(
            name=name,
            usage=usage,
            argsusage=argsusage,
            flags=flags,
            commands=commands,
            allow_parent=allow_parent,
            before=before,
            action=action,
            after=after,
        )
        self.version           = version
        self.description       = description
        self.authors           = authors or []
        self.email             = email
        self.copyright         = copyright
        self.writer            = writer
        self.err_writer        = err_writer
        self.help_app_template = help_app_template
        self.help_cmd_template = help_cmd_template
        setattr(self, 'on_usage_error',  on_usage_error or self.on_usage_error)
        setattr(self, 'exit_with_error', exit_with_error or self.exit_with_error)
        setattr(self, 'not_found_error', not_found_error or self.not_found_error)
        self.flags.insert(0, help_flag)
        self.commands.insert(0, help_command)

    def on_usage_error(self, err: UsageError):
        """
        handles usage errors during parsing or from context

        :param err: usage-exception contianing details on error
        """
        print(f'Incorrect Usage: {err.message}\n', file=self.err_writer)
        help_action(err.context, err.command)
        raise SystemExit(EX_USAGE)

    def exit_with_error(self, err: ExitError):
        """
        handles unrecoverable exceptions that must lead to complete exit

        :param err: exit-exception contianing details on error
        """
        print(f"App-Error: {err}", file=self.err_writer)
        raise SystemExit(err.code)

    def not_found_error(self, err: NotFoundError):
        """
        handles issues with invalid flags and bad command paths on help

        :param err: not-found-exception contianing details on error
        """
        msg = f'No Help topic for: {"->".join(err.path)}'
        if err.message.startswith('-'):
            msg = f'Command: {err.command.name}, Invalid Flag: {err.message}'
        print(msg, file=self.err_writer)
        raise SystemExit(EX_UNAVAILABLE)
 
    def config_error(self, err: ConfigError):
        """
        handles issues with app/command configuration errors

        :param err: config-exception containing details on error
        """
        print(f'ConfigError: {err.message}', file=self.err_writer)
        raise SystemExit(EX_CONFIG)

    def run(self, args: OptStrList = None, run_async: bool = False) -> OptCoroutine:
        """
        run the relevant actions based on the arguments given and app defintions

        :param args:      args being parsed and passed into relevant actions
        :param run_async: override app run_async setting
        :return:          asyncio coroutine if run_async=True
        """
        args   = args if args is not None else sys.argv.copy()
        future = run_app(self, args)
        if run_async:
            return future
        # generate new loop and ensure closure reguardless of error
        loop = get_event_loop()
        try:
            loop.run_until_complete(future)
        finally:
            loop.close()
