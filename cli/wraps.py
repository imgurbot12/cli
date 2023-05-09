"""
Function Command Wrapper Utilities
"""
import inspect
import functools
from typing import *
from datetime import timedelta

from .abc import *
from .app import App
from .flag import Flag
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

#: typehint for none-type
Null = type(None)

# custom typevars for associated translation functions
Decimal      = NewType('Decimal', float)
Duration     = NewType('Duration', str)
NewFile      = NewType('NewFile', str)
ExistingFile = NewType('ExistingFile', str)

class Inspected(NamedTuple):
    args:      List[str]
    kwargs:    List[str]
    defaults:  Dict[str, Any]
    typehints: Dict[str, Type]

class ActionCtx(NamedTuple):
    flags:     Flags
    defaults:  Dict[str, Any]
    arguments: List[str]

#** Functions **#

def is_union(origin: type) -> bool:
    """
    python3 compatable way of searching for union types
    """
    return 'Union' in str(origin) or 'Union' in type(origin).__name__

def inspectfunc(func: Callable) -> Inspected:
    """
    parse and retrieve list of argument names alongside argument typehints

    :param func: function being inspected for argument details
    :return:     (list of args, list of kwargs, defaults-dict, typehint-dict)
    """
    sig       = inspect.signature(func)
    params    = sig.parameters.values()
    args      = [p.name for p in params if p.kind == p.POSITIONAL_OR_KEYWORD]
    kwargs    = [p.name for p in params if p.kind == p.KEYWORD_ONLY]
    defaults  = {p.name:p.default for p in params if p.default != p.empty}
    typehints = {p.name:p.annotation for p in params if p.annotation != p.empty}
    # determine typehint of arg based on default if not already specified
    for name in (name for name in args if name not in typehints):
        typehints[name] = type(defaults.get(name, ''))
    return Inspected(args, kwargs, defaults, typehints)

def compile_typehint(attr: str, hint: Any, depth: int = 0) -> Optional[TypeFunc]:
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
    if hint in (str, int, float):
        return hint
    if hint in (bytes, bytearray):
        return parse_bytes_function(hint)
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
        if func is None:
            raise ValueError(f'{attr!r} uses invalid typehint: {args[0]!r}')
        return parse_list_function(func, origin)
    # support `Optional[<hint>]` or `<hint> | None` types
    if is_union(origin) and len(args) == 2 and args[1] is Null:
        return compile_typehint(attr, args[0], depth=depth+1)
    raise ValueError(f'{attr!r} uses an unsupported typehint: {hint}')

def compile_command_arg_validator(
    names: List[str],
    hints: List[Any],
    funcs: List[Optional[TypeFunc]]
) -> Callable[[Context], List[Any]]:
    """
    convert values according to their typefunctions

    :param names: argument names associated w/ values
    :param hints: typehints associated with values
    :param funcs: functions used to translate values accordingly
    :return:      command action that parses and saves argument values
    """
    def validate_values(ctx: Context) -> List[Any]:
        values, tracked = [], 0
        for (name, hint, func) in zip(names, hints, funcs):
            # pass context in if hint is for context
            if func is None:
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

def compile_command_flags(
    func:     Callable,
    names:    List[str],
    hints:    List[Any],
    funcs:    List[Optional[TypeFunc]],
    defaults: Dict[str, Any],
    is_app:   bool = False
) -> Flags:
    """
    compile command flags based on given configuration

    :param names:    list of parameter names
    :param hints:    list of typehints for parameters
    :param funcs:    parse functions to use in flag object
    :param defaults: default values for associated parameter names
    :param is_app:   boolean flag to tweak short name generation
    :return:         list of generated flag objects
    """
    # parse function doc to search for flag descriptions
    descriptions, doc = {}, func.__doc__ or ''
    for line in (line.strip() for line in doc.splitlines()):
        if not line or not any(line.startswith(c) for c in '@:'):
            continue
        # skip if document is not a parameter
        details = line.strip('@:').strip().split(' ', 2)
        if details[0].lower() != 'param':
            continue
        # parse description from line
        strip        = '@:<{}[]- \t\r'
        tlbl         = any(details[1].startswith(c) for c in '{<[:')
        param, usage = details[2].split(' ', 1) if tlbl else tuple(details[1:])
        # assign param/usage to description table
        descriptions[param.strip(strip)] = usage.strip(strip)
    # generate flags
    flags  = []
    shorts = [] if not is_app else ['h']
    for name, hint, parser in zip(names, hints, funcs):
        if func is None:
            continue
        # set shortform if first letter is unique
        fname = name.strip('_')
        short = fname.lower()[0]
        short = short if short not in shorts else ''
        shorts.append(short)
        # generate flag object
        is_bool = hint == bool
        flags.append(Flag(
            name=f'{fname}, {short}' if short else fname,
            usage=descriptions.get(name),
            default=defaults.get(name),
            hidden=name.startswith('_'),
            type=hint,
            has_value=not is_bool,
            parser=parser,
        ))
    return flags

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

def compile_command_argsusage(action_ctx: ActionCtx) -> str:
    """
    compile command argsusage from action argument information

    :param action: action function being evaluated
    :return:              generated command argsusage
    """
    usage = []
    for arg in action_ctx.arguments:
        if arg in action_ctx.defaults:
            usage.append('[arguments...]')
            break
        usage.append(f'[{arg}]')
    usage.append('[flags...]')
    return ' '.join(usage)

def action(func: Callable, is_app: bool = False) -> Tuple[AsyncAction, ActionCtx]:
    """
    wrap python function as standard command action

    :param func:   function being wrapped and converted into command action
    :param is_app: tweak command and flag generation when building app action
    :return:       generated function command action
    """
    func = wrap_async(func)
    spec = inspectfunc(func)
    # generate argument type converters/validators
    arghints      = [spec.typehints[name] for name in spec.args]
    arglist       = [compile_typehint(*args) for args in zip(spec.args, arghints)]
    validate_args = compile_command_arg_validator(spec.args, arghints, arglist)
    # fill out any flag fields w/ their associated data
    fhints = [spec.typehints[name] for name in spec.kwargs] 
    flist  = [compile_typehint(*args) for args in zip(spec.kwargs, fhints)]
    flags  = compile_command_flags(func, spec.kwargs, fhints, flist, spec.defaults, is_app)
    # generate argument number validator
    max_args        = sum(1 for func in arglist if func is not None)
    arg_diff        = len(arglist) - max_args
    max_args        = len([f for f in arglist if f])
    min_args        = sum(1 for a in spec.args if a not in spec.defaults) - arg_diff
    validate_argnum = range_args(min_args, max_args)
    # complete action translation
    @functools.wraps(func)
    async def action(ctx: Context):
        validate_argnum(ctx)
        args   = validate_args(ctx)
        names  = [flag.long for flag in flags]
        kwargs = {name:ctx.get(name) for name in names}
        return await func(*args, **kwargs)
    # return generated action function
    arguments = [arg for arg, hint in zip(spec.args, arglist) if hint]
    return action, ActionCtx(flags.copy(), spec.defaults, arguments)

def command(
    parent:       AbsCommand,
    name:         Optional[str]  = None,
    aliases:      Optional[list] = None,
    usage:        Optional[str]  = None,
    argsusage:    Optional[str]  = None,
    category:     str            = '*',
    hidden:       Optional[bool] = None,
    allow_parent: bool           = False
) -> CommandFunc:
    """
    dynamically generate a cli-command from the decorated function

    :param name:         name override for command
    :param aliases:      name aliases assigned to command
    :param usage:        specified command usage description
    :param argsusage:    specified command argsusage description
    :param category:     command category assignment
    :param hidden:       control if command is hidden from help
    :param allow_parent: allow parent to run if subcommand is also run
    :return:             decorator that returns generated command object
    """
    def decorator(func: Callable) -> Command:
        fname     = func.__name__
        main, ctx = action(func)
        command = Command(
            name=name or fname.strip('_'),
            aliases=aliases or [],
            category=category,
            usage=usage or compile_command_usage(main),
            argsusage=argsusage or compile_command_argsusage(ctx),
            hidden=fname.startswith('_') if hidden is None else hidden,
            allow_parent=allow_parent,
            action=main,
            flags=ctx.flags,
        )
        parent.commands.append(command)
        return command
    return decorator

@overload
def app(name_or_func: Callable) -> App:
    ...

@overload
def app(
    name_or_func: Optional[str]  = None,
    usage:        Optional[str]  = None,
    version:      Optional[str]  = None,
    argsusage:    Optional[str]  = None,
    description:  Optional[str]  = None,
    email:        Optional[str]  = None,
    authors:      Optional[list] = None,
    copyright:    Optional[str]  = None,
    allow_parent: bool           = False,
    **kwargs:     Any,
) -> AppFunc:
    ...

def app(
    name_or_func: Union[Callable, Optional[str]] = None,
    usage:        Optional[str]  = None,
    version:      Optional[str]  = None,
    argsusage:    Optional[str]  = None,
    description:  Optional[str]  = None,
    email:        Optional[str]  = None,
    authors:      Optional[list] = None,
    copyright:    Optional[str]  = None,
    allow_parent: bool           = False,
    **kwargs:     Any,
) -> Union[App, AppFunc]:
    """
    dynamically generate a simple cli-application from the decorated function

    :param name:         assigned name of application
    :param usage:        specified application usage description
    :param version:      symantic version of application
    :param argsusage:    specified application argsusage description
    :param description:  detailed description of application
    :param email:        primary email associated w/ application
    :param authors:      list of authors associated w/ application
    :param copyright:    copyright linked with application
    :param allow_parent: allow base parent app to run when child command is run
    :param kwargs:       additonal keyword arguments to pass to app definiton
    :return:             decorator that returns generated application object
    """
    func = name_or_func if callable(name_or_func) else None
    name = None if callable(name_or_func) else name_or_func
    def decorator(func: Callable) -> App:
        cname     = name or func.__name__.strip('_')
        main, ctx = action(func, is_app=True)
        return App(
            name=cname,
            usage=usage or compile_command_usage(main),
            version=version or '0.0.1',
            argsusage=argsusage or compile_command_argsusage(ctx),
            description=description,
            authors=authors or [],
            email=email,
            copyright=copyright,
            allow_parent=allow_parent,
            action=main,
            flags=ctx.flags,
            **kwargs,
        )
    return decorator if func is None else decorator(func)
