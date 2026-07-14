"""
CLI Autocomplete Suggestion Implementation
"""
from typing import Iterator, List, Optional, Union

from .arg import Arg
from .command import Command
from .flag import Flag
from .parser import index_commands, index_flags

#** Variables **#
__all__ = ['Suggestor']

Hints = Iterator[str]

#** Classes **#

class Suggestor:
    """
    """
    __slots__ = ('command', )

    def __init__(self, command: Command):
        self.command = command

    def split_commands(self, args: List[str]) -> Command:
        """
        """
        command = self.command
        while args:
            indexes = index_commands(command.visible_commands(), args)
            if not indexes:
                break
            index, command = indexes[-1]
            args[:index]   = []
        return command

    def split_flags(self, flags: List[Flag], args: List[str]) -> Optional[Flag]:
        """
        """
        indexes = index_flags(flags, args)
        if not indexes:
            return
        index, flag  = indexes[-1]
        args[:index] = []
        return flag

    def split_args(self,
        cmdargs: List[Arg], args: List[str], partial: bool) -> Optional[Arg]:
        """
        """
        limit   = 1 if partial else 0
        cmdargs = cmdargs.copy()
        while cmdargs and len(args) > limit:
            value = args.pop(0)
            if value == '--':
                continue
            cmdarg = cmdargs[0]
            if not cmdarg.repeat:
                cmdargs.pop(0)
        return cmdargs[0] if cmdargs else None

    def suggest_options(self, options: List[str], value: str) -> Hints:
        if not value:
            yield from options
        for option in options:
            if value.startswith(option):
                hint = option[len(value):]
                yield hint

    def suggest_source(self, source: Union[Arg, Flag], value: str) -> Hints:
        options   = []
        suggestor = source.suggestor
        if suggestor is not None:
            options += list(suggestor(value))

        default = str(source.default)
        if default and source.default is not None:
            options.append(default)
        return self.suggest_options(options, value)

    # partial = len(args) > spaces

    def suggest(self, args: List[str], partial: bool = False) -> Hints:
        """
        Build suggestions based on latest relevant argument in args

        :param args:    list of arguments from command-line
        :param partial: declaration if last argument was partial or complete
        :return:        yielded suggestion results
        """
        command = self.split_commands(args)
        if command is not self.command:
            args.pop(0)

        flag = self.split_flags(command.visible_flags(), args)
        if flag is not None:
            args.pop(0)
            if len(args) == 1 and flag._requires_value():
                if partial:
                    print('partial flag value', flag, args[0])
                    return self.suggest_source(flag, args[0])
                args.pop(0)

        arg = self.split_args(command.args, args, partial)
        if arg is not None:
            if len(args) == 1 and partial:
                return self.suggest_source(arg, args[0])
            return self.suggest_source(arg, '')

        value      = args[-1] if args and partial else ''
        flags      = command.visible_flags()
        f_required = [f for f in flags if f.required]
        if f_required:
            options = [v for flag in f_required for v in flag.variants()]
            return self.suggest_options(options, value)

        options = [c.name for c in command.visible_commands()]
        if command.subcmd_required:
            return self.suggest_options(options, value)

        options += [v for flag in flags for v in flag.variants()]
        return self.suggest_options(options, value)

    def suggest_list(self, args: List[str], partial: bool = False) -> List[str]:
        """
        """
        return list(self.suggest(args, partial))
