"""
single command defintions used as part of application definition
"""
import asyncio
import functools
from typing import *
from dataclasses import dataclass, field, InitVar

from .flag import Flags
from .context import NO_ACTION, Context, ConfigError

#** Variables **#
__all__ = [
    'Action',
    'Commands',
    'CommandBase',
    'Command'
]

#: defintion for any action called in commands
Action = Callable[[Context], None]

#: defintion for list of commands
Commands = List['Command']

#** Functions **#

#TODO: run sync cli things in event executor?

def wrap_async(func: Callable) -> Callable:
    """ensure actions are run async"""
    if not asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return func

def get_action(obj: object, name: str, func: Optional[Callable]) -> Callable:
    """ensure action assignment is not pulled from command-base default"""
    if not func or func is getattr(CommandBase, name):
        func = getattr(obj, f'run_{name}')
        return wrap_async(func)
    return wrap_async(func)

#** Classes **#

class CommandBase:
    """baseclass for command handling and attribute retrieval"""
    flags:    Flags
    commands: Commands

    def __post_init__(self, before: Action, action: Action, after: Action):
        """value validation to ensure correctness"""
        self.run_before = get_action(self, 'before', before)
        self.run_action = get_action(self, 'action', action)
        self.run_after  = get_action(self, 'after',  after)

    @property
    def categories(self) -> Dict[str, 'Command']:
        """
        organize commands into categories
        """
        categories = {}
        for cmd in self.commands:
            if cmd.category not in categories:
                categories[cmd.category] = []
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

    async def run_before(self, ctx: Context):
        """default before command function"""
        pass

    async def run_action(self, ctx: Context):
        """default action command function"""
        return NO_ACTION

    async def run_after(self, ctx: Context):
        """default after command function"""
        pass

    def before(self, func: Callable) -> Action:
        """
        decorate the specified function and assign to command `before` action

        :param func: function being assigned to before function
        :return:     wrapped before function
        """
        self.run_before = wrap_async(func)
        return self.run_before

    def action(self, func: Callable) -> Action:
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
        action = wraps.action(func)
        # save changes to command
        self.flags      = [*self.original_flags, *action.flags]
        self.run_action = action
        return self.run_action

    def after(self, func: Callable) -> Action:
        """
        decorate the specified function and assign to command `after` action

        :param func: function being assigned to after function
        :return:     wrapped after function
        """
        self.run_after = wrap_async(func)
        return self.run_after

    def command(self, *args: Any, **kwargs: Any) -> 'Command':
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

    def validate(self):
        """
        validate command settings before being run
        """
        # ensure flag-names dont overlap
        for n, flag in enumerate(self.flags[::-1], 1):
            for other in self.flags[:-n]:
                for name in flag.names:
                    if name in other.names:
                        raise ConfigError(
                            f'command {self.name!r} > '
                            f'flag {flag.name!r} name overlaps {other.name!r}')
        # ensure command-names don't overlap
        for n, cmd in enumerate(self.commands[::-1], 1):
            for other in self.commands[:-n]:
                if cmd.name == other.name:
                    raise ConfigError(
                        f'command {self.name!r} > '
                        f'subcmd {cmd.name!r} name overlaps: {other.name!r}')
                for alias in cmd.aliases:
                    if alias == other.name or alias in other.aliases:
                        raise ConfigError(
                            f'cmd {self.name!r} > subcmd {cmd.name!r} '
                            f'alias {alias!r} overlaps: {other.name!r}')
        # validate subcommands as well
        for cmd in self.commands:
            cmd.validate()

@dataclass
class Command(CommandBase):
    """
    controls specifications and behavior of a cli command
    
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

    name:         str
    aliases:      List[str]     = field(default_factory=list)
    usage:        Optional[str] = None
    argsusage:    Optional[str] = None
    category:     str           = '*'
    hidden:       bool          = False
    flags:        Flags         = field(default_factory=list, repr=False)
    commands:     Commands      = field(default_factory=list, repr=False)
    allow_parent: bool          = False

    before: InitVar[Action]
    action: InitVar[Action]
    after:  InitVar[Action]

    def to_string(self):
        """convert command names/alises to string for help formatting"""
        return ', '.join([self.name, *self.aliases])

    def has_name(self, name: str) -> bool:
        """
        return true if command has the given name

        :param name: name being compared to command
        :return:     true if any names/aliases match
        """
        return name == self.name or name in self.aliases

    def index(self, values: List[str]) -> int:
        """
        return earliest index of where a command name/alias was found

        :param values: list of strings to be searched
        :return:       index-num (if found); -1 (if missing)
        """
        for n, value in enumerate(values, 0):
            if value == self.name or value in self.aliases:
                return n
        return -1
