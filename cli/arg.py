"""
CLI Argument Implementation and DataType Parsers
"""
from typing import Any, Callable, Generic, List, Optional, Type

from . import T, SuggestFunc, get_type, get_suggestor, get_validator

#** Variables **#
__all__ = ['Arg', 'Args']

Args = List['Arg']

#** Classes **#

class Arg(Generic[T]):
    """
    """
    type: Type[T]

    def __init__(self,
        name:       str,
        about:      Optional[str]                      = None,
        default:    Optional[T]                        = None,
        required:   Optional[bool]                     = None,
        repeat:     bool                               = False,
        validators: Optional[List[Callable[[Any], T]]] = None,
        suggestor:  Optional[SuggestFunc]              = None,
        type:       Optional[Type[T]]                  = None,
    ):
        self.name       = name
        self.about      = about
        self.default    = default
        self.required   = self.default is None if required is None else required
        self.repeat     = repeat
        self.validators = validators or []
        self.type       = get_type(self, type)
        self.suggestor  = suggestor or get_suggestor(self.type)
        self.validators = get_validator(self.type, self.validators)

    def __repr__(self) -> str:
        return f'Arg(name={self.name}, default={self.default})'

    @classmethod
    def __class_getitem__(cls, value: Type):
        func     = getattr(super(), '__class_getitem__')
        instance = func(value)
        instance.type = value
        return instance
