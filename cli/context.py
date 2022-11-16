"""
context object and help object definitons useful for tracking application state
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from .flag import Flags

#** Variables **#
__all__ = [
    'FlagDict',
    'NO_ACTION',

    'CliError',
    'UsageError',
    'ExitError',
    'NotFoundError',
    'ConfigError',

    'Args',
    'Context',
]

#: simple defintion for dictionaries used in context object
FlagDict = Dict[str, Any]

#: tracker for parser to know if a command has taken no action
NO_ACTION = 'NO_COMMAND_ACTION_TAKEN'

#** Exceptions **#

class CliError(Exception):
    """baseclass for all cli internal exceptions"""
    pass

class UsageError(CliError):
    """raise error during usage issue"""

class ExitError(CliError):
    """raise error when app must exit"""

class NotFoundError(CliError):
    """raise error when app gets flag it doesnt recognize"""

class ConfigError(CliError):
    """raise error when app is improperly configured"""

#** Classes **#

class Args(list):
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

    def tail(self) -> List[str]:
        """return all arguments but first"""
        return self[1:] if len(self) >= 2 else self

    def present(self):
        """return true if there are any arguments"""
        return len(self) != 0

    def swap(self, fromidx: int, toidx: int):
        """swap from and to index in list"""
        if fromidx >= len(self) or toidx >= len(self):
            raise ValueError("index out of range")
        self[fromidx], self[toidx] = self[toidx], self[fromidx]

@dataclass
class Context:
    """passes information into/from various command actions"""

    app:     'App'               = field(repr=False)
    command: 'Command'           = field(repr=False)
    parent:  Optional['Context'] = field(default=None, repr=False)
    gflags:  Optional[FlagDict]  = field(default_factory=dict)
    flags:   Optional[FlagDict]  = field(default_factory=dict)
    args:    Optional[Args]      = field(default_factory=Args)

    def _get_key(self, flags: Flags, d: FlagDict, k: str) -> Optional[str]:
        """retrieve key that will work best for updating dictionary"""
        if k in d:
            return k
        for f in flags:
            if k in f.names and f.names[0] in d:
                return f.names[0]

    def _set(self, flags: Flags, d: FlagDict, k: str, v: Any):
        """set value into dictionary"""
        key    = self._get_key(flags, d, k) or k
        d[key] = v

    def _get(self, flags: Flags, d: FlagDict, k: str) -> Any:
        """get value from dictionary if exists"""
        key = self._get_key(flags, d, k)
        return None if key is None else d[key]

    def set(self, name: str, value: Any):
        """
        set a new localized flag value

        :param name:  name of the flag
        :param value: value being set
        """
        self._set(self.command.flags, self.flags, name, value)

    def get(self, name: str) -> Any:
        """
        collect a localized flag value

        :param name: name of the flag
        :return:     value of the flag if exists
        """
        return self._get(self.command.flags, self.flags, name)

    def set_global(self, name: str, value: Any):
        """
        set a new global flag value

        :param name:  name of the flag
        :param value: value being set
        """
        self._set(self.app.flags, self.gflags, name, value)

    def get_global(self, name: str) -> Any:
        """
        collect a global flag value

        :param name: name of the flag
        :return:     value of the flag if exists
        """
        return self._get(self.app.flags, self.gflags, name)

    def on_usage_error(self, error: str):
        """
        handle a usage error with the current action

        :param error: error-message to pass to handlers
        """
        raise UsageError(error)

    def exit_with_error(self, error: str, exit_code: int = 1):
        """
        exit with the following error and exit-code for some unrecoverable error

        :param error:     error-message to pass to handlers
        :param exit_code: exit-code to exit program with
        """
        raise ExitError(error, exit_code)
