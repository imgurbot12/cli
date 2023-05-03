"""
argument parsing logic and handling to run application as defined
"""
from typing import List, Optional, NamedTuple

from .abc import *
from .help import help_flag, help_action

#** Variables **#
__all__ = [
    'validate_cmd',
    'exec_app',
    'run_app',

    'EX_USAGE',
    'EX_UNAVAILABLE',
    'EX_CONFIG'
]

# exit codes stolen from sysexists.h (/usr/include/sysexits.h)
EX_USAGE       = 64  #- command line usage error -#
EX_UNAVAILABLE = 69  #- service unavailable -#
EX_CONFIG      = 78  #- configuration error -#

class SplitArgs(NamedTuple):
    next:      Optional[AbsCommand]
    collected: List[str]
    remaining: List[str]

#** Functions **#

def validate_cmd(command: AbsCommand):
    """
    validate command object to avoid configuration errors

    :param cmd: command object to validate
    """
    # ensure flag-names dont overlap
    for n in range(len(command.flags)-1, 0, -1):
        flag = command.flags[n]
        for other in command.flags[:n]:
            for name in flag.names:
                if name in other.names:
                    raise ConfigError(
                        f'command {command.name!r} > flag {flag.display!r} '
                        f'name overlaps {other.display!r}', command)
    # ensure command-names don't overlap
    for n in range(len(command.commands)-1, 0, -1):
        cmd = command.commands[n]
        for other in command.commands[:n]:
            if cmd.name == other.name:
                raise ConfigError(
                    f'command {command.name!r} > subcmd '
                    f'{cmd.name!r} name overlaps: {other.name!r}', command)
            for alias in cmd.aliases:
                if alias == other.name or alias in other.aliases:
                    raise ConfigError(
                        f'cmd {command.name!r} > subcmd {cmd.name!r} '
                        f'alias {alias!r} overlaps: {other.name!r}', command)
    # validate subcommands as well
    for cmd in command.commands:
        validate_cmd(cmd)

def split_arguments(cmd: AbsCommand, args: List[str]) -> SplitArgs:
    """
    split arguments into current command values and next command arguments

    :param cmd:  command being evaluated for currently
    :param args: args to split into related values and non-related values
    :return:     (next-command <if any>, related-values, unrelated-values)
    """
    args.pop(0)
    next:  Optional[AbsCommand] = None
    index: int = len(args)
    for command in cmd.commands:
        idx = command.index(args)
        if idx is not None and idx <= index:
            next  = command
            index = idx
    return SplitArgs(next, args[:index], args[index:])

def parse_flags(
    flags: Flags, args: List[str], ctx: Context, cmd: AbsCommand) -> FlagDict:
    """
    parse values for flag-values based on flag definitions

    :param flags: flags to scan arguments for
    :param args:  all arguments to be parsed for flag-values
    :return:      dictionary of flag-names to flag-values
    """
    # collect indexes or defaults
    (fdict, indexes) = ({}, [])
    for flag in flags:
        index = flag.index(args)
        # if flag is not present
        if index is None:
            # if flag has default
            if flag.default is not None:
                fdict[flag.long] = flag.default
            # if flag is required
            elif flag.required:
                raise UsageError(f'flag {flag.display!r} is required', ctx, cmd)
            continue
        # check if flag appears more than once
        plusone = index+1
        if flag.index(args[plusone:]) is not None:
            raise UsageError(
                f'flag {flag.display!r} declared more than once', ctx, cmd)
        # raise error if indexes overlap or value isnt given
        if flag.has_value and (len(args) <= plusone or plusone in indexes):
            raise UsageError(
                f'flag {flag.display!r} no value specified', ctx, cmd)
        # append index otherwise
        indexes.append((flag, index))
    # collect values from indexes (from highest to lowest)
    for flag, idx in sorted(indexes, key=lambda x: x[1], reverse=True):
        # attempt to get value, convert, and set in values
        if flag.has_value:
            # attempt to parse value
            raw = args.pop(idx+1)
            val = flag.parse(raw)
            if val is None:
                raise UsageError(
                    f'flag {flag.display!r} decode fail: {raw!r}', ctx, cmd)
            fdict[flag.long] = val
        # if no-value is possible, set to true
        else:
            fdict[flag.long] = True
        args.pop(idx)
    # iterate the arguments for any non-parsed flags
    for arg in args:
        if arg.startswith('-'):
            raise NotFoundError(arg, [], ctx, cmd)
    # return parsed values
    return fdict

def has_help_flag(gflags: dict) -> bool:
    """
    check if the given global flags contain the help flag

    :param gflags: parsed global flags
    :return:       true if `help` flag is found
    """
    return bool(gflags.get(help_flag.long))

async def exec_app(app: AbsApplication, args: List[str]):
    """
    iterate args until given commands and correlated flags are executed

    :param app:     application w/ flag/command definitions
    :param args:    arguments to parse according to app definition
    """
    # validate application configuration before executing
    validate_cmd(app)
    # run application
    context: Context    = Context(app, app)
    command: AbsCommand = app
    # evaluate and run commands based on cli data
    next_cmd:     Optional[AbsCommand] = app
    funcret:      Result               = None
    global_flags: Optional[FlagDict]   = None
    help_flag:    bool                 = False
    while next_cmd is not None:
        (command, parent) = (next_cmd, context)
        # split args into next-command args and current args
        next_cmd, values, args = split_arguments(command, args)
        # collect flags from values
        flags = parse_flags(command.flags, values, context, command)
        # pass content into new context
        if global_flags is None:
            global_flags = flags
        values  = Args(values)
        context = Context(app, command, parent, global_flags, flags, values)
        # only run command if no subcommand is present or parent is allowed
        help_flag = help_flag or has_help_flag(global_flags)
        if (next_cmd is None and not help_flag) or command.allow_parent:
            await command.run_before(context)
            funcret = await command.run_action(context)
            await command.run_after(context)
    # raise help if help-flag was given
    if help_flag:
        help_action(context, command)
    # raise help if no action was taken at all
    elif funcret == NO_ACTION:
        raise UsageError('no action taken', context, command)

async def run_app(app: AbsApplication, args: List[str]):
    """
    wrap app execution/iteration w/ standard application error-handlers

    :param app:  application w/ flag/command definitions
    :param args: arguments to parse according to app definition
    """
    try:
        await exec_app(app, args) 
    except UsageError as e:
        app.on_usage_error(e)
    except ExitError as e:
        app.exit_with_error(e)
    except NotFoundError as e:
        app.not_found_error(e)
    except ConfigError as e:
        app.config_error(e)
