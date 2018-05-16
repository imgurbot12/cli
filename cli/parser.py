from __future__ import print_function
from .context import Context, GlobalContext
from .help import show_app_help
from functools import reduce

#** Functions **#

def _get_dict(dictionary, mapList):
    """get value from nested dictionary using list of keys as path"""
    return reduce(lambda d, k: d[k], mapList, dictionary)

def _set_dict(dictionary, mapList, value):
    """set value into nested dictionary using list of keys as path"""
    _get_dict(dictionary, mapList[:-1])[mapList[-1]] = value

#** Classes **#
class ArgumentParser:
    """
    Handler object for parsing and running commands based on given values

    automatically accepts, validates, parses, and runs commands while also building
    help-page in case of any error
    """

    def __init__(self, app):
        self.app = app
        self._validate(
            {},
            {name:flag.names[0] for flag in self.app.flags for name in flag.names}, # all global flag names
            self.app.commands,
            "app"
        )

    def _validate(self, command_names, flag_names, commands, cmd_path):
        """recursively iterate commands and flags to ensure that no command names or flags are overlapping"""
        # check if command names are already in use
        for cmd in commands:
            for name in cmd.names():
                if name in command_names:
                    self.app.exit_with_error(
                        '{0}->{1}->command: "{2}", name: {3} in use by: "{4}"!'.format(
                            cmd_path, cmd.name, ", ".join(cmd.names()), name, command_names[name]), 2)
                else: command_names[name] = cmd.name
                # check if command flag names are already in use
                for flag in cmd.flags:
                    for name in flag.names:
                        if name in flag_names:
                            self.app.exit_with_error(
                                '{0}->{1}->flag: "{2}", name: "{3}" in use by: "{4}"!'.format(
                                    cmd_path, cmd.name, flag, name, flag_names[name]), 2)
                        else: flag_names[name] = flag.names[0]
            # run recursively for sub-commands and their flags
            self._validate(command_names, flag_names, cmd.subcommands, cmd_path+"->"+cmd.name)

    def _get_flags(self, context, flags, values):
        """
        parses the list of values for a dictionary object containing all of the flags used
        returns updated list of values along with flags
        """
        indexes = []   # list of indexes to delete from values
        collected = {} # dict of flags that were collected from values
        # list only flags but keep length and placement the same to check for flag matches
        only_flags = [word.lstrip("-") if word.startswith('-') else '' for word in values]
        # iterate flags attempting to index and collect values for each flag
        for flag in flags:
            index = flag.index(only_flags)
            if index > -1:
                indexes.append(index)
                # add flag=value if present else add flag=true
                if flag.has_value:
                    # check that value actually exists after flag
                    if index+1 >= len(values):
                        self.app.on_usage_error(context,
                            "Flag: %s requires value! (type=%r)" % (", ".join(flag.names), flag.__class__.__name__), 1)
                    value = flag.convert(values[index+1])
                    if not value:
                        self.app.exit_with_error("%s decode value failure: %r" % (flag, values[index+1]), 1)
                    # append value to collected flags
                    collected[flag.names[0]] = value
                    indexes.append(index+1) # append value's index to delete as well
                else:
                    collected[flag.names[0]] = True
            # add in default value if has one
            elif flag.default is not None:
                collected[flag.names[0]] = flag.default
        # remove indexes from values that are collected flags and their values
        # reverse order of indexes to delete them backwards to avoid issues
        for index in sorted(indexes, reverse=True):
            values.pop(index)
        return collected, values

    def _run_commands(self, context, values):
        """
        parse the values for flags, sub-commands, and main command arguments
        before building it into a context object and running the command's action
        then attempts to run recursively again with new context for sub-commands
        """
        # get command found in values
        (command, command_name) = (None, None)
        for cmd in context.command.subcommands:
            found_cmd = cmd.is_present(values)
            if found_cmd:
                command = cmd
                command_name = found_cmd
                break
        # check if any commands found
        if command is None: return False
        # attempt to collect flags for command
        flags, values = self._get_flags(context, command.flags, values)
        # check for out of place arguments in values
        if values.index(command_name) != 0:
            if values[0].startswith("-"):
                self.app.on_usage_error(context, "flag provided but not defined: %s" % values[0], context is not None)
            else: self.app.not_found_error(context, values[0])
        # collect arguments for command before any sub-commands
        sub_index = len(values)
        for cmd in command.subcommands:
            found_cmd = cmd.is_present(values)
            if found_cmd:
                sub_index = values.index(found_cmd)
                break
        # check if there are any invalid flags left in arguments
        args = values[1:sub_index]
        for arg in args:
            if arg.startswith("-"):
                self.app.on_usage_error(context, "flag provided but not defined: %s" % arg, context is not None)
        # create new context object and run command action
        context = Context(context.app, context.dictionary['global-flags'], context, command, flags, args)
        command.run(context) # run command's action with context
        # iterate again for commands sub-commands if available
        self._run_commands(context, values[sub_index:])
        return True

    def run(self, values):
        """
        collect data from values and parse into
        global-flags, command-flags, commands and command-arguments before
        adding them to context object and running commands recursively
        """
        # get global flags and update values
        global_flags, values = self._get_flags(None, self.app.flags, values)
        # create base context as place-holder
        context = GlobalContext(self.app, global_flags)
        # check if builtin help or version flag exists
        if global_flags['help']:
            show_app_help(context)
            raise SystemExit(0)
        if global_flags['version']:
            print("%s version %s" % (context.app.name, context.app.version), file=context.app.writer)
            raise SystemExit(0)
        # run app actions
        self.app.before(context)
        self.app.action(context)
        self.app.after(context)
        # attempt to collect commands and their subsequent flags
        # if no commands were found: print help page
        if not self._run_commands(context, values):
            show_app_help(context)
            raise SystemExit(0)






