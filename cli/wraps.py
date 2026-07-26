"""
CLI Action Argument Construction Wrappers
"""
import asyncio
import inspect
import functools
from typing import (
    Any, Callable, Dict, List, NamedTuple, Optional, Set, Type, TypeVar)
from typing_extensions import Annotated, get_args, get_origin

from .arg import Arg
from .flag import Flag
from .cmd import Action, AsyncAction, Command
from .context import Context

#** Variables **#
__all__ = [
    'Doc',
    'Inspected',
    'Extra',

    'wrap_async',
    'get_signature',
    'parse_doc',
    'into_command',
    'wrap_ctx',
]

R = TypeVar('R')

#: hidden attribute tied to context wrapper
WRAP_CTX_ATTR = '__cli_wrapped_ctx'

#: hidden attribute used to cache arg definitions
ARG_ATTR = '__cli_arg'

#: hidden attribute used to cache flag definitions
FLAG_ATTR = '__cli_flags'

#: hidden attribute used to cache extra definitions
EXTRA_ATTR = '__cli_extra'

#** Classes **#

class Doc(NamedTuple):
    about:  str
    params: Dict[str, str]

class Inspected(NamedTuple):
    args:      List[str]
    kwargs:    List[str]
    arg_splat: Optional[str]
    kw_splat:  Optional[str]
    defaults:  Dict[str, Any]
    typehints: Dict[str, Type]

class Extra:
    pass

#** Functions **#

def wrap_async(action: Action) -> AsyncAction:
    """
    convert action into async-action

    :param action: action callback
    :return:       async action callback
    """
    if inspect.iscoroutinefunction(action):
        return action

    @functools.wraps(action)
    async def inner(*args, **kwargs):
        await asyncio.to_thread(action, *args, **kwargs)
    return inner

@functools.lru_cache(maxsize=None)
def get_signature(callable: Callable) -> Inspected:
    """
    """
    sig       = inspect.signature(callable)
    args      = []
    kwargs    = []
    defaults  = {}
    typehints = {}
    arg_splat = None
    kw_splat  = None
    for p in sig.parameters.values():
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
            args.append(p.name)
        elif p.kind == p.KEYWORD_ONLY:
            kwargs.append(p.name)
        elif p.kind == p.VAR_POSITIONAL:
            arg_splat = p.name
        elif p.kind == p.VAR_KEYWORD:
            kw_splat = p.name
        if p.annotation != p.empty:
            typehints[p.name] = p.annotation
        if p.default != p.empty:
            defaults[p.name] = p.default
            if p.name not in typehints:
                typehints[p.name] = type(p.default)
    return Inspected(args, kwargs, arg_splat, kw_splat, defaults, typehints)

@functools.lru_cache(maxsize=None)
def parse_doc(callable: Callable):
    """
    """
    doc   = callable.__doc__ or ''
    about = []
    strip = '@:<{}[]- \t\r'
    descriptions = {}
    for line in doc.splitlines():
        line = line.strip()
        if not line:
            continue

        if not line.startswith(':'):
            about.append(line)
            continue

        details = line.strip('@:').strip().split(' ', 2)
        if details[0].lower() != 'param':
            continue

        table        = any(details[1].startswith(c) for c in '{<[:')
        param, usage = details[2].split(' ', 1) if table else tuple(details[1:])
        descriptions[param.strip(strip)] = usage.strip(strip)
    return Doc(' '.join(about), descriptions)

def is_context(typedef: Type) -> bool:
    """
    check if the given typdef annotation is context
    """
    return inspect.isclass(typedef) and issubclass(typedef, Context)

def is_extra(typedef: Type) -> bool:
    """
    check if the given typedef annotation is extra
    """
    return get_origin(typedef) is Annotated \
        and any(isinstance(arg, Extra) for arg in get_args(typedef))

def into_command(callable: Callable, cls: Type[Command] = Command) -> Command:
    """
    convert function into a command definition using function doc/signature

    :param callable: function to convert to a command
    :param cls:      command class factory
    :return:         command generated from function
    """
    doc           = parse_doc(callable)
    signature     = get_signature(callable)
    args          = []
    flags         = []
    extra: Set[str] = getattr(callable, EXTRA_ATTR, set())
    args_default    = getattr(callable, ARG_ATTR, {})
    flags_default   = getattr(callable, FLAG_ATTR, {})
    for name in signature.args:
        typedef = signature.typehints.get(name, str)
        if name in extra or is_context(typedef) or is_extra(typedef):
            continue
        kwargs = args_default.get(name) or {}
        about  = kwargs.pop('about', None) or doc.params.get(name) or ''
        args.append(Arg(
            name=name,
            about=about,
            default=signature.defaults.get(name, None),
            type=typedef,
            **kwargs
        ))

    for name in signature.kwargs:
        typedef = signature.typehints.get(name, str)
        if name in extra or is_context(typedef) or is_extra(typedef):
            continue
        kwargs   = flags_default.get(name) or {}
        about    = kwargs.pop('about', None) or doc.params.get(name) or ''
        required = kwargs.pop('required', None) or (name not in signature.defaults)
        flags.append(Flag(
            name=name,
            about=about,
            default=signature.defaults.get(name, None),
            required=required,
            type=typedef,
            **kwargs
        ))

    if signature.arg_splat is not None:
        name    = signature.arg_splat
        typedef = signature.typehints.get(name, str)
        kwargs  = args_default.get(name) or {}
        about   = kwargs.pop('about', None) or doc.params.get(name) or ''
        args.append(Arg(
            name=name,
            about=about,
            default=signature.defaults.get(name, None),
            type=typedef,
            repeat=True,
            **kwargs
        ))
    return cls(
        name=callable.__name__,
        about=doc.about,
        args=args,
        flags=flags,
        action=callable,
    )

def wrap_ctx(callable: Callable[..., R]) -> Callable[[Context], R]:
    """
    wrap function in handler that unwraps the context into its relevant args

    :param callable: original function to wrap
    :return:         wrapped function
    """
    if hasattr(callable, WRAP_CTX_ATTR):
        return callable

    signature = get_signature(callable)
    def inner(ctx: Context) -> R:
        used = set()
        args = []
        for arg in signature.args:
            cast  = signature.typehints[arg]
            value = ctx.get(arg, cast)
            used.add(arg)
            args.append(value)
        kwargs = {}
        for kwarg in signature.kwargs:
            cast  = signature.typehints[kwarg]
            value = ctx.get(kwarg, cast)
            used.add(kwarg)
            kwargs[kwarg] = value
        if signature.arg_splat is not None:
            splat: Optional[List] = ctx.get(signature.arg_splat, default=None)
            if splat is None:
                splat = []
                for key, value in ctx.args.items():
                    if key not in signature.args:
                        used.add(key)
                        splat.append(value)
            else:
                used.add(signature.arg_splat)
            args.extend(splat)
        if signature.kw_splat is not None:
            for key, value in ctx.args.items():
                if key not in used and key not in kwargs:
                    kwargs[key] = value
            for key, value in ctx.flags.items():
                if key not in used and key not in kwargs:
                    kwargs[key] = value
            for key, value in ctx.extra.items():
                if key not in used and key not in kwargs:
                    kwargs[key] = value
        return callable(*args, **kwargs)

    setattr(inner, WRAP_CTX_ATTR, True)
    return inner
