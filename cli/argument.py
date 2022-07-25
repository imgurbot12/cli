"""
argument parsers and implementations for special types
"""
import re
from typing import *
from datetime import timedelta

#** Variables **#
__all__ = [
    'TypeFunc',

    'parse_bool',
    'parse_decimal',
    'parse_duration',
    'parse_list_function',

    'range_args',
    'exact_args',
    'no_args',
]

#: regex parser for duration string
re_duration = re.compile(
    r'^(?P<weeks>\d+w)?'
    r'(?P<days>\d+d)?'
    r'(?P<hours>\d+h)?'
    r'(?P<minutes>\d+m)?'
    r'(?P<seconds>\d+s)?$'
)

#: type defintion for typehint translation for cli
TypeFunc = Callable[[str], Any]

#** Functions **#

def parse_bool(boolean: str) -> bool:
    """
    parse boolean string into bool value

    :param boolean: bool string
    :return:        string boolean value
    """
    if boolean.lower() in ('0', 'false'):
        return False
    if boolean.lower() in ('1', 'true'):
        return True
    raise ValueError(f'invalid boolean string: {boolean!r}')

def parse_decimal(decimal: str, digits: int = 2) -> float:
    """
    parse decimal string into float value

    :param decimal: decimal string
    :return:        decimal float value
    """
    return round(float(decimal), digits)

def parse_duration(duration: str) -> timedelta:
    """
    parse duration string into timedelta value

    :param duration: duration string
    :return:         parsed timedelta value
    """
    match  = re_duration.match(duration).groupdict()
    kwargs = {k:int(v.strip('wdhms') if v else 0) for k,v in match.items()}
    return timedelta(**kwargs)

def parse_list_function(typefunc: TypeFunc, origin: type = list) -> TypeFunc:
    """
    generate list parser function with the given typefunc

    :param typefunc: type-function to convert string into new value
    :param origin:   type to convert list into (set, list, tuple)
    :return:         function to parse a list into a list of a specified type
    """
    return lambda l: origin([typefunc(v) for v in l.split(',')])

def range_args(min: int = 0, max: Optional[int] = None) -> Callable:
    """
    generate before action function to validate the number of arguments

    :param min: minimum number of arguments
    :param max: maximum number of arguments
    :return:    function used to regulate argument numbers
    """
    def validate_range_args(ctx: 'Context'):
        if min < 0 and len(ctx.args) > 0:
            ctx.on_usage_error('action does not take any arguments')
        if min > 0 and len(ctx.args) < min:
            ctx.on_usage_error(f'action must have at least {min} arguments')
        if max and len(ctx.args) > max:
            ctx.on_usage_error(f'action can have at maximum {max} arguments')
    return validate_range_args

def exact_args(num: int) -> Callable:
    """
    generate before action function to validate the exact of arguments

    :param num: number of allowed arguments
    :return:    function used to regulate argument numbers
    """
    def validate_exact_args(ctx: 'Context'):
        if len(ctx.args) != num:
            ctx.on_usage_error(f'action must have exactly {num} arguments')
    return validate_exact_args

#: public action validator to ensure no arguments are passed
no_args = range_args(-1)