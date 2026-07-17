"""
CLI Utility Functions
"""
from io import TextIOBase
from typing import Any, BinaryIO, TextIO, Union, cast

from .context import get_current_context

#** Variables **#
__all__ = ['echo']

#** Functions **#

def echo(
    *data: Any,
    file:  Union[TextIO, BinaryIO, None] = None,
    err:   bool = False,
    join:  str  = ' ',
    end:   str  = '\n'
):
    """
    cli context based echo command

    :param data: data to echo to configured stdout/stderr
    :param file: file override for echo location
    :param err:  default to stdout or stderr
    :param join: substring to join elements of data
    :param end:  ending suffix for echo
    """
    if file is None:
        ctx  = get_current_context()
        file = ctx.stderr if err else ctx.stdout

    is_binary = not isinstance(file, TextIOBase)
    file      = cast(Union[BinaryIO, TextIO], file)

    bin = []
    for arg in data:
        if not isinstance(arg, (str, bytes, bytearray)):
            arg = str(arg)
        if is_binary:
            arg = arg.encode() if isinstance(arg, str) else arg
            bin.append(arg)
        else:
            arg = arg.decode() if not isinstance(arg, str) else arg
            bin.append(arg)

    j = join.encode() if is_binary else join
    e = end.encode() if is_binary else end

    file.write(j.join(bin) + e) #type: ignore
    file.flush()
