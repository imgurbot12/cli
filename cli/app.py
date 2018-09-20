from __future__ import print_function
from .parser import ArgumentParser
from .flags import _assert_flags, BoolFlag
from .commands import _assert_calls, _assert_commands
from .help import helpFlag, helpCommand, show_app_help, show_cmd_help
import sys

#** Variables **#
versionFlag = BoolFlag(name="version, v", usage="print the version")
versionFlag._builtin = True

#** Classes **#
class App:

    def __init__(self,
                 # basic settings
                 name,
                 usage,
                 version,
                 flags,
                 commands,
                 # app info settings
                 email="",
                 authors=[],
                 copyright="",
                 argsusage="",
                 description="",
                 # writer object
                 writer=sys.stdout,
                 errwriter=sys.stderr,
                 # help templates
                 help_template=None,
                 cmd_help_template=None,
                 # function handlers
                 action=None,
                 beforeFunc=None,
                 afterFunc=None,
                 cmdNotFoundFunc=None,
                 onUsageErrorFunc=None,
    ):
        self.name = name
        self.usage = usage
        self.version = version
        self.flags = [helpFlag, versionFlag] + flags
        self.commands = [helpCommand] + commands
        self.email = email
        self.authors = authors
        self.copyright = copyright
        self.argsusage = argsusage
        self.description = description
        self.writer = writer
        self.errwriter = errwriter
        self.help_template = help_template
        self.cmd_help_template = cmd_help_template
        self.categories = {}
        # assert basic attributes
        _assert_flags(flags)
        _assert_commands(commands)
        _assert_calls(self, action, beforeFunc, afterFunc)
        # build categories
        for cmd in self.commands:
            if not cmd.hidden:
                if cmd.category not in self.categories:
                    self.categories[cmd.category] = []
                self.categories[cmd.category].append(cmd)
        # ensure error calls are valid
        if cmdNotFoundFunc is not None:
            assert(callable(cmdNotFoundFunc))
            self.not_found_error = cmdNotFoundFunc
        if onUsageErrorFunc is not None:
            assert(callable(onUsageErrorFunc))
            self.on_usage_error = onUsageErrorFunc

    def command(self, name):
        """return command if name exists"""
        for cmd in self.commands:
            if cmd.has_name(name):
                return cmd
        return False

    def visible_categories(self):
        """return category names for each category"""
        return [category for category in self.categories.keys()]

    def visible_commands(self):
        """return commands that are not hidden"""
        return [cmd for cmd in self.commands if not cmd.hidden]

    def visible_flags(self):
        """return flags that are not hidden"""
        return [flag for flag in self.flags if not flag.hidden and not flag._builtin]

    def not_found_error(self, context, command):
        """default error handler for command-not-found"""
        print("No help topic for %r\n" % command, file=self.errwriter)
        raise SystemExit(3)

    def on_usage_error(self, context, error, isSubCmd):
        """default error handler for command-usage-error"""
        print("Incorrect Usage: %s\n" % error, file=self.writer)
        if isSubCmd:
            show_cmd_help(context, context.command)
        else:
            show_app_help(self)
        raise SystemExit(4)

    def exit_with_error(self, error, exitcode):
        print("App-Error: %s" % error, file=self.errwriter)
        raise SystemExit(exitcode)

    def before(self, context):
        pass

    def after(self, context):
        pass

    def action(self, context):
        """
        attempt to collect commands and their subsequent flags
        if no commands were found: print help page
        """
        if not self.parser.run_commands(context):
            show_app_help(context.app)

    def run(self, args):
        self.parser = ArgumentParser(self)
        self.parser.run(args[1:])