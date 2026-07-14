"""
CLI Command Implementation
"""
import sys
from typing import Callable, Dict, List, Optional, Type

from . import Context
from .arg import Args
from .flag import Flags
from .wraps import wraps

#** Variables **#
__all__ = ['Action', 'Command', 'Commands']

Action   = Callable[..., None]
Commands = List['Command']

#** Classes **#

class Command:
    __slots__ = (
        'name', 'about', 'version', 'authors', 'category', 'hidden',
        'args', 'flags', 'commands', 'aliases', 'subcommand_required',
        'action', )

    def __init__(self,
        name:                   str,
        about:                  Optional[str]       = None,
        version:                Optional[str]       = None,
        authors:                Optional[List[str]] = None,
        category:               Optional[str]       = None,
        hidden:                 bool                = False,
        args:                   Optional[Args]      = None,
        flags:                  Optional[Flags]     = None,
        commands:               Optional[Commands]  = None,
        aliases:                Optional[List[str]] = None,
        action:                 Optional[Action]    = None,
        subcommand_required:    bool                = False,
    ):
        """
        """
        self.name                = name
        self.about               = about
        self.version             = version
        self.authors             = authors
        self.category            = category or '*'
        self.hidden              = hidden
        self.args                = args or []
        self.flags               = flags or []
        self.commands            = commands or []
        self.aliases             = aliases or []
        self.subcommand_required = subcommand_required
        self.action              = action

    def __repr__(self) -> str:
        return f'Command(name={self.name}, aliases={self.aliases!r})'

    @property
    def categories(self) -> Dict[str, List['Command']]:
        """
        Organize sub-commands into categories

        :return: dictionary of category names associated w/ sub-commands
        """
        categories = {}
        for cmd in self.commands:
            categories.setdefault(cmd.category, [])
            categories[cmd.categories].append(cmd)
        return categories

    def visible_flags(self) -> Flags:
        """
        Retrieve visable flags

        :return: all non hidden flags attached to this command
        """
        return [f for f in self.flags if not f.hidden]

    def visible_commands(self, category: Optional[str] = None) -> Commands:
        """
        Retrieve visable commands (of given category if specified)

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

    def _validate_args(self):
        """
        """
        reserved = set()
        repeated = None
        for n, arg in enumerate(self.args, 0):
            if arg.repeat:
                if repeated is not None:
                    raise ValueError(
                        f'{self.name} arg({n}) cannot also be repeated.')
                repeated = arg.name
            if arg.name not in reserved:
                reserved.add(arg.name)
                continue
            raise ValueError(
                f'{self.name} arg({n}) has duplicate argument {arg.name!r}')

    def _validate_flags(self):
        """
        """
        reserved = set()
        for n, flag in enumerate(self.flags, 0):
            if flag.name in reserved:
                raise ValueError(
                    f'{self.name} flag({n}) has duplicate name {flag.name!r}')
            reserved.add(flag.name)
            for var in flag.variants():
                if var in reserved:
                    raise ValueError(
                        f'{self.name} flag({n}) has duplicate flag {var!r}')
                reserved.add(var)

    def _validate_commands(self):
        """
        """
        reserved = set()
        for n, cmd in enumerate(self.commands, 0):
            if cmd.name in reserved:
                raise ValueError(
                    f'{self.name} command({n}) has duplicate name {cmd.name!r}')
            reserved.add(cmd.name)
            for alias in cmd.aliases:
                if alias in reserved:
                    raise ValueError(
                        f'{self.name} command({n}) has duplicate alias {alias!r}')
                reserved.add(alias)

    def validate(self):
        """
        """
        self._validate_args()
        self._validate_flags()
        self._validate_commands()

    def parse(self,
        args:   Optional[List[str]]      = None,
        parser: Optional[Type['Parser']] = None,
    ) -> 'ParsedCmd':
        """
        """
        engine = (parser or Parser)(self)
        return engine.parse(args or sys.argv[1:])

    #TODO: limit call to last in chain (unless explicitlly allowed)
    def run_with(self, context: Context, action: Optional[Action] = None):
        """
        """
        action = action or self.action
        if action is not None:
            if not context.parsed.commands or not self.subcommand_required:
                func = wraps(action)
                func(context)
        for parsed in context.parsed.commands.values():
            context = context.stack(parsed)
            context.command.run_with(context)

    def run(self,
        args:   Optional[List[str]]      = None,
        parser: Optional[Type['Parser']] = None,
    ):
        """
        """
        result  = self.parse(args, parser)
        context = Context(result)
        self.run_with(context)

#** Imports **#
from .parser import Parser, ParsedCmd
