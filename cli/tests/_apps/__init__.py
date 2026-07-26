"""
Application Implementations for UnitTests
"""
from typing_extensions import Annotated

from ...suggest import Suggest

#** Variables **#
__all__ = ['APP_V1', 'APP_V2']

USERS  = ['bob', 'jeff', 'jerry', 'aiden', 'admin', 'root']
REPEAT = [1, 2, 3, 11]

User   = Annotated[str, Suggest[USERS]]
Repeat = Annotated[int, Suggest[REPEAT]]

#** Imports **#
from .v1 import APP_V1
from .v2 import APP_V2
