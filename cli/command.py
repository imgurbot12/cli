"""
single command defintions used as part of application definition
"""
import asyncio
from functools import wraps
from dataclasses import dataclass, field, InitVar
from typing import Callable, Optional, List, Dict

from .flag import Flags
from .context import NO_ACTION, Context

#** Variables **#
__all__ = [
    'Action',
    'Commands',

    'range_args',
    'exact_args',
    'no_args',

    'CommandBase',
    'Command'
]

#: defintion for any action called in commands
Action = Callable[[Context], None]

#: defintion for list of commands
Commands = List['Command']

#** Functions **#

def _wraps(func: Callable) -> Callable:
    """ensure actions are run async"""
    if not asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return func

def range_args(min: int = 0, max: Optional[int] = None) -> Action:
    """
    generate before action function to validate the number of arguments

    :param min: minimum number of arguments
    :param max: maximum number of arguments
    :return:    function used to regulate argument numbers
    """
    def validate_range_args(ctx: Context):
        if min < 0 and len(ctx.args) > 0:
            ctx.on_usage_error('action does not take any arguments')
        if min > 0 and len(ctx.args) < min:
            ctx.on_usage_error(f'action must have at least {min} arguments')
        if max and len(ctx.args) > max:
            ctx.on_usage_error(f'action can have at maximum {max} arguments')
    return validate_range_args

def exact_args(num: int) -> Action:
    """
    generate before action function to validate the exact of arguments

    :param num: number of allowed arguments
    :return:    function used to regulate argument numbers
    """
    def validate_exact_args(ctx: Context):
        if len(ctx.args) != num:
            ctx.on_usage_error(f'action must have exactly {num} arguments')
    return validate_exact_args

#: public action validator to ensure no arguments are passed
no_args = range_args(-1)

#** Classes **#

class CommandBase:
    """baseclass for command handling and attribute retrieval"""
    flags:    Flags
    commands: Commands

    def __post_init__(self, before: Action, action: Action, after: Action):
        """value validation to ensure correctness"""
        self.before = _wraps(before or self.before)
        self.action = _wraps(action or self.action)
        self.after  = _wraps(after  or self.after)
        # ensure flag-names dont overlap
        all_names = set()
        for flag in self.flags:
            names = set(flag.names)
            for name in names:
                if name in all_names:
                    raise ValueError(f'flag: {flag.name} name overlaps: {name}')
            all_names.update(names)
        # ensure command-names don't overlap
        cmd_names = set()
        for cmd in self.commands:
            names = set([cmd.name, *cmd.aliases])
            for name in names:
                if name in cmd_names:
                    raise ValueError(f'cmd: {cmd.name} name overlaps: {name}')
            cmd_names.update(names)

    @property
    def categories(self) -> Dict[str, 'Command']:
        """organize commands into categories"""
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
        """retrieve category names"""
        return [category for category in self.categories.keys()]

    async def before(ctx: Context):
        """default before command function"""

    async def action(ctx: Context):
        """default action command function"""
        return NO_ACTION

    async def after(ctx: Context):
        """default after command function"""

@dataclass
class Command(CommandBase):
    """controls specifications and behavior of a cli command"""

    name:      str
    aliases:   List[str]     = field(default_factory=list)
    usage:     str           = 'no usage given'
    argsusage: Optional[str] = None
    category:  str           = '*'
    hidden:    bool          = False
    flags:     Flags         = field(default_factory=list, repr=False)
    commands:  Commands      = field(default_factory=list, repr=False)
    before:    InitVar[Action]
    action:    InitVar[Action]
    after:     InitVar[Action]

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
