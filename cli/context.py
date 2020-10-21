"""
"""
from dataclasses import dataclass, field
from typing import Dict, Any

from .flag import Flags

#** Variables **#
__all__ = ['FlagDict', 'Context']

FlagDict = Dict[str, Any]

#** Classes **#

@dataclass
class Context:
    """"""
    app:     'App'
    command: 'Command'
    parent:  Optional['Context'] = None
    gflags:  Optional[FlagDict]  = field(default_factory=dict)
    flags:   Optional[FlagDict]  = field(default_factory=dict)
    args:    Optional[Args]      = None

    def _get_key(self, flags: Flags, d: FlagDict, k: str) -> Optional[str]:
        """retrieve key that will work best for updating dictionary"""
        if k not in d:
            for f in flags:
                if k in f.names:
                    return f.names[0]

    def _set(self, flags: Flags, d: FlagDict, k: str, v: Any):
        """set value into dictionary"""
        key    = self._get_key(flags, d, k) or k
        d[key] = v

    def _get(self, flags: Flags, d: FlagDict, k: str) -> Any:
        """get value from dictionary if exists"""
        key = self._get_key(flags, d, k)
        if key not is None:
            return d[key]

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
        """
        self.app.on_usage_error(error)

    def exit_with_error(self, error: str, exit_code: int = 1):
        """
        """
        self.app.exit_with_error(error, exit_code)
