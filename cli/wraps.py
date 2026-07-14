"""
CLI Action Argument Construction Wrappers
"""
import inspect
import functools
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Type, TypeVar

from . import Context

#** Variables **#

R = TypeVar('R')

#** Classes **#

class Inspected(NamedTuple):
    args:      List[str]
    kwargs:    List[str]
    arg_splat: Optional[str]
    kw_splat:  Optional[str]
    defaults:  Dict[str, Any]
    typehints: Dict[str, Type]

#** Functions **#

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

def wraps(callable: Callable[..., R]) -> Callable[[Context], R]:
    """
    """
    if hasattr(callable, '__cli_wrapped'):
        return callable
    signature = get_signature(callable)
    def inner(ctx: Context):
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

    setattr(inner, '__cli_wrapped', True)
    return inner
