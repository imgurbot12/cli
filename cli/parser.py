"""
argument parsing logic and handling to run application as defined
"""
from typing import List, Tuple, Optional

from .flag import Flags
from .context import *
from .command import CommandBase, Command
from .help import help_flag, help_action

#** Variables **#
__all__ = [
    'run_app',

    'EX_USAGE',
    'EX_UNAVAILABLE',
    'EX_CONFIG'
]

# exit codes stolen from sysexists.h (/usr/include/sysexits.h)
EX_USAGE       = 64  #- command line usage error -#
EX_UNAVAILABLE = 69  #- service unavailable -#
EX_CONFIG      = 78  #- configuration error -#

#** Functions **#

def split_arguments(
    cmd:  CommandBase,
    args: Args
) -> Tuple[Optional[Command], Args, Args]:
    """
    split arguments into current command values and next command arguments

    :param cmd:  command being evaluated for currently
    :param args: args to split into related values and non-related values
    :return:     (next-command <if any>, related-values, unrelated-values)
    """
    args.pop(0)
    indexes = sorted([
        (c,i)
        for c,i in ((c,c.index(args)) for c in cmd.commands)
        if i != -1
    ], key=lambda x: x[1])
    next_cmd, idx = indexes[0] if indexes else (None, len(args))
    return (next_cmd, args[:idx], args[idx:])

def parse_flags(flags: Flags, args: Args) -> FlagDict:
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
        # if flag is present
        if index != -1:
            # check if flag appears more than once
            if flag.index(args[index+1:]) != -1:
                raise UsageError(f'flag: {flag.name} declared more than once')
            # raise error if indexes overlap or value isnt given
            if flag.has_value and (len(args) <= index+1 or index+1 in indexes):
                raise UsageError(f'flag: {flag.name} no value specified')
            # append index otherwise
            indexes.append((flag, index))
        # if flag has default
        elif flag.default is not None:
            fdict[flag.names[0]] = flag.default
        # if flag is required
        elif flag.required:
            raise UsageError(f'flag: {flag.name} is required')
    # collect values from indexes (from highest to lowest)
    for flag, idx in sorted(indexes, key=lambda x: x[1], reverse=True):
        # attempt to get value, convert, and set in values
        if flag.has_value:
            # attempt to parse value
            raw = args.pop(idx+1)
            val = flag.convert(raw)
            if val is None:
                raise UsageError(f'flag: {flag.name} decode failure: {raw}')
            fdict[flag.names[0]] = val
        # if no-value is possible, set to true
        else:
            fdict[flag.names[0]] = True
        args.pop(idx)
    # iterate the arguments for any non-parsed flags
    for arg in args:
        if arg.startswith('-'):
            raise NotFoundError(arg)
    # return parsed values
    return fdict

def has_help_flag(gflags: dict) -> bool:
    """
    check if the given global flags contain the help flag

    :param gflags: parsed global flags
    :return:       true if `help` flag is found
    """
    return bool(gflags.get(help_flag.names[0]))

async def run_app(app: 'App', args: List[str]):
    """
    iterate args until given commands and correlated flags are executed

    :param app:  application w/ flag/command definitions
    :param args: arguments to parse according to app definition
    """
    try:
        # validate application configuration before executing
        app.validate()
        # evaluate and run commands based on cli data
        (next_cmd, ctx, ret, gflags) = (app, Context(app, app), None, None)
        while next_cmd is not None:
            (cmd, parent) = (next_cmd, ctx)
            # split args into next-command args and current args
            next_cmd, values, args = split_arguments(cmd, args)
            # collect flags from values
            flags = parse_flags(cmd.flags, values)
            # pass content into new context
            if gflags is None:
                gflags = flags
            ctx = Context(app, cmd, parent, gflags, flags, Args(values))
            # only run command if no subcommand is present or parent is allowed
            if (next_cmd is None and not has_help_flag(gflags)) or cmd.allow_parent:
                await cmd.run_before(ctx)
                ret = await cmd.run_action(ctx)
                await cmd.run_after(ctx)
        # raise help if help-flag was given
        if has_help_flag(gflags):
            help_action(ctx, cmd)
        # raise help if no action was taken at all
        elif ret == NO_ACTION:
            raise UsageError('no action taken')
    except UsageError as e:
        app.on_usage_error(ctx, cmd, str(e))
    except ExitError as e:
        app.exit_with_error(ctx, cmd, e.args[0], e.args[1])
    except NotFoundError as e:
        app.not_found_error(ctx, cmd, str(e))
    except ConfigError as e:
        print(f'ConfigError: {e}', file=app.err_writer)
        raise SystemExit(EX_CONFIG)
