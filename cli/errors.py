"""
CLI Parser/Runtime Exception Implementations
"""
from typing import ClassVar, Dict, List, Optional, Union

from .arg import Arg
from .cmd import Command
from .flag import Flag
from .help import Help
from .parser import ParseCtx

#** Variables **#
__all__ = [
    'Exit',
    'CliError',

    'HelpError',
    'CommandRequired',
    'NoCommandChain',
    'InvalidCommand',
    'Missing',
    'MissingValue',
    'Invalid',
    'Unexpected',
]

#** Classes **#

class Exit(RuntimeError):
    """
    Custom Exception for Early Exit of CLI Actions
    """

    def __init__(self, exit_code: int = 0):
        self.exit_code = exit_code

class CliError(Exception):
    """
    Baseclass for CLI Exceptions
    """
    exit_code: ClassVar[int] = 1

    def __init__(self, ctx: ParseCtx, *args):
        super().__init__(ctx, *args)
        self.ctx     = ctx
        self.message = self.__class__.__name__

    def format_message(self, help: Help) -> str:
        """
        format the error message as part of the help-display
        """
        return self.message

    def show(self, help: Optional[Help] = None) -> str:
        """
        show the help-page associated with this error
        """
        help = help or Help()
        return help.styling.wrap_color('red', 'error:') \
            + help.space \
            + self.format_message(help) \
            + help.newline \
            + help.err_suffix(self.ctx)

class HelpError(CliError):
    """
    Internal Exception used when Help Command should be raised.
    """
    exit_code: ClassVar[int] = 0

    def __init__(self, ctx: ParseCtx, command: Command):
        super().__init__(ctx, command)
        self.ctx     = ctx
        self.command = command

    def show(self, help: Optional[Help] = None) -> str:
        help = help or Help()
        return help.help(self.ctx, self.command)

class UsageError(CliError):
    """
    Generic Usage Error Exception
    """
    exit_code: ClassVar[int] = 2

    def __init__(self, ctx: ParseCtx, *args):
        super().__init__(ctx, *args)
        if args and isinstance(args[0], str):
            self.message = args[0]

class InvalidCommand(UsageError):
    def __init__(self, ctx: ParseCtx, command: str):
        super().__init__(ctx, command)
        self.command = command
        self.message = 'unrecognized subcommand'

    def format_message(self, help: Help) -> str:
        return self.message + help.space \
            + help.styling.wrap_color('yellow', repr(self.command))

class CommandRequired(UsageError):
    def __init__(self, ctx: ParseCtx, commands: List[Command]):
        super().__init__(ctx, commands)
        self.commands = commands
        self.message  = 'requires a subcommand but one was not provided'

    def format_message(self, help: Help) -> str:
        commands = self.ctx.command.visible_commands()
        name = help.styling.wrap_color('yellow', repr(self.ctx.command.name))
        cmds = [help.styling.wrap_color('green', c.name) for c in commands]
        return f'{name} {self.message}' \
            + help.newline \
            + help.indent \
            + f'[subcommands: {", ".join(cmds)}]'

class NoCommandChain(UsageError):
    def __init__(self, ctx: ParseCtx, commands: List[Command]):
        super().__init__(ctx, commands)
        self.commands = commands
        self.message  = 'command chaining is not allowed'

    def format_message(self, help: Help):
        cmds = [help.styling.wrap_color('green', c.name) for c in self.commands]
        name = help.styling.wrap_color('yellow', repr(self.ctx.command.name))
        return f'{name} {self.message}' \
            + help.newline \
            + help.indent \
            + f'[used: {", ".join(cmds)}]'

class Missing(UsageError):
    def __init__(self, ctx: ParseCtx, missing: List[Union[Arg, Flag]]):
        super().__init__(ctx, missing)
        self.missing = missing
        self.message = 'the following required arguments were not provided'
        self.missing.sort(key=lambda m: isinstance(m, Flag))

    def format_message(self, help: Help) -> str:
        elems   = []
        for elem in self.missing:
            line = help.usage(self.ctx, elem)
            elems.append(help.indent + help.styling.wrap_color('green', line))
        return f'{self.message}:' \
            + help.newline \
            + help.newline.join(elems)

class MissingValue(UsageError):
    def __init__(self, ctx: ParseCtx, missing: List[Flag]):
        super().__init__(ctx, missing)
        self.missing = missing
        self.message = 'following flag(s) are missing values'

    def format_message(self, help: Help) -> str:
        items = []
        for flag in self.missing:
            line          = help.flag_usage(self.ctx, flag)
            prefix, value = line.rsplit(help.space, 1)
            value         = help.styling.wrap_color('yellow', value)
            line          = prefix + help.space + value
            items.append(help.indent + line)
        return f'{self.message}:' \
            + help.newline \
            + help.newline.join(items)

class Invalid(UsageError):
    def __init__(self, ctx: ParseCtx, invalid: Dict[Union[Arg, Flag], str]):
        super().__init__(ctx, invalid)
        self.invalid = invalid
        self.message = 'invalid arguments present'

    def format_message(self, help: Help) -> str:
        invalid = list(self.invalid.items())
        invalid.sort(key=lambda i: isinstance(i[0], Arg))
        return f'{self.message}:' \
            + help.newline \
            + help.buffer(
                items=invalid,
                left=lambda items: help.usage(self.ctx, items[0]),
                right=lambda items: help.styling.wrap_color('yellow', items[1]),
            ).rstrip()

class Unexpected(UsageError):
    def __init__(self, ctx: ParseCtx, unexpected: List[str]):
        super().__init__(ctx, unexpected)
        self.unexpected = unexpected
        self.message    = 'unexpected argument'

    def format_message(self, help: Help) -> str:
        items = [help.styling.wrap_color('yellow', repr(u))
            for u in self.unexpected]
        return f'{self.message}(s) {", ".join(items)} found'
