"""
Help Page Generation
"""
import functools
from typing import Callable, List, Optional, Union

from . import T
from .arg import Arg
from .cmd import Command
from .flag import Flag
from .style import AnsiTermStyle, Styling

#** Variables **#
__all__ = ['Help']

#** Functions **#

@functools.lru_cache()
def help_flag() -> Flag:
    return Flag[bool]('help', 'Print help', suggestor=False)

@functools.lru_cache()
def help_command() -> Command:
    return Command(
        name='help',
        about='Print this message or the help of the given subcommand(s)',
        suggest=False)

#** Classes **#

class Help:
    """
    """
    __slots__ = ('styling', 'indent', 'space', 'newline', 'flag', 'command')

    def __init__(self,
        styling: Optional[Styling] = None,
        indent:  str               = '  ',
        space:   str               = ' ',
        newline: str               = '\n',
    ):
        self.styling = styling or AnsiTermStyle()
        self.indent  = indent
        self.space   = space
        self.newline = newline
        self.flag    = help_flag()
        self.command = help_command()

    def apply_helpers(self, command: Command):
        """
        """
        if self.flag not in command.flags:
            command.flags.append(self.flag)
        if command.commands and self.command not in command.commands:
            command.commands.append(self.command)

    def buffer(self,
        items:     List[T],
        left:      Callable[[T], str],
        right:     Callable[[T], str],
        threshold: int = 80,
        prefix:    Optional[str] = None,
    ) -> str:
        """
        """
        r1 = []
        r2 = []
        for item in items:
            r1.append(left(item))
            r2.append(right(item))

        buffer = 0
        prefix = prefix or self.indent
        for a, b in zip(r1, r2):
            line = self.indent + a
            if (len(prefix) + len(line) + len(b)) > threshold:
                buffer = None
                break
            buffer = len(line) if buffer < len(line) else buffer

        lines = []
        if buffer is None:
            for a, b in zip(r1, r2):
                line = a + self.newline + (self.indent * 2) + b
                lines.append(prefix + line)
        else:
            for a, b in zip(r1, r2):
                buf = self.space * (buffer - len(a) + 1)
                lines.append(prefix + a + buf + b)
        return self.newline.join(lines) + self.newline

    def about(self, item: Union[Arg, Flag]) -> str:
        """
        """
        if isinstance(item, Flag) and not item._requires_value():
            return item.about
        if item.default is not None:
            default = item.default
            if isinstance(default, bool):
                default = int(default)
            return f'{item.about} [default: {default}]'
        return item.about or 'required argument'

    def arg_usage(self, ctx: 'ParseCtx', arg: Arg) -> str:
        """
        """
        if arg.required:
            return f'<{arg.name.upper()}>'
        return f'[{arg.name.upper()}]'

    def flag_usage(self, ctx: 'ParseCtx', flag: Flag, short: bool = False) -> str:
        """
        """
        if not flag._requires_value():
            value = ''
        elif flag.default is not None:
            value = f'[{flag.name.upper()}]'
        else:
            value = f'<{flag.name.upper()}>'

        if short:
            if flag.short is not None:
                return f'-{flag.short} --{flag.long} {value}'
            return self.space * 4 + f'--{flag.long} {value}'
        return f'--{flag.long} {value}'

    def command_usage(self, ctx: 'ParseCtx', cmd: Command) -> str:
        """
        """
        path  = [*ctx.path[:-1], cmd]
        usage = []
        for c in path:
            usage.append(c.name)
            for arg in c.args:
                usage.append(self.arg_usage(ctx, arg))

            flags    = [f for f in c.visible_flags() if f != self.flag]
            required = [f for f in flags if f.required]
            for flag in required:
                usage.append(self.flag_usage(ctx, flag))
            if len(required) < len(flags):
                usage.append('<OPTIONS>')

        if cmd.commands:
            command = '[COMMAND]' if cmd.invoke_without_command else '<COMMAND>'
            usage.append(command)
        return self.space.join(usage)

    def usage(self, ctx: 'ParseCtx', item: Union[Arg, Command, Flag]) -> str:
        """
        """
        if isinstance(item, Arg):
            return self.arg_usage(ctx, item)
        elif isinstance(item, Flag):
            return self.flag_usage(ctx, item)
        return self.command_usage(ctx, item)

    def err_suffix(self, ctx: 'ParseCtx') -> str:
        """
        """
        return self.newline \
            + self.styling.wrap_style('underline', 'Usage:') \
            + self.space \
            + self.command_usage(ctx, ctx.command) \
            + self.newline * 2 \
            + "For more information, try: '--help'."

    def help(self, ctx: 'ParseCtx', cmd: Command) -> str:
        """
        """
        help    = self.styling.wrap_style('underline', 'Usage:') \
            + self.space \
            + self.command_usage(ctx, cmd) \
            + self.newline
        if cmd.args:
            help += self.newline \
                + self.styling.wrap_style('underline', 'Arguments:') \
                + self.newline \
                + self.buffer(
                    items=cmd.args,
                    left=lambda arg: self.arg_usage(ctx, arg),
                    right=self.about,
                )
        if cmd.visible_commands():
            help += self.newline \
                + self.styling.wrap_style('underline', 'Commands:') \
                + self.newline \
                + self.buffer(
                    items=cmd.visible_commands(),
                    left=lambda c: c.name,
                    right=lambda c: c.about or '',
                )
        if cmd.visible_flags():
            short = any(f.short is not None for f in cmd.flags)
            help += self.newline \
                + self.styling.wrap_style('underline', 'Options:') \
                + self.newline \
                + self.buffer(
                    items=cmd.visible_flags(),
                    left=lambda f: self.flag_usage(ctx, f, short),
                    right=self.about,
                )
        return help

#** Imports **#
from .parser import ParseCtx
