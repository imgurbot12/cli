"""
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, List

from .flag import Flags
from .context import Context

#** Variables **#
__all__ = ['Action', 'Command']

Action   = Callable[[Context], None]
Commands = List['Command']

#** Classes **#

@dataclass
class Command:
    """controls specifications and behavior of a cli command"""
    name:        str
    aliases:     Optional[List[str]]  = field(default_factory=list)
    usage:       Optional[str]        = None
    argsusage:   Optional[str]        = None
    category:    str                  = '*'
    hidden:      bool                 = False
    flags:       Optional[Flags]      = field(default_factory=list)
    subcommands: Optional[Commands]   = field(default_factory=list)
    before:      Optional[Action]     = None
    action:      Optional[Action]     = None
    after:       Optional[Action]     = None

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

    def is_within(self, values: List[str]) -> bool:
        """
        return true if name or any aliases exist in list of values

        :param values: list of strings to be evaluated
        :return:       true if any names/aliases exist in values
        """
        for value in values:
            if self.has_name(value):
                return True
        return False

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
        :return:         subcommands not hidden of primary command
        """
        commands = [c for c in self.subcommands if not c.hidden]
        if category is not None:
            commands = [c for c in commands if c.category == category]
        return commands

    async def before(self, ctx: Context):
        """default before command function"""
        print('before')

    async def after(self, ctx: Context):
        """default after command function"""
        print('after')

    async def action(self, ctx: Context):
        """default action command function"""
        print('action')
