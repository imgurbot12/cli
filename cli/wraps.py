"""
CLI Action Argument Construction Wrappers
"""
import asyncio
import inspect
import functools
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Type, TypeVar

from .arg import Arg
from .flag import Flag
from .cmd import Action, AsyncAction, Command
from .context import Context

#** Variables **#

R = TypeVar('R')

#: hidden attribute tied to context wrapper
WRAP_CTX_ATTR = '__cli_wrapped_ctx'

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

def into_command(callable: Callable, cls: Type[Command] = Command) -> Command:
    """
    convert function into a command definition using function doc/signature

    :param callable: function to convert to a command
    :param cls:      command class factory
    :return:         command generated from function
    """
    doc       = parse_doc(callable)
    signature = get_signature(callable)
    args      = []
    flags     = []
    for arg in signature.args:
        typedef = signature.typehints.get(arg, str)
        args.append(Arg[typedef](
            name=arg,
            about=doc.params.get(arg, None),
            default=signature.defaults.get(arg, None),
        ))
    for flag in signature.kwargs:
        typedef = signature.typehints.get(flag, str)
        flags.append(Flag[typedef](
            name=flag,
            about=doc.params.get(flag, None),
            default=signature.defaults.get(flag, None),
            required=flag not in signature.defaults,
        ))
    if signature.arg_splat is not None:
        typedef = signature.typehints.get(signature.arg_splat, str)
        args.append(Arg[typedef](
            name=signature.arg_splat,
            about=doc.params.get(signature.arg_splat, None),
            repeat=True,
            required=False,
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
            splat = ctx.get(signature.arg_splat, default=None)
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
