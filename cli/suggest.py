"""
CLI Autocomplete Suggestion Implementation
"""
import functools
from typing import (
    Any, Dict, Iterator, List, Mapping, Optional, Sequence, Set,
    Tuple, Type, Union)

from . import SuggestFunc
from .arg import Arg
from .context import Context
from .cmd import Command
from .flag import Flag
from .parser import index_commands, index_flags
from .utils import echo
from .wraps import wrap_suggestor

#** Variables **#
__all__ = ['SuggestorCLS', 'SuggestFunc', 'Suggest', 'Suggestor', 'suggest_static']

Hints  = Iterator[str]
Static = Union[Sequence[str], Set[str], Mapping[str, Any]]

SuggestorCLS = Type['Suggestor']

#** Functions **#

def empty():
    yield from ()

def _action(ctx: Context):
    """
    default auto-complete command action
    """
    suggestor = ctx.suggestor()
    pos       = ctx.get_arg('pos', int)
    args      = ctx.get_arg('args', List[str])
    partial   = len(args) > pos
    for suggest in suggestor.suggest(args, partial):
        echo(suggest)
    ctx.exit()

@functools.lru_cache()
def autocomplete_cmd() -> Command:
    """
    default auto-complete hidden command definition
    """
    return Command(
        name='__autocomplete',
        about='Hidden autocompletion command',
        args=[Arg[int]('pos'), Arg[str]('args', repeat=True)],
        hidden=True,
        action=_action,
    )

def suggest_options(options: List[str], value: str) -> Hints:
    """
    helper function to suggest items from a list based on the value

    :param options: options to recommend against
    :param value:   current value used to generate suggestions
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
    generate suggestor based on a static list of items

    :param s: list of static items to suggest against
    :return:  static suggestion function
    """
    vals    = list(s.keys()) if isinstance(s, Mapping) else list(s)
    options = [str(v) for v in vals]
    def static_suggestor(value: str) -> Hints:
        return suggest_options(options, value)
    return static_suggestor

#** Classes **#

class Suggest:
    """
    Suggestion Annotation-Helper Type

    ```python
    Test = Annotated[str, Suggest[my_suggest_function]]
    ```
    """
    __slots__ = ('suggestor', )

    def __init__(self, suggestor: SuggestFunc):
        self.suggestor = suggestor

    @classmethod
    def __class_getitem__(cls, suggestor: Union[SuggestFunc, Static]):
        return cls(suggestor) \
            if callable(suggestor) else cls(suggest_static(suggestor))

class Suggestor:
    """
    Auto-Complete Suggestion Generator Implementation
    """
    __slots__ = ('command', 'extra')

    def __init__(self, command: Command, extra: Optional[Dict[str, Any]] = None):
        self.command = command
        self.extra   = extra or {}

    def split_commands(self, args: List[str]) -> Command:
        """
        find last valid command in raw arguments
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
        find last valid flag in raw arguments (if present)

        :param flags: list of flags to compare against
        :param args:  raw arguments to parse
        :return:      (last matched-flag, list of all matched-flags)
        """
        indexes = index_flags(flags, args)
        if not indexes:
            return None, []
        index, flag = indexes[-1]
        if flag.suggestor is False:
            return None, []
        args[:index] = []
        return flag, [f for _,f in indexes]

    def split_args(self,
        cmdargs: List[Arg], args: List[str], partial: bool) -> Optional[Arg]:
        """
        find last valid argument in raw arguments (if present)

        :param cmdargs: list of command arguments to compare against
        :param args:    raw arguments to parse
        :param partial: status of cursor (either partial string or new)
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

        if not cmdargs:
            return None
        cmd = cmdargs[0]
        return None if cmd.suggestor is False else cmd

    def suggest_options(self, options: List[str], value: str) -> Hints:
        """
        helper function to suggest items from a list based on the value

        :param options: options to recommend against
        :param value:   current value used to generate suggestions
        """
        return suggest_options(options, value)

    def suggest_source(self, source: Union[Arg, Flag], value: str) -> Hints:
        """
        generate suggestions from the given source argument/flag

        :param source: source of suggestions
        :param value:  value used to generate suggestions from
        """
        results       = []
        raw_suggestor = source.suggestor
        if callable(raw_suggestor):
            suggestor = wrap_suggestor(raw_suggestor)
            for item in suggestor(self.extra, value):
                if item not in results:
                    results.append(item)

        default = str(source.default) if source.default is not None else None
        if default:
            for item in self.suggest_options([default], value):
                if item not in results:
                    results.append(item)
        yield from results

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
            if not args and partial:
                return empty()

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
        flags      = [f for f in flags if f.suggestor is not False]
        f_required = [f for f in flags if f.required]
        if f_required:
            options = [v for flag in f_required for v in flag.variants()]
            return self.suggest_options(options, value)

        options = [c.name for c in command.visible_commands() if c.suggest]
        if options and not command.invoke_without_command:
            return self.suggest_options(options, value)

        options += [v for flag in flags for v in flag.variants()]
        return self.suggest_options(options, value)

    def suggest_list(self, args: List[str], partial: bool = False) -> List[str]:
        """
        Build suggestions based on latest relevant argument in args

        :param args:    list of arguments from command-line
        :param partial: declaration if last argument was partial or complete
        :return:        list of complete suggestions
        """
        return list(self.suggest(args, partial))
