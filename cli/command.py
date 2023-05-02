"""
single command defintions used as part of application definition
"""
import asyncio
import functools
from typing import Dict, Optional, List, Callable, Union, cast, overload

from .abc import *

#** Variables **#
__all__ = ['Command']

#** Functions **#

#TODO: run sync cli things in event executor?

def wrap_async(func: Action) -> AsyncAction:
    """ensure actions are run async"""
    if not asyncio.iscoroutinefunction(func):
        func = cast(SyncAction, func)
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return func

def get_action(obj: object, name: str, func: OptAction) -> AsyncAction:
    """ensure action assignment is not pulled from command-base default"""
    if func is None:
        func = getattr(obj, f'run_{name}')
    if isinstance(func, Action):
        return wrap_async(cast(Action, func))
    raise RuntimeError(f'Invalid Action {name!r} {func!r}')

#** Classes **#

class Command(AbsCommand):
    """
    Controls Specifications and Behavior of a CLI Command

    :param name:         name of command
    :param aliases:      name aliases for command
    :param usage:        usage description 
    :param argsusage:    argument usage description
    :param category:     assigned command category
    :param hidden:       hide command in help if true
    :param flags:        configured command flags
    :param commands:     configured subcommands of command
    :param allow_parent: allow parent to run on child command run
    :param before:       command before-action function
    :param action:       command action function
    :param after:        command after-action function
    """

    def __init__(self,
        name:         str,
        aliases:      Optional[List[str]] = None,
        usage:        Optional[str]       = None,
        argsusage:    Optional[str]       = None,
        category:     Optional[str]       = None,
        hidden:       bool                = False,
        flags:        Optional[Flags]     = None,
        commands:     Optional[Commands]  = None,
        allow_parent: bool                = False,
        before:       OptAction           = None,
        action:       OptAction           = None,
        after:        OptAction           = None,
    ):
        self.name         = name
        self.aliases      = aliases or []
        self.usage        = usage
        self.argsuage     = argsusage
        self.category     = category
        self.hidden       = hidden
        self.flags        = flags or []
        self.commands     = commands or []
        self.allow_parent = allow_parent
        self.run_before   = wrap_async(before or self.run_before)
        self.run_action   = wrap_async(action or self.run_action)
        self.run_after    = wrap_async(after or self.run_after)

    @property
    def categories(self) -> Dict[str, 'Command']:
        """
        organize sub-commands into categories

        :return: dictionary of category names associated w/ sub-commands
        """
        categories = {}
        for cmd in self.commands:
            categories.setdefault(cmd.category, [])
            categories[cmd.category].append(cmd)
        return categories

    def visible_flags(self) -> Flags:
        """
        retrieve visable flags

        :return: all non hidden flags attached to this command
        """
        return [f for f in self.flags if not f.hidden]

    def visible_commands(self, category: Optional[str] = None) -> Commands:
        """
        retrieve visable commands (of given category if specified)

        :param category: only return commands of the given category if specified
        :return:         commands not hidden
        """
        commands = [c for c in self.commands if not c.hidden]
        if category is not None:
            commands = [c for c in commands if c.category == category]
        return commands

    def visible_categories(self) -> List[str]:
        """
        retrieve category names
        """
        return [category for category in self.categories.keys()]

    async def run_before(self, ctx: Context): #type: ignore
        """default before-action function when executing command"""
        pass

    async def run_after(self, ctx: Context): #type: ignore
        """default after-action function when executing command"""
        pass

    async def run_action(self, ctx: Context) -> Result: #type: ignore
        """default action function when executing command"""
        return NO_ACTION

    def before(self, func: Action) -> AsyncAction:
        """
        decorate the specified function and assign to command `before` action

        :param func: function being assigned to before function
        :return:     wrapped before function
        """
        self.run_before: AsyncAction = wrap_async(func)
        return self.run_before

    def action(self, func: Action) -> AsyncAction:
        """
        decorate the specified function and assign to command action

        :param func: function being assigned to action function
        :return:     wrapped action function
        """
        from . import wraps
        # preserve original flags
        if not hasattr(self, 'original_flags'):
            self.original_flags = self.flags
        # generate new action
        action, ctx = wraps.action(func)
        # save changes to command
        self.flags      = [*self.original_flags, *ctx.flags]
        self.run_action: AsyncAction = action
        return self.run_action

    def after(self, func: Action) -> AsyncAction:
        """
        decorate the specified function and assign to command `after` action

        :param func: function being assigned to after function
        :return:     wrapped after function
        """
        self.run_after: AsyncAction = wrap_async(func)
        return self.run_after

    @overload
    def command(self, func: Callable) -> AbsCommand:
        ...
    
    @overload
    def command(self, *args, **kwargs) -> CommandFunc:
        ...

    def command(self, *args, **kwargs) -> Union[AbsCommand, CommandFunc]:
        """
        add the specified function as a subcommand to the current parent

        :param args:   positional arguments to pass to command wrapping
        :param kwargs: keyword arguments to pass to command wrapping
        :return:       newly wrapped command object attached to parent
        """
        from . import wraps
        # allow decorator to act as normal wrapper without any args
        if not kwargs and len(args) == 1 and callable(args[0]):
            decorator = wraps.command(self)
            return decorator(args[0])
        # otherwise call decorator as normal
        return wraps.command(self, *args, **kwargs)
