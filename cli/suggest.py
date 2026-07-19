"""
CLI Autocomplete Suggestion Implementation
"""
from typing import Any, Iterator, List, Mapping, Optional, Sequence, Set, Tuple, Union

from . import SuggestFunc
from .arg import Arg
from .cmd import Command
from .flag import Flag
from .parser import index_commands, index_flags

#** Variables **#
__all__ = ['SuggestFunc', 'Suggest', 'Suggestor', 'suggest_static']

Hints  = Iterator[str]
Static = Union[Sequence[str], Set[str], Mapping[str, Any]]

#** Functions **#

def empty():
    yield from ()

def suggest_options(options: List[str], value: str) -> Hints:
    """
    """
    if not value:
        yield from options
        return
    for option in options:
        if option.startswith(value) and value != option:
            hint = option[len(value):]
            yield hint

def suggest_static(s: Static) -> SuggestFunc:
    """
    """
    vals    = list(s.keys()) if isinstance(s, Mapping) else list(s)
    options = [str(v) for v in vals]
    def static_suggestor(value: str) -> Hints:
        return suggest_options(options, value)
    return static_suggestor

#** Classes **#

class Suggest:
    __slots__ = ('suggestor', )

    def __init__(self, suggestor: SuggestFunc):
        self.suggestor = suggestor

    @classmethod
    def __class_getitem__(cls, suggestor: Union[SuggestFunc, Static]):
        return cls(suggestor) \
            if callable(suggestor) else cls(suggest_static(suggestor))

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

    def split_flags(self, flags: List[Flag],
        args: List[str]) -> Tuple[Optional[Flag], List[Flag]]:
        """
        """
        indexes = index_flags(flags, args)
        if not indexes:
            return None, []
        index, flag  = indexes[-1]
        args[:index] = []
        return flag, [f for _,f in indexes]

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
        """
        """
        return suggest_options(options, value)

    def suggest_source(self, source: Union[Arg, Flag], value: str) -> Hints:
        """
        """
        results   = []
        suggestor = source.suggestor
        if suggestor is not None:
            for item in suggestor(value):
                if item not in results:
                    results.append(item)

        default = str(source.default) if source.default is not None else None
        if default:
            for item in self.suggest_options([default], value):
                if item not in results:
                    results.append(item)
        yield from results

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

        flag, fmatched = self.split_flags(command.visible_flags(), args)
        if flag is not None:
            args.pop(0)
            if len(args) == 0 and flag._requires_value():
                if not partial:
                    return self.suggest_source(flag, '')
                return empty()
            if len(args) == 1 and flag._requires_value():
                if partial:
                    return self.suggest_source(flag, args[0])
                args.pop(0)

        arg = self.split_args(command.args, args, partial)
        if arg is not None:
            if len(args) == 1 and partial:
                return self.suggest_source(arg, args[0])
            return self.suggest_source(arg, '')

        value      = args[-1] if args and partial else ''
        all_flags  = command.visible_flags()
        flags      = [f for f in all_flags if f not in fmatched or f.repeat]
        f_required = [f for f in flags if f.required]
        if f_required:
            options = [v for flag in f_required for v in flag.variants()]
            return self.suggest_options(options, value)

        options = [c.name for c in command.visible_commands()]
        if options and not command.invoke_without_command:
            return self.suggest_options(options, value)

        options += [v for flag in flags for v in flag.variants()]
        return self.suggest_options(options, value)

    def suggest_list(self, args: List[str], partial: bool = False) -> List[str]:
        """
        """
        return list(self.suggest(args, partial))
