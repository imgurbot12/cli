"""
V2 API Application Implementation
"""
import logging

from ... import NO_ACTION, Context, app

#** Variables **#
__all__ = ['v2']

#** App **#

@app(version='0.0.2')
def v2(*, user: str = 'root', log: int = logging.WARNING, debug: bool = False):
    """
    example application v2
    
    :param user:  user to run application as
    :param log:   specify loglevel for whole application
    :param debug: same as --log 0
    """
    return NO_ACTION

@v2.command()
def echo(ctx: Context, message: str, *, dry: bool = False, file: str = None):
    """
    repeat something back to the user

    :param message: message to echo
    :param dry:     run dry run
    :param file:    file to echo content to
    """
    print(message, file=ctx.app.writer)

@v2.command(name='do')
def docmd(*, kill: bool = False):
    """
    do a specified action

    :param kill: end action with "and dies..."
    """
    return NO_ACTION

@docmd.command()
def run(ctx: Context, miles: int, *, km: bool = False):
    """
    run x number of miles
    
    :param miles: number of miles to run
    :param km:    use kilometers rather than miles
    """
    print('running', file=ctx.app.writer)
    user    = ctx.get_global('user')
    measure = 'kilometers' if km else 'miles'
    print(f'{user} ran {miles} {measure}', file=ctx.app.writer)
    if ctx.parent.get('kill'):
        print('and dies...', file=ctx.app.writer)

@docmd.command()
def fly(ctx: Context, miles: int, miles2: int = 0, *, km: bool = False):
    """
    fly x number of miles
    
    :param miles:  number of miles to run
    :param miles2: number of miles to add to miles
    :param km:     use kilometers rather than miles
    """
    print('flying', file=ctx.app.writer)
    user    = ctx.get_global('user')
    measure = 'kilometers' if km else 'miles'
    print(f'{user} flew {miles+miles2} {measure}', file=ctx.app.writer)
    if ctx.parent.get('kill'):
        print('and dies...', file=ctx.app.writer)

