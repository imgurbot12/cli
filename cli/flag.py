"""
CLI Flag Implementation
"""
from typing import (
    Any, Callable, Generic, List, Literal, Optional, Tuple, Type,
    cast, get_args)

from . import T, OptSuggest, get_type, get_suggestor, get_validator

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
    Command Flag/Option Configuration Setting
    """
    type:      Type[T]
    suggestor: OptSuggest

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
        suggestor:  OptSuggest                         = None,
        type:       Optional[Type[T]]                  = None,
    ):
        """
        :param name:       name of flag
        :param about:      description of flag
        :param default:    default value assigned to flag
        :param required:   label if flag is required during parsing
        :param repeat:     allow flag to be repeated
        :param short:      flag short variant
        :param long:       flag long variant
        :param hidden:     hide flag in help if true
        :param validators: validators used to process flag value
        :param suggestor:  flag auto-complete suggestion function
        :param type:       flag type assignment
        """
        name, name_short = parse_short(name)
        self.name        = name
        self.about       = about or ''
        self.default     = default
        self.required    = required
        self.repeat      = repeat
        self.short       = short or name_short
        self.long        = long or name
        self.hidden      = hidden
        self.validators  = validators.copy() if validators else []
        self.suggestor   = suggestor
        self._set_type(type)

    def _set_type(self, typedef: Optional[Type]):
        """
        type assignment and all related attributes that pull from type
        """
        newtype, meta   = get_type(self, typedef)
        self.type       = newtype
        self.repeat     = self.repeat or meta.repeat
        self.suggestor  = get_suggestor(self.type, self.suggestor)
        self.validators = get_validator(self.type, self.validators)
        self.default    = flag_default(self.type, self.default)

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
        return if flag requires a value or not based on type
        """
        return self.type is not bool

    def variants(self) -> List[str]:
        """
        short and long flag variants of this flag
        """
        names = [f'--{self.long}']
        if self.short is not None:
            names.insert(0, f'-{self.short}')
        return names
