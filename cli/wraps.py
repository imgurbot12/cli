"""
Function Command Wrapper Utilities
"""
import functools
from typing import *
from datetime import timedelta

from .app import App
from .context import Context
from .command import Action, Command, wrap_async
from .argument import *

#** Variables **#
__all__ = [
    'Decimal',
    'Duration',
    'NewFile',
    'ExistingFile',

    'app',
    'action',
    'command',
]

null = type(None)

# custom typevars for associated translation functions
Decimal      = TypeVar('Decimal')
Duration     = TypeVar('Duration')
NewFile      = TypeVar('NewFile')
ExistingFile = TypeVar('ExistingFile')

#** Functions **#

def inspectfunc(func: Callable) -> Tuple[list, dict, dict]:
    """
    parse and retrieve list of argument names alongside argument typehints

    :param func: function being inspected for argument details
    :return:     (list of args, defaults-dict, typehint-dict)
    """
    # retrieve args from __varnames__ if func was run through `wrap_async`
    args           = getattr(func, '__varnames__', func.__code__.co_varnames)
    defaults       = func.__defaults__ or []
    typehints      = func.__annotations__
    default_dict   = dict(zip(args[-len(defaults):], defaults))
    # determine typehint of arg based on default if not already specified
    for name in (name for name in args if name not in typehints):
        typehints[name] = type(default_dict.get(name, ''))
    return args, default_dict, typehints

def compile_typehint(attr: str, hint: Any, depth: int = 0) -> TypeFunc:
    """
    compile the given attribute's typehint into a string-to-type function

    :param attr:  attribute name associated w/ typehint
    :param hint:  typehint being compiled into typefunc
    :param depth: recursion depth of function (used for debug)
    :return:      compiled typefunction
    """
    # ignore special variables like `Context`
    if hint in (Context, ):
        return
    # parse basic typehints
    if hint in (str, bytes, bytearray, int, float):
        return hint
    if hint in (set, list, tuple):
        return parse_list_function(str, hint)
    if hint == bool:
        return parse_bool
    if hint == Decimal:
        return parse_decimal
    if hint in (Duration, timedelta):
        return parse_duration
    if hint == NewFile:
        return parse_new_file
    if hint == ExistingFile:
        return parse_existing_file
    # parse complex typehints
    origin, args = get_origin(hint), get_args(hint)
    if origin in (set, list, tuple):
        func = compile_typehint(attr, args[0], depth+1)
        return parse_list_function(func, origin)
    raise ValueError(f'{attr!r} uses an unsupported typehint: {hint}')

def compile_command_values(
    names: List[str],
    hints: List[Any],
    funcs: List[TypeFunc]
) -> Action:
    """
    convert values according to their typefunctions

    :param names: argument names associated w/ values
    :param hints: typehints associated with values
    :param funcs: functions used to translate values accordingly
    :return:      command action that parses and saves argument values
    """
    def validate_values(ctx: Context) -> List[Any]:
        values, tracked = [], 0
        for n, (name, hint, func) in enumerate(zip(names, hints, funcs), 1):
            # pass context in if hint is for context
            if hint == Context:
                values.append(ctx)
                continue
            # retrieve value from args if exists
            val = ctx.args.get(tracked)
            if val is None:
                continue
            # attempt convert args as standard
            try:
                values.append(func(val))
                tracked += 1
            except ArgumentError as err:
                ctx.on_usage_error(f'argument name={name}, {err}')
            except Exception:
                htype = getattr(hint, '__name__', hint)
                ctx.on_usage_error(
                    f'argument name={name} value={val!r} is an invalid {htype}'
                )
        return values
    return validate_values

def compile_command_usage(action: Action) -> str:
    """
    compile command usage from action docstring

    :param action: action function being evaluated
    :return:       generated command usage
    """
    usage, doc = '', action.__doc__ or ''
    for line in (line.strip() for line in doc.splitlines()):
        if not line or any(line.startswith(c) for c in '@:'):
            continue
        usage += line + ' '
    return usage.strip()

def compile_command_argsusage(action: Action) -> str:
    """
    compile command argsusage from action argument information

    :param action: action function being evaluated
    :return:              generated command argsusage
    """
    usage = []
    for arg in action.arguments:
        if arg in action.defaults:
            usage.append('[arguments...]')
            break
        usage.append(f'[{arg}]')
    usage.append('[flags...]')
    return ' '.join(usage)

def action(func: Callable) -> Action:
    """
    wrap python function as standard command action

    :param func: function being wrapped and converted into command action
    :return:     generated function command action
    """
    func                      = wrap_async(func)
    args, defaults, typehints = inspectfunc(func)
    # generate argument type converters/validators
    typelist        = [typehints[name] for name in args]
    funclist        = [compile_typehint(name, typehints[name]) for name in args]
    validate_values = compile_command_values(args, typelist, funclist)
    # generate argument number validator
    max_args        = len([f for f in funclist if f])
    arg_diff        = len(funclist) - max_args
    max_args        = len([f for f in funclist if f])
    min_args        = sum(1 for a in args if a not in defaults) - arg_diff
    validate_argnum = range_args(min_args, max_args)
    # complete action translation
    @functools.wraps(func)
    async def action(ctx: Context):
        validate_argnum(ctx)
        return await func(*validate_values(ctx))
    # export a few variables for command generation
    action.defaults  = defaults
    action.arguments = [arg for n, arg in enumerate(args, 0) if funclist[n]]
    # return generated action function
    return action

def command(
    parent:    Command,
    aliases:   Optional[list] = None,
    usage:     Optional[str]  = None,
    argsusage: Optional[str]  = None,
    category:  str            = '*',
    hidden:    Optional[bool] = None,
):
    """
    dynamically generate a cli-command from the decorated function

    :param aliases:   name aliases assigned to command
    :param usage:     specified command usage description
    :param argsusage: specified command argsusage description
    :param category:  command category assignment
    :param hidden:    control if command is hidden from help
    :return:          decorator that returns generated command object
    """
    def decorator(func: Callable) -> Command:
        fname   = func.__name__
        main    = action(func)
        command = Command(
            name=fname.strip('_'),
            aliases=aliases or [],
            category=category,
            usage=usage or compile_command_usage(main),
            argsusage=argsusage or compile_command_argsusage(main),
            hidden=fname.startswith('_') if hidden is None else hidden,
            action=main,
        )
        parent.commands.append(command)
        return command
    return decorator

def app(
    name:        Optional[str]  = None,
    usage:       Optional[str]  = None,
    version:     Optional[str]  = None,
    argsusage:   Optional[str]  = None,
    description: Optional[str]  = None,
    email:       Optional[str]  = None,
    authors:     Optional[list] = None,
    copyright:   Optional[str]  = None,
) -> App:
    """
    dynamically generate a simple cli-application from the decorated function

    :param name:        assigned name of application
    :param usage:       specified application usage description
    :param version:     symantic version of application
    :param argsusage:   specified application argsusage description
    :param description: detailed description of application
    :param email:       primary email associated w/ application
    :param authors:     list of authors associated w/ application
    :param copyright:   copyright linked with application
    :return:            decorator that returns generated application object
    """
    def decorator(func: Callable) -> App:
        cname = name or func.__name__.strip('_')
        main  = action(func)
        return App(
            name=cname,
            usage=usage or compile_command_usage(main),
            version=version or '0.0.1',
            argsusage=argsusage or compile_command_argsusage(main),
            description=description,
            authors=authors or [],
            email=email,
            copyright=copyright,
            action=main,
        )
    return decorator
