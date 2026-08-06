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
from .context import MISSING, get_dict
from .help import Help

#** Variables **#
__all__ = ['Parser', 'ParsedCmd']

ArgValue   = Union[str, None, Type[MISSING]]
FlagValues = Union[List[Optional[str]], Type[MISSING]]

#** Functions **#

def index_flags(flags: List[Flag], args: List[str]) -> List[Tuple[int, Flag]]:
    """
    retrieve list of indexes for each flag found in the arguments

    :param flags: list of flags to find indexes of
    :param args:  list of arguments to parse flags from
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
    retrieve list of indexes for each command found in the arguments

    :param commands: list of commands to find indexes of
    :param args:     list of arguments to parse commands from
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
            if not command.repeat:
                commands.pop(cmd_idx)
            break
    return indexes

#** Classes **#

class ParsedCmd(NamedTuple):
    """
    Parse Completion Command Details
    """
    source:   Command
    args:     Dict[str, Any]
    commands: Dict[str, List['ParsedCmd']]
    flags:    Dict[str, Any]

class ParseCtx:
    """
    Parsing shared context object
    """
    __slots__ = ('path', 'extra',
        'missing', 'missing_v', 'invalid', 'unexpected', 'disallowed')

    path:       List[Command]
    extra:      Dict[str, Any]

    missing:    List[Union[Arg, Flag, Command]]
    missing_v:  List[Flag]
    disallowed: List[Command]
    invalid:    InvalidDict
    unexpected: List[str]

    def __init__(self, path: List[Command], extra: Dict[str, Any]):
        self.path       = path
        self.extra      = extra
        self.missing    = []
        self.missing_v  = []
        self.invalid    = {}
        self.disallowed = []
        self.unexpected = []

    def __repr__(self) -> str:
        return f'ParseCtx(path={[c.name for c in self.path]})'

    @property
    def command(self) -> Command:
        """
        retrieve latest command in parsing stack
        """
        return self.path[-1]

    def stack(self, command: Command) -> 'ParseCtx':
        """
        generate new child context with next command
        """
        return self.__class__([*self.path, command], self.extra)

    def splice_args(self, array: List[T],
        index: int, length: Optional[int] = None) -> List[T]:
        """
        splice a subsection of an array and remove it from the existing one

        :param array:  array to splice entries from
        :param index:  index to begin splicing from
        :param length: length of items to splice (defaults to end)
        :return:       subsection spliced out
        """
        end    = (index + length) if length is not None else len(array)
        splice = array[index:end]
        array[index:end] = []
        return splice

    def get_extra(self, name: str, ctype: Type[T]) -> T:
        """
        retrieve extra value of a specific name and validate type

        :param name:  name of extra value
        :param ctype: type annotation/validation
        """
        if name not in self.extra:
            if issubclass(ctype, self.__class__):
                return cast(T, self)
        return get_dict(self.extra, name, ctype)

    def add_missing(self, *missing: Union[Arg, Flag, Command]):
        """
        log a missing argument/flag/command during parsing
        """
        self.missing.extend(missing)

    def add_missing_value(self, *missing: Flag):
        """
        log a missing flag value during parsing
        """
        self.missing_v.extend(missing)

    def add_disallowed(self, commands: List[Command]):
        """
        log disallowed command chain
        """
        self.disallowed.extend(commands)

    def add_invalid(self, invalid: Union[Arg, Flag], value: str, error: str):
        """
        log an invalid argument/flag value during parsing
        """
        self.invalid[invalid] = InvalidRef(value, error)

    def add_unexpected(self, *unexpected: str):
        """
        log an unexpected argument during parsing
        """
        self.unexpected.extend(unexpected)

    def finalize(self):
        """
        raise an exception if any items were logged during parsing
        """
        if self.unexpected:
            raise Unexpected(self, self.unexpected)
        if self.invalid:
            raise Invalid(self, self.invalid)
        if self.disallowed:
            raise NoCommandChain(self, self.disallowed)
        if self.missing_v:
            raise MissingValue(self, self.missing_v)
        if self.missing:
            command = [m for m in self.missing if isinstance(m, Command)]
            if command:
                raise CommandRequired(self, command[0].commands)
            raise Missing(self, cast(List[Union[Arg, Flag]], self.missing))

class Parser:
    """
    CLI Raw Argument Parser Implementation
    """
    __slots__ = ('command', 'complete', 'help')

    def __init__(self,
        command:  Command,
        help:     Optional[Help]    = None,
        complete: Optional[Command] = None,
    ):
        """
        :param command:  command definition to parse from
        :param help:     help-page generator
        :param complete: auto-completion command (if any)
        """
        self.help     = help or Help()
        self.command  = command
        self.complete = complete or autocomplete_cmd()
        self._init()

    def _init(self):
        """
        append help and auto-complete flags/commands
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
        validate the given value matches an arguments configuration

        :param ctx:         parsing context
        :param arg:         command argument definition
        :param value:       value to parse
        :param error_flags: raise an exception on flag prefix if true
        """
        if value is MISSING:
            return ctx.add_missing(arg) if arg.required else arg.default

        if error_flags and isinstance(value, str) and value.startswith('-'):
            return ctx.add_unexpected(value)

        for raw_validator in arg.validators:
            validator = wrap_validator(raw_validator)
            try:
                value = validator(ctx, value)
            except ValueError as e:
                value = cast(str, value)
                return ctx.add_invalid(arg, value, e.args[0])
        return value

    def validate_flag(self, ctx: ParseCtx, flag: Flag, values: FlagValues) -> Any:
        """
        validate the given value matches a flags configuration

        :param ctx:    parsing context
        :param flag:   command flag/option definition
        :param values: values assigned to flag
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
            for raw_validator in flag.validators:
                validator = wrap_validator(raw_validator)
                try:
                    value = validator(ctx, value)
                except ValueError as e:
                    return ctx.add_invalid(flag, value, e.args[0])
            parsed.insert(0, value)
        return parsed if flag.repeat else parsed[0]

    def split_args(self, ctx: ParseCtx,
        cmdargs: List[Arg], args: List[str]) -> Dict[str, Any]:
        """
        split command arguments from the raw argument list

        :param ctx:     parsing context
        :param cmdargs: command arguments to parse and validate against
        :param args:    raw arguments to parse from
        :return:        map of parsed/validated argument values
        """
        values      = {} #type: Dict[str, Any]
        cmdargs     = cmdargs.copy()
        error_flags = True
        while cmdargs and args:
            cmdarg = cmdargs[0]
            value  = args.pop(0) if args else MISSING
            if value == '--' and error_flags:
                error_flags = False
                continue

            val = self.validate_arg(ctx, cmdarg, value, error_flags)
            if cmdarg.repeat:
                val = val if isinstance(val, (list, tuple, set)) else [val]
                values.setdefault(cmdarg.name, [])
                values[cmdarg.name].extend(val)
            else:
                values[cmdarg.name] = val
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
        split flags from the raw argument list

        :param ctx:   parsing context
        :param flags: command flags to parse and validate against
        :param args:  raw arguments to parse from
        :return:      map of parsed/validated flag values
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
        args: List[str]) -> Dict[str, List[ParsedCmd]]:
        """
        split sub-commands from the raw argument list

        :param ctx:      parsing contxt
        :param commands: subcommands to parse and validate against
        :param args:     raw arguments to parse from
        :return:         map of parsed/validated commands
        """
        indexes = index_commands(commands, args)

        parsed: Dict[str, List[ParsedCmd]] = OrderedDict()
        indexes.reverse()
        for idx, command in indexes:
            c_ctx      = ctx.stack(command)
            c_args     = c_ctx.splice_args(args, idx)[1:]
            c_commands = self.split_commands(c_ctx, command.commands, c_args)
            c_flags    = self.split_flags(c_ctx, command.flags, c_args)
            c_params   = self.split_args(c_ctx, command.args, c_args)
            c_ctx.finalize()
            parsed.setdefault(command.name, [])
            parsed[command.name].insert(0,
                ParsedCmd(command, c_params, c_commands, c_flags))

        if not parsed and commands \
            and not ctx.command.invoke_without_command:
            ctx.add_missing(ctx.command)

        if len(parsed) > 1 and not ctx.command.chain:
            ctx.add_disallowed([c for c in commands if c.name in parsed])

        return OrderedDict(reversed(parsed.items()))

    def split_help(self, ctx: ParseCtx, args: List[str]):
        """
        check for the presence of the help command/flag and raise error

        :param ctx:  parsing context
        :param args: raw arguments to compare against
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
                vars = {v:c for c in cmd.commands for v in c.variants()}
                if item not in vars:
                    raise InvalidCommand(ctx, item)
                cmd = vars[item]
            raise HelpError(ctx, cmd)

    def parse(self, args: List[str],
        extra: Optional[Dict[str, Any]] = None) -> ParsedCmd:
        """
        parse the specified arguments against the command defintion

        :param args: raw arguments to parse from
        :return:     parsed command values
        """
        args     = args.copy()
        nargs    = len(args)
        ctx      = ParseCtx([self.command], extra or {})
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
    CliError, CommandRequired, HelpError, Invalid, InvalidCommand,
    InvalidDict, InvalidRef, Missing, MissingValue, NoCommandChain, Unexpected)
from .suggest import autocomplete_cmd
from .wraps import wrap_validator
