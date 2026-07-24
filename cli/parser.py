"""
CLI Argument Parser
"""
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast
from typing_extensions import NamedTuple

from . import T
from .arg import Arg
from .cmd import Command
from .flag import Flag
from .context import MISSING
from .help import Help

#** Variables **#
__all__ = ['Parser', 'ParsedCmd']

ArgValue   = Union[str, None, Type[MISSING]]
FlagValues = Union[List[Optional[str]], Type[MISSING]]

#** Functions **#

def index_flags(flags: List[Flag], args: List[str]) -> List[Tuple[int, Flag]]:
    """
    """
    flags   = flags.copy()
    indexes = []
    for arg_idx, arg in enumerate(args, 0):
        if arg == '--':
            break
        for flag_idx, flag in enumerate(flags, 0):
            if arg not in flag.variants():
                continue
            indexes.append((arg_idx, flag))
            if not flag.repeat:
                flags.pop(flag_idx)
            break
    return indexes

def index_commands(
    commands: List[Command], args: List[str]) -> List[Tuple[int, Command]]:
    """
    """
    commands = commands.copy()
    indexes  = []
    for arg_idx, arg in enumerate(args, 0):
        if arg == '--':
            break
        for cmd_idx, command in enumerate(commands, 0):
            if command.name != arg and arg not in command.aliases:
                continue
            indexes.append((arg_idx, command))
            commands.pop(cmd_idx)
            break
    return indexes

#** Classes **#

class ParsedCmd(NamedTuple):
    source:   Command
    args:     Dict[str, Any]
    commands: Dict[str, 'ParsedCmd']
    flags:    Dict[str, Any]

class ParseCtx:
    """
    """
    __slots__ = ('path', 'missing', 'missing_v', 'invalid', 'unexpected')

    path:       List[Command]
    missing:    List[Union[Arg, Flag, Command]]
    missing_v:  List[Flag]
    invalid:    Dict[Union[Arg, Flag], str]
    unexpected: List[str]

    def __init__(self, path: List[Command]):
        self.path       = path
        self.missing    = []
        self.missing_v  = []
        self.invalid    = {}
        self.unexpected = []

    def __repr__(self) -> str:
        path = [c.name for c in self.path]
        return f'Context(path={path})'

    @property
    def command(self) -> Command:
        """
        """
        return self.path[-1]

    def stack(self, command: Command) -> 'ParseCtx':
        """
        """
        return self.__class__([*self.path, command])

    def splice_args(self, array: List[T],
        index: int, length: Optional[int] = None) -> List[T]:
        """
        """
        end    = (index + length) if length is not None else len(array)
        splice = array[index:end]
        array[index:end] = []
        return splice

    def add_missing(self, *missing: Union[Arg, Flag, Command]):
        """
        """
        self.missing.extend(missing)

    def add_missing_value(self, *missing: Flag):
        """
        """
        self.missing_v.extend(missing)

    def add_invalid(self, invalid: Union[Arg, Flag], value: str):
        """
        """
        self.invalid[invalid] = value

    def add_unexpected(self, *unexpected: str):
        """
        """
        self.unexpected.extend(unexpected)

    def finalize(self):
        """
        """
        if self.unexpected:
            raise Unexpected(self, self.unexpected)
        if self.invalid:
            raise Invalid(self, self.invalid)
        if self.missing_v:
            raise MissingValue(self, self.missing_v)
        if self.missing:
            command = [m for m in self.missing if isinstance(m, Command)]
            if command:
                raise CommandRequired(self, command[0].commands)
            raise Missing(self, cast(List[Union[Arg, Flag]], self.missing))

class Parser:
    """
    """
    __slots__ = ('command', 'complete', 'help')

    def __init__(self,
        command:  Command,
        help:     Optional[Help]    = None,
        complete: Optional[Command] = None,
    ):
        self.help     = help or Help()
        self.command  = command
        self.complete = complete or autocomplete_cmd()
        self._init()

    def _init(self):
        """
        """
        command = self.command
        self.help.apply_helpers(command)
        if self.complete not in command.commands:
            command.commands.append(self.complete)
            #NOTE: dont force autocomplete command usage
            if len(command.commands) == 1:
                command.invoke_without_command = True
        command.validate()

    def validate_arg(self,
        ctx: ParseCtx, arg: Arg, value: ArgValue, error_flags: bool) -> Any:
        """
        """
        if value is MISSING:
            return ctx.add_missing(arg) if arg.required else arg.default

        if error_flags and isinstance(value, str) and value.startswith('-'):
            return ctx.add_unexpected(value)

        for validator in arg.validators:
            try:
                value = validator(value)
            except ValueError as e:
                return ctx.add_invalid(arg, e.args[0])
        return value

    def validate_flag(self, ctx: ParseCtx, flag: Flag, values: FlagValues) -> Any:
        """
        """
        if values is MISSING:
            return ctx.add_missing(flag) if flag.required else flag.default

        values = cast(List[Optional[str]], values)
        if flag._requires_value() and any(v is None for v in values):
            return ctx.add_missing_value(flag)

        parsed = []
        for value in values:
            if value is None:
                parsed.append(flag.default if flag._requires_value() else True)
                continue
            for validator in flag.validators:
                try:
                    value = validator(value)
                except ValueError as e:
                    return ctx.add_invalid(flag, e.args[0])
            parsed.insert(0, value)
        return parsed if flag.repeat else parsed[0]

    def split_args(self, ctx: ParseCtx,
        cmdargs: List[Arg], args: List[str]) -> Dict[str, Any]:
        """
        """
        values      = {}
        cmdargs     = cmdargs.copy()
        error_flags = True
        while cmdargs and args:
            cmdarg = cmdargs[0]
            value  = args.pop(0) if args else MISSING
            if value == '--' and error_flags:
                error_flags = False
                continue

            value = self.validate_arg(ctx, cmdarg, value, error_flags)
            if cmdarg.repeat:
                value = value if isinstance(value, (list, tuple, set)) else [value]
                values.setdefault(cmdarg.name, [])
                values[cmdarg.name].extend(value)
            else:
                values[cmdarg.name] = value
                cmdargs.pop(0)

        remaining = []
        for arg in cmdargs:
            if arg.name in values:
                continue
            if arg.default is not None:
                values[arg.name] = arg.default
                continue
            if arg.required:
                remaining.append(arg)

        ctx.add_missing(*remaining)
        ctx.add_unexpected(*args)
        return values

    def split_flags(self, ctx: ParseCtx,
        flags: List[Flag], args: List[str]) -> Dict[str, Any]:
        """
        """
        indexes = index_flags(flags, args)

        values: Dict[str, List[Optional[str]]] = {}
        indexes.reverse()
        for idx, flag in indexes:
            ctx.splice_args(args, idx, 1)
            has_value = not any(i == idx + 1 for i, _ in indexes) \
                and idx + 1 <= len(args) and flag._requires_value()
            value = ctx.splice_args(args, idx, 1)[0] if has_value else None
            values.setdefault(flag.name, [])
            values[flag.name].append(value)

        parsed = {}
        for flag in flags:
            fvalue = values.get(flag.name, MISSING)
            parsed[flag.name] = self.validate_flag(ctx, flag, fvalue)
        return parsed

    def split_commands(self, ctx: ParseCtx, commands: List[Command],
        args: List[str]) -> Dict[str, ParsedCmd]:
        """
        """
        indexes = index_commands(commands, args)

        parsed = []
        indexes.reverse()
        for idx, command in indexes:
            c_ctx      = ctx.stack(command)
            c_args     = c_ctx.splice_args(args, idx)[1:]
            c_commands = self.split_commands(c_ctx, command.commands, c_args)
            c_flags    = self.split_flags(c_ctx, command.flags, c_args)
            c_params   = self.split_args(c_ctx, command.args, c_args)
            c_ctx.finalize()
            parsed.append((command.name, ParsedCmd(command,
                c_params, c_commands, c_flags)))

        parsed.reverse()
        if not parsed and commands \
            and not ctx.command.invoke_without_command:
            ctx.add_missing(ctx.command)
        return OrderedDict(parsed)

    def split_help(self, ctx: ParseCtx, args: List[str]):
        """
        """
        for variant in self.help.flag.variants():
            if variant in args:
                raise HelpError(ctx, self.command)

        variants = self.help.command.variants()
        for idx, arg in enumerate(args, 0):
            if arg not in variants:
                continue

            cmd  = self.command
            path = args[idx+1:]
            for item in path:
                variants = {v:c for c in cmd.commands for v in c.variants()}
                if item not in variants:
                    raise InvalidCommand(ctx, item)
                cmd = variants[item]
            raise HelpError(ctx, cmd)

    def parse(self, args: List[str]) -> ParsedCmd:
        """
        """
        args     = args.copy()
        nargs    = len(args)
        ctx      = ParseCtx([self.command])
        self.split_help(ctx, args)

        try:
            commands = self.split_commands(ctx, self.command.commands, args)
            flags    = self.split_flags(ctx, self.command.flags, args)
            params   = self.split_args(ctx, self.command.args, args)
            ctx.finalize()
        except CliError as err:
            if nargs == 0:
                raise HelpError(ctx, self.command) from None
            raise err
        return ParsedCmd(self.command, params, commands, flags)

#** Imports **#
from .errors import (
    CliError, CommandRequired, HelpError, Invalid, InvalidCommand, Missing,
    MissingValue, Unexpected)
from .suggest import autocomplete_cmd
