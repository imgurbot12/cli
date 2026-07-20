"""
CLI Suggestion UnitTests
"""
from typing import List
from unittest import TestCase

from ._apps import USERS, APP_V1
from .. import Command, Suggestor

#** Variables **#
__all__ = ['SuggestTests']

#** Classes **#

class SuggestTests(TestCase):
    app: Command = APP_V1

    def suggest(self, args: List[str], partial: bool = False) -> List[str]:
        """
        """
        return Suggestor(self.app).suggest_list(args, partial)

    def assertSuggest(self,
        args: List[str], expect: List[str], partial: bool = False):
        """
        """
        results = self.suggest(args, partial)
        self.assertListEqual(results, expect)

    def test_command(self):
        """
        """
        self.assertSuggest([], ['echo', 'do', '-u', '--user', '-l', '--log', '-d', '--debug', '-r', '--repeat'])
        self.assertSuggest(['do'], ['run', 'fly'])

    def test_flag(self):
        """
        """
        self.assertSuggest(['-'], ['u', '-user', 'l', '-log', 'd', '-debug', 'r', '-repeat'], True)
        self.assertSuggest(['--'], ['user', 'log', 'debug', 'repeat'], True)
        self.assertSuggest(['-u'], [], True)
        self.assertSuggest(['-u', 'jeff', '--'], ['log', 'debug', 'repeat'], True)
        self.assertSuggest(['-u', 'jeff', '-r', '1', '--'], ['log', 'debug', 'repeat'], True)
        self.assertSuggest(['do', 'run', '1', '1', '-'], ['-km'], True)

    def test_flag_value(self):
        """
        """
        self.assertSuggest(['-u'], USERS)
        self.assertSuggest(['-u', 'b'], ['ob'], True)
        self.assertSuggest(['-u', 'a'], ['iden', 'dmin'], True)
        self.assertSuggest(['-u', 'ai'], ['den'], True)
        self.assertSuggest(['-u', 'j'], ['eff', 'erry'], True)
        self.assertSuggest(['-u', 'je'], ['ff', 'rry'], True)
        self.assertSuggest(['-u', 'jeff'], [], True)
        self.assertSuggest(['-u', 'jeff'], ['echo', 'do', '-l', '--log', '-d', '--debug', '-r', '--repeat'])

    def test_argument(self):
        """
        """
        self.assertSuggest(['do', 'run'], ['1', '2', '3', '11'])
        self.assertSuggest(['do', 'run', '1'], ['1'], True)
        self.assertSuggest(['do', 'run', '1'], ['42'])
        self.assertSuggest(['do', 'run', '1', '1'], ['--km'])
        self.assertSuggest(['do', 'fly'], [])
        self.assertSuggest(['do', 'fly', '1'], ['--km'])
