"""
V1 API Application Implementation
"""
import logging

from ... import (
    range_args,
    exact_args,
    App, Command, 
    StringFlag, IntFlag, BoolFlag, FilePathFlag,
)

#** Variables **#
__all__ = ['v1']

#** App **#

v1 = App(
    name='v1',
    usage='example application v1',
    version='0.0.1',
    flags=[
        StringFlag(
            name='user, u',
            usage='user to run application as',
            default='root',
        ),
        IntFlag(
            name='log, l',
            usage='specify loglevel for whole application',
            default=logging.WARNING,
        ),
        BoolFlag(
            name='debug, d',
            usage='same as --log 0',
        )
    ],
    commands=[
        Command(
            name='echo',
            usage='repeat something back to user',
            argsusage='<message...>',
            flags=[
                StringFlag(
                    name='dry, d',
                    usage='run dry run',
                ),
                FilePathFlag(
                    name='file, f',
                    usage='file to echo content to'
                )
            ]
        ),
        Command(
            name='do',
            usage='do a specified action',
            argsusage='<command> <arguments...> <flags...>',
            flags=[
                BoolFlag(
                    name='kill, k',
                    usage='end action with "and dies..."'
                )
            ],
            commands=[
                Command(
                    name='run',
                    usage='run a given number of miles',
                    argsusage='<miles> <flags...>',
                    before=exact_args(1),
                    action=lambda ctx: print('running', file=ctx.app.writer),
                    flags=[
                        BoolFlag(
                            name='km',
                            usage='use kilometers rather than miles',
                        )
                    ]
                ),
                Command(
                    name='fly',
                    usage='fly a given number of miles',
                    argsusage='<miles...> <flags...>',
                    before=range_args(1, 2),       
                    action=lambda ctx: print('flying', file=ctx.app.writer),
                    flags=[
                        BoolFlag(
                            name='km',
                            usage='use kilometers rather than miles',
                        )
                    ]
                ),
            ]
        )
    ]
)
