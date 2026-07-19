"""
Simple Application Command Description for UnitTesting
"""
import logging
from pathlib import Path

from . import User, Repeat
from ... import Arg, Command, Flag
from ...validate import LogLevel

#** Variables **#
__all__ = ['APP_V1']

APP_V1 = Command(
    name='v1',
    about='example application v1',
    args=[],
    flags=[
        Flag[User]('user, u', 'user to run application as', 'root'),
        Flag[LogLevel]('log, l', 'specify loglevel for whole application', logging.DEBUG),
        Flag[bool]('debug, d', 'same as --log debug'),
        Flag[Repeat]('repeat, r', 'repeatable flag', repeat=True),
    ],
    invoke_without_command=True,
    commands=[
        Command(
            name='echo',
            about='repeat something back to the user',
            args=[Arg[str]('test', repeat=True)],
            flags=[
                Flag[bool]('dry, d', 'run dry run'),
                Flag[Path]('file, f', 'file to echo content to'),
            ]
        ),
        Command(
            name='do',
            about='do a specific action',
            flags=[
                Flag[bool]('kill, k', 'end action with "and dies..."'),
            ],
            commands=[
                Command(
                    name='run',
                    about='run a given number of miles',
                    args=[Arg[Repeat]('dist1'), Arg[int]('dist2', default=42)],
                    flags=[
                        Flag[bool]('km', 'use kilometers rather than miles')
                    ]
                ),
                Command(
                    name='fly',
                    about='fly a given number of miles',
                    args=[Arg[int]('dist2')],
                    flags=[
                        Flag[bool]('km', 'use kilometers rather than miles'),
                    ]
                )
            ],
        )
    ],
)
