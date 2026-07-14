"""
CLI Flag Implementation
"""
from typing import (
    Any, Callable, Generic, List, Literal, Optional, Tuple, Type,
    cast, get_args)

from . import T, SuggestFunc, get_type, get_validator

#** Variables **#
__all__ = ['Flag', 'Flags']

Flags = List['Flag']
Short = Literal[
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
    'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

#** Functions **#

def flag_default(type: Type[T], value: Any) -> Optional[T]:
    """
    determine default based on type and value
    """
    if type is bool and value is None:
        return cast(T, False)
    return value

def parse_short(name: str) -> Tuple[str, Optional[Short]]:
    """
    parse short included with name (if specified)

    example: `name, n` = (long=name, short=n)
    """
    comma = name.count(',')
    if comma > 1:
        raise ValueError(f'Invalid flag name: {name!r}')
    if comma == 0:
        return (name, None)
    long, short = name.split(',', 1)
    long, short = long.strip(), short.strip()
    if short not in get_args(Short):
        raise ValueError(f'Invalid short flag: {short!r}')
    return (long, cast(Short, short))

#** Classes **#

class Flag(Generic[T]):
    """
    """
    type: Type[T]

    def __init__(self,
        name:       str,
        about:      Optional[str]                      = None,
        default:    Optional[T]                        = None,
        required:   bool                               = False,
        repeat:     bool                               = False,
        short:      Optional[Short]                    = None,
        long:       Optional[str]                      = None,
        hidden:     bool                               = False,
        validators: Optional[List[Callable[[Any], T]]] = None,
        suggestor:  Optional[SuggestFunc]              = None,
        type:       Optional[Type[T]]                  = None,
    ):
        name, name_short = parse_short(name)
        self.name        = name
        self.about       = about or ''
        self.required    = required
        self.repeat      = repeat
        self.short       = short or name_short
        self.long        = long or name
        self.hidden      = hidden
        self.validators  = validators or []
        self.suggestor   = suggestor
        self.type        = get_type(self, type)
        self.validators  = get_validator(self.type, self.validators)
        self.default     = flag_default(self.type, default)

    def __repr__(self) -> str:
        attrs = {'name': self.name, 'short': self.short, 'long': self.long}
        items = ', '.join(f'{k}={v}' for k,v in attrs.items() if v)
        return f'Flag({items})'

    @classmethod
    def __class_getitem__(cls, value: Type):
        func     = getattr(super(), '__class_getitem__')
        instance = func(value)
        instance.type = value
        return instance

    def _requires_value(self) -> bool:
        """
        """
        return self.type is not bool

    def variants(self) -> List[str]:
        """
        """
        names = [f'--{self.long}']
        if self.short is not None:
            names.insert(0, f'-{self.short}')
        return names
