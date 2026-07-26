"""
Action Based Application Command Description for UnitTesting
"""
import logging
from pathlib import Path
from typing import List, Optional

from . import User, Repeat
from ... import Context, command, extra, option
from ...validate import LogLevel

#** Variables **#
__all__ = ['APP_V2']

@command(invoke_without_command=True)
@option('user', short='u')
@option('log', short='l')
@option('debug', short='d')
@option('repeat', short='r')
def v1(ctx: Context, *,
    user:   User         = 'root',
    log:    LogLevel     = logging.DEBUG,
    debug:  bool         = False,
    repeat: Optional[List[Repeat]] = None,
):
    """
    example application v1

    :param user:   user to run application as
    :param log:    specify loglevel for whole application
    :param debug:  same as --log debug
    :param repeat: repeatable flag
    """
    pass

@v1.command
@option('dry', short='d')
@option('file', short='f')
def echo(*test: str, dry: bool = False, file: Optional[Path] = None):
    """
    repeat something back to the user

    :param dry:  run dry run
    :param file: file to echo content to
    """
    print('echo', test, dry, file)

@v1.command
@option('kill', short='k')
def do(ctx: Context, *, kill: bool = False):
    """
    do a specific action

    :param kill: end action with "and dies..."
    """
    ctx.extra['extra'] = 'ayylmao'
    print('do!', kill)

@do.command
@extra('extra')
def run(dist1: Repeat, dist2: int = 42, *, km: bool = False, extra: str):
    """
    run a given number of miles

    :param km: use kilometers rather than miles
    """
    print('run', dist1, dist2, km, extra)

@do.command
def fly(dist2: int, *, km: bool = False):
    """
    :param km: use kilometers rather than miles
    """
    print('fly', dist2, km)

APP_V2 = v1
