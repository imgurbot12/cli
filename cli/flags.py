import re
from datetime import timedelta

#** Variables **#
_dtregex = re.compile(r'((?P<hours>\d+?)hr)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

#** Function **#

def _assert_flags(flags):
    """assert that list of flags is valid"""
    if flags is not None:
        # ensure flags is list first
        assert (isinstance(flags, list))
        # ensure that each obj in list is correct type
        for obj in flags:
            assert(isinstance(obj, TypeFlag) or issubclass(obj.__class__, TypeFlag))

def _parse_name(name):
    """
    parse name into long and short form
    if short form is present
    """
    if ',' in name: return [n.strip() for n in name.split(",")]
    else: return [name.strip()]


#** Classes **#
class TypeFlag(object):
    """
    basic flag-type that allows you to specify the type of the flag value
    """

    def __init__(self, name, type, usage="", default=None, hidden=False, required=False):
        self.names = _parse_name(name)
        self.type = type
        self.usage = usage
        self.default = default
        self.hidden = hidden
        self.required = required
        self._builtin = False  # true if flag is built-into the app by default
        self.has_value = True  # true if flag-type has value to collect from args on input
        if default is not None:
            assert(isinstance(default, type))
            if required:
                raise AttributeError(
                    'flag: %r using default and required is redundant!' % (
                        ', '.join(self.names)
                    )
                )

    def __str__(self):
        return '-'+", ".join('-'+f for f in self.names)

    def __repr__(self):
        return "<%s: %r, usage: %r>" % (self.__class__.__name__, ", ".join(self.names), self.usage)

    def index(self, values):
        """
        return index of location in values if exists
        returns -1 if not found
        """
        for name in self.names:
            if name in values:
                return values.index(name)
        return -1

    def convert(self, string):
        """attempt to convert string to valid type for flag"""
        try: return self.type(string)
        except: return False

#** Sub-Classes **#

class BoolFlag(TypeFlag):

    def __init__(self, name, usage="", default=False, hidden=False, required=False):
        super(BoolFlag, self).__init__(name, int, usage, default, hidden, required)
        self.has_value = False  # bool-flag type has no set value at end of flag

class IntFlag(TypeFlag):

    def __init__(self, name, usage="", default=None, hidden=False, required=False):
        super(IntFlag, self).__init__(name, int, usage, default, hidden, required)

class FloatFlag(TypeFlag):

    def __init__(self, name, usage="", default=None, hidden=False, required=False):
        super(FloatFlag, self).__init__(name, float, usage, default, hidden, required)

class StringFlag(TypeFlag):

    def __init__(self, name, usage="", default=None, hidden=False, required=False):
        super(StringFlag, self).__init__(name, str, usage, default, hidden, required)

class ListFlag(TypeFlag):

    def __init__(self, name, usage="", default=None, hidden=False, required=False):
        super(ListFlag, self).__init__(name, list, usage, default, hidden, required)

class DurationFlag(TypeFlag):

    def __init__(self, name, usage="", default=None, hidden=False, required=False):
        # if default is string, parse into duration
        if isinstance(default, str):
            parsed = self._parse(default)
            if not parsed:
                raise ValueError("DurationFlag: %r INVALID Value: %r" % (name, default))
            else: default = parsed
        # run base-class init with arguments
        super(DurationFlag, self).__init__(name, int, usage, default, hidden, required)

    def _parse(self, time_str):
        """parse raw time-string into time-delta object before returning seconds"""
        parts = _dtregex.match(time_str)
        if not parts: return False
        if parts.end() == 0: return False
        return timedelta(**{k: int(v) for k, v in parts.groupdict().items() if v}).seconds

    def convert(self, string):
        """convert raw time-delta string into number of seconds"""
        try:
            return self._parse(string)
        except: return False

class EnumFlag(TypeFlag):
    """
    flag designed to allow for an enumeration of valid respones and types

    if the enum is a dictionary, rather than a set the given input will
    be automatically correlated to the corresponding value which can be of any
    type, else will simply return the valid value with its original type
    """

    def __init__(self, name, enum, usage="", default=None, hidden=False, required=False):
        super(EnumFlag, self).__init__(name, str, usage, default, hidden, required)
        assert isinstance(enum, set) or isinstance(enum, dict)
        self._enum = set()
        self._conv = enum if isinstance(enum, dict) else {i: i for i in enum}
        # iterate through enum and ensure values are valid-types
        for value in enum:
            if isinstance(value, str):
                self._enum.add(value)
            elif isinstance(value, int):
                self._enum.add(value)
            elif isinstance(value, float):
                self._enum.add(value)
            else:
                raise TypeError('enum values can only be str/int/float!')

    def convert(self, string):
        """converts to associated value based on matching enum"""
        # convert to valid type
        if string.isdigit():
            new = int(string)
        elif all(c == '.' or c.isdigit() for c in string) and string.count('.') <= 1:
            new = float(string)
        else:
            new = string
        # ensure is in enum
        if not new in self._enum:
            return False
        # return associated value or original depending on original enum
        return self._conv[new]
