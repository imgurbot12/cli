"""
CLI UI Coloring/Styling Utilities
"""
from abc import abstractmethod
from typing import Dict, Literal, Protocol, Tuple, Union

#** Variables **#
__all__ = [
    'Rgb',
    'SimpleColor',
    'Color',

    'Styling',
    'AnsiTermStyle',
]

Rgb         = Tuple[int, int, int]
SimpleColor = Literal['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan',
    'white', 'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
    'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white']

Color = Union[SimpleColor, Rgb]
Style = Literal['bold', 'dim', 'underline', 'overline',
    'italic', 'blink', 'reverse', 'strike']

#** Classes **#

class Styling(Protocol):
    """
    Output Styling Abstraction (Primarily for ANSI Terminal Codes)
    """
    BLACK:           str
    RED:             str
    GREEN:           str
    YELLOW:          str
    BLUE:            str
    MAGENTA:         str
    CYAN:            str
    WHITE:           str
    BRIGHT_BLACK:    str
    BRIGHT_RED:      str
    BRIGHT_GREEN:    str
    BRIGHT_YELLOW:   str
    BRIGHT_BLUE:     str
    BRIGHT_MAGENTA:  str
    BRIGHT_CYAN:     str
    BRIGHT_WHITE:    str

    @abstractmethod
    def format_rgba(self, r: int, g: int, b: int):
        """
        format rgb color in the relevant style
        """
        raise NotImplementedError

    @abstractmethod
    def reset_color(self, color: Color) -> str:
        """
        reset the styling of the specified color
        """
        raise NotImplementedError

    @abstractmethod
    def format_style(self, style: Style) -> str:
        """
        return format for the specific text styling
        """
        raise NotImplementedError

    @abstractmethod
    def reset_style(self, style: Style) -> str:
        """
        return reset for the specific text styling
        """
        raise NotImplementedError

    def format_simple(self, color: SimpleColor) -> str:
        """
        format a simple color with its relevant prefix
        """
        return getattr(self, color.upper())

    def format_color(self, color: Color) -> str:
        """
        return formating for a color (both simple/rgb)
        """
        if isinstance(color, tuple):
            return self.format_rgba(*color)
        return self.format_simple(color)

    def wrap_color(self, color: Color, text: str):
        """
        wrap the given text with the specified color formatting
        """
        return f'{self.format_color(color)}{text}{self.reset_color(color)}'

    def wrap_style(self, style: Style, text: str):
        """
        wrap the given text with the specified style formatting
        """
        return f'{self.format_style(style)}{text}{self.reset_style(style)}'

    def toggle_color(self, color: Color, apply: bool):
        """
        toggle color as either format or reset
        """
        return self.format_color(color) if apply else self.reset_color(color)

    def toggle_style(self, style: Style, apply: bool):
        """
        toggle style as either format or reset
        """
        return self.format_style(style) if apply else self.reset_style(style)

class AnsiTermStyle(Styling):
    """
    Terminal ANSI Escape Codes for Styling
    """
    ANSI_ADD: Dict[Style, int] = {
        'bold':      1,
        'dim':       2,
        'underline': 4,
        'overline':  53,
        'italic':    3,
        'blink':     5,
        'reverse':   7,
        'strike':    9,
    }
    ANSI_CLEAR: Dict[Style, int] = {
        'bold':      22,
        'dim':       22,
        'underline': 24,
        'overline':  55,
        'italic':    23,
        'blink':     25,
        'reverse':   27,
        'strike':    29,
    }

    BLACK          = '\033[30m'
    RED            = '\033[31m'
    GREEN          = '\033[32m'
    YELLOW         = '\033[33m'
    BLUE           = '\033[34m'
    MAGENTA        = '\033[35m'
    CYAN           = '\033[36m'
    WHITE          = '\033[37m'
    BRIGHT_BLACK   = '\033[90m'
    BRIGHT_RED     = '\033[91m'
    BRIGHT_GREEN   = '\033[92m'
    BRIGHT_YELLOW  = '\033[93m'
    BRIGHT_BLUE    = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN    = '\033[96m'
    BRIGHT_WHITE   = '\033[97m'

    def format_rgba(self, r: int, g: int, b: int):
        return f'\033[38;2;{r:d};{g:d};{b:d}m'

    def reset_color(self, color: Color) -> str:
        return '\033[39m'

    def format_style(self, style: Style) -> str:
        return f'\033[{self.ANSI_ADD[style]}m'

    def reset_style(self, style: Style) -> str:
        return f'\033[{self.ANSI_CLEAR[style]}m'
