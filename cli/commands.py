from .flags import _assert_flags

#** Functions **#

def _assert_calls(self, action, beforeFunc, afterFunc):
    """
    ensure the before and after function are valid
    before adding them to the class object
    """
    if action is not None:
        assert(callable(action))
        self.action = action
    if beforeFunc is not None:
        assert (callable(beforeFunc))
        self.before = beforeFunc
    if afterFunc is not None:
        assert (callable(afterFunc))
        self.after = afterFunc

def _assert_commands(subcommands):
    """assert that list of commands is valid"""
    if subcommands is not None:
        # ensure obj is list
        assert (isinstance(subcommands, list))
        # ensure each obj in list is Command
        for obj in subcommands:
            assert (isinstance(obj, Command))

#** Classes **#
class Command:

    def __init__(self,
                 name,
                 aliases=[],
                 usage="",
                 argsusage="",
                 category=" ",
                 hidden=False,
                 flags=[],
                 subcommands=[],
                 action=None,
                 beforeFunc=None,
                 afterFunc=None,
    ):
        self.name = name
        self.aliases = aliases
        self.usage = usage
        self.argsusage = argsusage
        self.category = category
        self.hidden = hidden
        self.flags = flags
        self.subcommands = subcommands
        # ensure function objects are callable
        _assert_calls(self, action, beforeFunc, afterFunc)
        # check types on flags
        _assert_flags(flags)
        _assert_commands(subcommands)

    def __str__(self):
        return "<Command: %r, Aliases: %s>" % (self.name, self.aliases)

    def __repr__(self):
        return self.__str__()

    def names(self):
        """return all names for command"""
        return [self.name]+self.aliases

    def has_name(self, name):
        """return true if command has the given name"""
        return name == self.name or name in self.aliases

    def visible_commands(self):
        """return sub-commands for command"""
        return [cmd for cmd in self.subcommands if not cmd.hidden]

    def visible_flags(self):
        """return flags that are not hidden"""
        return [flag for flag in self.flags if not flag.hidden]

    def is_present(self, values):
        """return true if name or any alias exists in list of values"""
        for value in values:
            if self.has_name(value):
                return value
        return False

    def after(self, context):
        pass

    def before(self, context):
        pass

    def action(self, context):
        pass

    def run(self, context):
        """run command and pass context object"""
        self.before(context)
        self.action(context)
        self.before(context)