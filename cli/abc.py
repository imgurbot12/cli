"""
Abstract/BaseClass Instances/Protocols
"""
from abc import abstractmethod
from collections import UserList
from functools import cached_property
from typing import *
from typing import TextIO
from typing_extensions import Self

from pyderive import dataclass, field

#** Variables **#
__all__ = [
    'T',
    'NO_ACTION',
    'Result',
    'SyncAction',
    'AsyncAction',
    'Action',
    'OptAction',
    'Flags',
    'FlagDict',
    'Commands',
    'AppFunc',
    'CommandFunc',
    'OptCoroutine',
    'OptStrList',

    'CliError',
    'UsageError',
    'ExitError',
    'NotFoundError',
    'ConfigError',

    'Args',
    'Context',
    'AbsFlag',
    'AbsCommand',
    'AbsApplication',
]

#: generic typevar for flag definitions
T = TypeVar('T')

#: tracker for parser to know if a command has taken no action
class NO_ACTION:
    pass

#: typehint definition for action return-type
Result = Optional[Type[NO_ACTION]]

#: definition for sync action type
SyncAction = Callable[['Context'], Result]

#: definition for async action type
AsyncAction = Callable[['Context'], Coroutine[Any, Any, Result]]

#: defintion for any action called in commands
Action = Union[SyncAction, AsyncAction]

#: definition for optional action
OptAction = Optional[Action]

#: definition for list of flags
Flags = List['AbsFlag']

#: definition for flags organized into a dictionary
FlagDict = Dict[str, Any]

#: defintion for list of commands
Commands = List['AbsCommand']

#: type definition app function
AppFunc = Callable[[Callable], 'AbsApplication']

#: type definition command function
CommandFunc = Callable[[Callable], 'AbsCommand']

#: type definition for optional empty coroutine
OptCoroutine = Optional[Coroutine[None, None, None]]

#: type definition for optional list of strings
OptStrList = Optional[List[str]]

#** Functions **#

def ctx_fix_key(flags: Flags, fdict: FlagDict, key: str) -> Optional[str]:
    """translate key into long flag-name if it matches any existing flags"""
    if key not in fdict:
        for flag in flags:
            if key in flag.names:
                key = flag.long
                break
    if key in fdict:
        return key

def ctx_get(flags: Flags, fdict: FlagDict, key: str, default: Any) -> Any:
    """get value in flag-dictionary with the specified key"""
    realkey = ctx_fix_key(flags, fdict, key)
    return default if realkey is None else fdict[realkey]

def ctx_set(flags: Flags, fdict: FlagDict, key: str, value: Any):
    """set value in flag-dictionary with the specified key"""
    key = ctx_fix_key(flags, fdict, key) or key
    fdict[key] = value

def ctx_default(flags: Flags, fdict: FlagDict, key: str, default: Any) -> Any:
    """`setdefault` implementation w/ ctx-key-translation"""
    key = ctx_fix_key(flags, fdict, key) or key
    fdict.setdefault(key, default)

#** Classes **#

class CliError(Exception):
    """baseclass for all cli internal exceptions"""

    def __init__(self, msg: str, ctx: 'Context', cmd: 'AbsCommand'):
        self.message = msg
        self.context = ctx
        self.command = cmd

    def __str__(self):
        return f'cmd={self.command.name!r} error={self.message!r}'

class UsageError(CliError):
    """raise error during usage issue"""

class ExitError(CliError):
    """raise error when app must exit"""

    def __init__(self, msg: str, code: int, ctx: 'Context', cmd: 'AbsCommand'):
        self.message = msg
        self.code    = code
        self.context = ctx
        self.command = cmd

class NotFoundError(CliError):
    """raise error when app gets flag it doesnt recognize"""

    def __init__(self, msg: str, path: List[str], ctx: 'Context', cmd: 'AbsCommand'):
        self.message = msg
        self.path    = path
        self.context = ctx
        self.command = cmd
        if not path:
            path.append(cmd.name)
            while ctx.ctx_parent:
                if ctx.command.name not in path:
                    path.insert(0, ctx.command.name)
                ctx = ctx.ctx_parent

class ConfigError(CliError):
    """raise error when app is improperly configured"""

    def __init__(self, msg: str, cmd: 'AbsCommand'):
        self.message = msg
        self.command = cmd
        self.context = None

class Args(UserList):
    """extended list object intended to add ease-of-use functions for context"""

    def get(self, index: int) -> Optional[str]:
        """
        retrieve value from arguments at given index

        :param index: index of arg to collect
        :return:      value from index if exists
        """
        return self[index] if len(self) > index else None

    def first(self) -> Optional[str]:
        """return 1st argument in args"""
        return self.get(0)

    def tail(self) -> Self:
        """return all arguments but first"""
        return self[1:] if len(self) >= 2 else self

    def present(self) -> bool:
        """return true if there are any arguments"""
        return len(self) != 0

    def swap(self, fromidx: int, toidx: int):
        """swap from and to index in list"""
        if fromidx >= len(self) or toidx >= len(self):
            raise ValueError("index out of range")
        self[fromidx], self[toidx] = self[toidx], self[fromidx]

@dataclass(slots=True)
class Context:
    """Context-Object to Pass Information into/from Various Command Actions"""
    app:          'AbsApplication'    = field(repr=False)
    command:      'AbsCommand'        = field(repr=False) 
    ctx_parent:   Optional['Context'] = field(default=None, repr=False)
    global_flags: FlagDict            = field(default_factory=dict)
    local_flags:  FlagDict            = field(default_factory=dict)
    args:         Args                = field(default_factory=Args)
 
    @property
    def parent(self) -> Self:
        """retrieve parent or raise execution error"""
        if self.ctx_parent is None:
            raise CliError(
                'Unable to retrieve Context Parent', self, self.command)
        return self.ctx_parent

    def get(self, name: str, default: Any = None) -> Any:
        """
        collect a localized command flag value or return default

        :param name:    name of flag to retrieve
        :param default: default value to return if not found
        :return:        flag value or default when not found
        """
        return ctx_get(self.command.flags, self.local_flags, name, default)

    def set(self, name: str, value: Any):
        """
        set a new localized command flag value

        :param name:  name of flag to set
        :param value: value of flag to set
        """
        return ctx_set(self.command.flags, self.global_flags, name, value)

    @abstractmethod
    def get_global(self, name: str, default: Any = None) -> Any:
        """
        collect a globalized command flag value or return default

        :param name:    name of flag to retrieve
        :param default: default value to return if not found
        :return:        flag value or default when not found
        """
        return ctx_get(self.app.flags, self.global_flags, name, default)

    @abstractmethod
    def set_global(self, name: str, value: Any):
        """
        set a new globalized command flag value

        :param name:  name of flag to set
        :param value: value of flag to set
        """
        return ctx_set(self.app.flags, self.global_flags, name, value)
 
    def setdefault(self, name: str, value: Any, isglobal: bool = False):
        """
        set default value for localized flag if specified name is not present
        
        :param name:     name of flag to set default for
        :param value:    value to set default as
        :param isglobal: modify global variables if true
        """
        flags = self.app.flags if isglobal else self.command.flags
        fdict = self.global_flags if isglobal else self.local_flags
        return ctx_default(flags, fdict, name, value)
 
    def not_found_error(self, error: str, path: List[str]):
        """
        handle not-found error with the current action

        :param error: error-message to pass to handlers
        """
        raise NotFoundError(error, path, self, self.command)

    def on_usage_error(self, error: str):
        """
        handle a usage error with the current action

        :param error: error-message to pass to handlers
        """
        raise UsageError(error, self, self.command)

    def exit_with_error(self, error: str, exit_code: int = 1):
        """
        exit with the following error and exit-code for some unrecoverable error

        :param error:     error-message to pass to handlers
        :param exit_code: exit-code to exit program with
        """
        raise ExitError(error, exit_code, self, self.command)

class AbsFlag(Protocol[T]):
    """Abstract Flag Object Definition"""
    name:      str
    usage:     Optional[str]
    default:   Optional[T]
    hidden:    bool
    required:  bool
    type:      Type[T]
    has_value: bool

    @abstractmethod
    def parse(self, value: str) -> T:
        raise NotImplementedError
    
    @cached_property
    def names(self) -> List[str]:
        return [n for n in (n.strip() for n in self.name.split(',', 1)) if n]
    
    @property
    def display(self) -> str:
        return ', '.join(self.names)

    @property
    def long(self) -> str:
        return self.names[0]

    @property
    def short(self) -> str:
        return self.names[-1]

    def index(self, values: Iterable[str]) -> Optional[int]:
        """
        return index of flag in values if found

        :param values: list of values to search
        :return:       index-num (if found)
        """
        names = self.names
        for n, value in enumerate(values, 0):
            if value.lstrip('-') in names and value.startswith('-'):
                return n 

class AbsCommand(Protocol):
    """Abstract Command Object Definition"""
    name:         str
    aliases:      List[str]
    flags:        Flags
    commands:     Commands
    category:     Optional[str]
    hidden:       bool
    allow_parent: bool
    
    @overload
    @abstractmethod
    def command(self, func: Callable) -> 'AbsCommand':
        ...
    
    @overload
    @abstractmethod
    def command(self, *args, **kwargs) -> CommandFunc:
        ...

    @abstractmethod
    def command(self, *args, **kwargs) -> Union['AbsCommand', CommandFunc]:
        raise NotImplementedError

    async def run_before(self, ctx: Context):
        pass

    async def run_action(self, ctx: Context) -> Result:
        return NO_ACTION

    async def run_after(self, ctx: Context):
        pass
  
    def categories(self) -> Dict[str, 'AbsCommand']:
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

        :return: list of visible category names
        """
        return [category for category in self.categories.keys()]

    @cached_property
    def display(self):
        """convert command names/alises to string for help formatting"""
        return ', '.join([self.name, *self.aliases])

    def has_name(self, name: str) -> bool:
        """
        return true if command has the given name

        :param name: name being compared to command
        :return:     true if any names/aliases match
        """
        return name == self.name or name in self.aliases

    def index(self, values: Iterable[str]) -> Optional[int]:
        """
        return earliest index of where a command name/alias was found

        :param values: list of strings to be searched
        :return:       index-num (if found)
        """
        for n, value in enumerate(values, 0):
            if value == self.name or value in self.aliases:
                return n

class AbsApplication(AbsCommand, Protocol):
    writer:            TextIO
    err_writer:        TextIO
    help_app_template: Optional[str]
    help_cmd_template: Optional[str]
    
    @abstractmethod
    def on_usage_error(self, err: UsageError):
        raise NotImplementedError

    @abstractmethod
    def exit_with_error(self, err: ExitError):
        raise NotImplementedError

    @abstractmethod
    def not_found_error(self, err: NotFoundError):
        raise NotImplementedError

    @abstractmethod
    def config_error(self, err: ConfigError):
        raise NotImplementedError
 
    @overload
    @abstractmethod
    def run(self, args: OptStrList = None, run_async: Literal[False] = False):
        ...

    @overload
    @abstractmethod
    def run(self, args: OptStrList = None, run_async: Literal[True] = True) -> Coroutine[None, None, None]:
        ...

    @abstractmethod
    def run(self, args: OptStrList = None, run_async: bool = False) -> OptCoroutine:
        raise NotImplementedError
