from .commands import Command

#** Classes **#
class Args(list):

    def get(self, index):
        """return n-th argument in args"""
        return self[index]

    def first(self):
        """return 1st argument in args"""
        return self[0]

    def tail(self):
        """return all arguments but first"""
        return self[1:]

    def present(self):
        """return true if there are any arguments"""
        return len(self) != 0

    def swap(self, fromidx, toidx):
        """swap from and to index in list"""
        if fromidx >= len(self) or toidx >= len(self):
            raise ValueError("index out of range")
        self[fromidx], self[toidx] = self[toidx], self[fromidx]

class Context(object):

    def __init__(self, app, global_flags, parent_context, command, flags, args):
        self.app = app
        self.command = command
        self.dictionary = {
            'global-flags': global_flags,
            'flags': flags,
            'args': Args(args),
        }
        self.parent_c = parent_context

    def _set_flag(self, flag_name, value, flag_list, dict_key):
        """
        attempt to replace/write/create flag value
        according to primary flag name if possible
        """
        # attempt to overwrite existing value if exists
        if flag_name in self.dictionary[dict_key]:
            self.dictionary[dict_key][flag_name] = value
        else:
            # attempt to find main flag name and add it by that name
            for flag in flag_list:
                if flag_name in flag.names:
                    self.dictionary[dict_key][flag.names[0]] = value
                    return
            # if its not any existing flag name, add it as a new flag
            self.dictionary[dict_key][flag_name] = value

    def _get_flag(self, flag_name, flag_list, dict_key):
        """attempt to collect flag value by primary flag name"""
        if flag_name in self.dictionary[dict_key]:
            return self.dictionary[dict_key][flag_name]
        else:
            for flag in flag_list:
                if flag_name in flag.names:
                    return self.dictionary[dict_key][flag.names[0]]
        return False

    def _get_set(self, flag_name, flag_list, dict_key):
        """determine if flag name in list of flags using dict-key"""
        if flag_name in self.dictionary[dict_key]:
            return True
        else:
            for flag in flag_list:
                if flag_name in flag.names:
                    return flag.names[0] in self.dictionary[dict_key]
        return False

    def num_flags(self):
        """return number of flags"""
        return len(self.dictionary['flags'])

    def set(self, name, value):
        """add flag to flags dict"""
        return self._set_flag(name, value, self.command.flags, 'flags')

    def global_set(self, name, value):
        """add flag to global-flags dict"""
        return self._set_flag(name, value, self.app.flags, 'global-flags')

    def flag_set(self, name, value):
        """add flag to flags dict"""
        return self._set_flag(name, value, self.command.flags, 'flags')

    def global_flag(self, flag):
        """attempt to return global flag from dictionary"""
        return self._get_flag(flag, self.app.flags, 'global-flags')

    def flag(self, flag):
        """attempt to return local flag from dictionary"""
        return self._get_flag(flag, self.command.flags, 'flags')

    def flag_is_set(self, flag):
        """determine if command-flag is set"""
        return self._get_set(flag, self.command.flags, 'flags')

    def global_is_set(self, flag):
        """determine if global-flag is set"""
        return self._get_set(flag, self.app.flags, 'global-flags')

    def flag_names(self):
        """return list of flag names"""
        return [flag.names[0] for flag in self.dictionary['flags']]

    def global_flag_names(self):
        """return list of global-flag names"""
        return [flag.names[0] for flag in self.dictionary['global-flags']]

    def parent(self):
        """return parent context object"""
        return self.parent_c

    def args(self):
        """return list of arguments for command"""
        return self.dictionary['args']

    def narg(self):
        """return number of arguments"""
        return len(self.dictionary['args'])

class GlobalContext(Context):
    """
    global instance of Context object used as base parent context
    for any other context objects as well as the base object for
    ArgumentParser to use to parse all incoming arguments
    """

    def __init__(self, app, global_flags, args):
        command = Command("", subcommands=app.commands)
        super(GlobalContext, self).__init__(app, global_flags, None, command, None, args)