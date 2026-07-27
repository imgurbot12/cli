"""
CLI Argument Implementation and DataType Parsers
"""
from typing import Any, Callable, Generic, List, Optional, Type

from . import T, OptSuggest, get_type, get_suggestor, get_validator

#** Variables **#
__all__ = ['Arg', 'Args']

Args = List['Arg']

#** Classes **#

class Arg(Generic[T]):
    """
    Command Argument Configuration Setting
    """
    type:      Type[T]
    suggestor: OptSuggest

    def __init__(self,
        name:       str,
        about:      Optional[str]                      = None,
        default:    Optional[T]                        = None,
        required:   Optional[bool]                     = None,
        repeat:     bool                               = False,
        validators: Optional[List[Callable[[Any], T]]] = None,
        suggestor:  OptSuggest                         = None,
        type:       Optional[Type[T]]                  = None,
    ):
        """
        :param name:       name of argument
        :param about:      description of argument
        :param default:    default value assigned to argument
        :param required:   label if argument is required during parsing
        :param repeat:     allow argument to be repeated
        :param validators: validators used to process argument value
        :param suggestor:  argument auto-complete suggestion function
        :param type:       argument type assignment
        """
        self.name       = name
        self.about      = about
        self.default    = default
        self.required   = self.default is None if required is None else required
        self.repeat     = repeat
        self.validators = validators or []
        self.suggestor  = suggestor
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

    def __repr__(self) -> str:
        return f'Arg(name={self.name}, default={self.default})'

    @classmethod
    def __class_getitem__(cls, value: Type):
        func     = getattr(super(), '__class_getitem__')
        instance = func(value)
        instance.type = value
        return instance
