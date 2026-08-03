"""
CLI Parser UnitTests
"""
from pathlib import Path
from typing import Iterable, List, Tuple, Type, Union, cast
from unittest import TestCase

from ._apps import APP_V1, APP_V2
from .. import Arg, Command, Flag, Parser, ParsedCmd
from ..parser import Invalid, MissingValue, ParseCtx, CommandRequired, Missing, Unexpected

#** Variables **#
__all__ = ['ParserTestsV1', 'ParserTestsV2']

DEFAULT_OPTS = {'user': 'root', 'log': 10, 'debug': False, 'repeat': None, 'help': False}

#** Classes **#

class ParserTests(TestCase):
    __test__ = False

    app: Command

    def parse(self, args: List[str]) -> ParsedCmd:
        """
        """
        return Parser(self.app).parse(args)

    def assertPath(self, ctx: ParseCtx, path: List[str]):
        """
        """
        expected = [c.name for c in ctx.path]
        self.assertListEqual(expected, path)

    def assertMissing(self,
        args:      List[str],
        path:      List[str],
        missing:   List[Union[Arg, Flag]],
        exception: Union[Type[Missing], Type[MissingValue]] = Missing,
    ):
        """
        """
        error = None
        try:
            self.parse(args)
            self.assertFalse(True)
        except exception as e:
            error = e
        self.assertIsNotNone(error)
        error = cast(Missing, error)
        self.assertPath(error.ctx, [self.app.name, *path])
        self.assertEqual(len(error.missing), len(missing))
        for actual, expect in zip(error.missing, missing):
            self.assertEqual(actual.__class__, expect.__class__)
            self.assertEqual(actual.name, expect.name)

    def assertMissingMulti(self,
        tests:     Iterable[Tuple[List[str], List[str], List[Union[Arg, Flag]]]],
        exception: Union[Type[Missing], Type[MissingValue]] = Missing,
    ):
        """
        """
        for args, path, unexpected in tests:
            with self.subTest(args):
                self.assertMissing(args, path, unexpected, exception)

    def assertInvalid(self,
        args: List[str], path: List[str], missing: List[Union[Arg, Flag]]):
        """
        """
        error = None
        try:
            self.parse(args)
            self.assertFalse(True)
        except Invalid as e:
            error = e
        self.assertIsNotNone(error)
        error = cast(Invalid, error)
        self.assertPath(error.ctx, [self.app.name, *path])
        self.assertEqual(len(error.invalid), len(missing))
        for actual, expect in zip(error.invalid, missing):
            self.assertEqual(actual.__class__, expect.__class__)
            self.assertEqual(actual.name, expect.name)

    def assertInvalidMulti(self,
        tests: Iterable[Tuple[List[str], List[str], List[Union[Arg, Flag]]]]):
        """
        """
        for args, path, unexpected in tests:
            with self.subTest(args):
                self.assertInvalid(args, path, unexpected)

    def assertUnexpected(self,
        args: List[str], path: List[str], unexpected: List[str]):
        """
        """
        error = None
        try:
            self.parse(args)
            self.assertFalse(True)
        except Unexpected as e:
            error = e
        self.assertIsNotNone(error)
        error = cast(Unexpected, error)
        self.assertPath(error.ctx, [self.app.name, *path])
        self.assertListEqual(error.unexpected, unexpected)

    def assertUnexpectedMulti(self,
        tests: Iterable[Tuple[List[str], List[str], List[str]]]):
        """
        """
        for args, path, unexpected in tests:
            with self.subTest(args):
                self.assertUnexpected(args, path, unexpected)

    def test_flag_not_defined(self):
        """
        ensure error is raised on undefined-flags
        """
        self.assertUnexpectedMulti([
            (['-a'], [], ['-a']),
            (['echo', '-a'], ['echo'], ['-a']),
            (['do', 'run', '1', '-a'], ['do', 'run'], ['-a']),
        ])

    def test_flag_invalid(self):
        """
        ensure error invalid flag location
        """
        self.assertUnexpectedMulti([
            (['-f', 'echo', 'test'], [], ['-f']),
            (['echo', 'test', '-l'], ['echo'], ['-l']),
            (['echo', 'test', '-u'], ['echo'], ['-u']),
        ])

    def test_flag_invalid_value(self):
        """
        ensure error on flag invalid value
        """
        self.assertInvalidMulti([
            (['-l', 'a'], [], [Flag('log')]),
            (['-l', 'a', '-r', '1', '-r', '2'], [], [Flag('log')]),
            (['-l', 'a', '-r', '1', '-r', 'a'], [], [Flag('log'), Flag('repeat')]),
        ])

    def test_flag_missing_value(self):
        """
        ensure error on flag missing value
        """
        self.assertMissingMulti([
            (['-u'], [], [Flag('user')]),
            (['-l'], [], [Flag('log')]),
            (['-r', '1', '-r'], [], [Flag('repeat')]),
            (['-u', 'echo', 'test'], [], [Flag('user')]),
            (['echo', 'test', '-f'], ['echo'], [Flag('file')]),
        ], MissingValue)

    def test_flag_repeat(self):
        """
        ensure repeated flags work as intended or error if not repeat
        """
        result = self.parse(['-r', '1', '-r', '2', '-r', '3'])
        self.assertDictEqual(result.args, {})
        self.assertDictEqual(result.flags, {**DEFAULT_OPTS, 'repeat': [1,2,3]})
        self.assertDictEqual(result.commands, {})
        self.assertUnexpectedMulti([
            (['-u', 'a', '-u', 'b'], [], ['-u', 'b']),
            (['-d', '-d'], [], ['-d']),
            (['-d', '--debug'], [], ['--debug']),
            (['--debug', '-d'], [], ['-d']),
            (['echo', 'test', '-f', 'a', '-f', 'b'], ['echo'], ['-f']),
        ])

    def test_argument_extra(self):
        """
        ensure error is raised when too many arguments are present
        """
        self.assertUnexpectedMulti([
            (['do', 'run', '1', '2', '3'], ['do', 'run'], ['3']),
            (['do', 'fly', '4', '5'], ['do', 'fly'], ['5']),
        ])

    def test_argument_missing(self):
        """
        ensure error is raised when arguments arent enough
        """
        self.assertMissingMulti([
            (['echo'], ['echo'], [Arg('test')]),
            (['do', 'run'], ['do', 'run'], [Arg('dist1')]),
            (['do', 'fly'], ['do', 'fly'], [Arg('dist2')]),
        ])

    def test_argument_invalid(self):
        """
        ensure error is raised when arugment is invalid
        """
        self.assertInvalidMulti([
            (['do', 'run', 'a'], ['do', 'run'], [Arg('dist1')]),
            (['do', 'run', '1', 'b'], ['do', 'run'], [Arg('dist2')]),
            (['do', 'run', 'a', 'b'], ['do', 'run'], [Arg('dist1'), Arg('dist2')]),
            (['do', 'fly', 'a'], ['do', 'fly'], [Arg('dist2')])
        ])

    def test_command_invalid(self):
        """
        ensure error is raised with invalid command/argument
        """
        self.assertUnexpectedMulti([
            (['badcmd'], [], ['badcmd']),
            (['do', 'badcmd'], ['do'], ['badcmd']),
        ])

    def test_command_missing(self):
        """
        ensure error is raised when subcommand is required
        """
        try:
            self.parse(['do'])
            self.assertFalse(True)
        except CommandRequired as e:
            self.assertPath(e.ctx, [self.app.name, 'do'])
            self.assertListEqual([c.name for c in e.commands], ['run', 'fly'])

    def test_simple(self):
        """
        ensure simple single-command parse works as intended
        """
        result = self.parse([])
        self.assertDictEqual(result.args, {})
        self.assertDictEqual(result.flags, DEFAULT_OPTS)
        self.assertDictEqual(result.commands, {})

        result = self.parse(['-d'])
        self.assertDictEqual(result.args, {})
        self.assertDictEqual(result.flags, {**DEFAULT_OPTS, 'debug': True})
        self.assertDictEqual(result.commands, {})

        for value in ('info', '20'):
            with self.subTest(value):
                result = self.parse(['-l', value])
                self.assertDictEqual(result.args, {})
                self.assertDictEqual(result.flags, {**DEFAULT_OPTS, 'log': 20})
                self.assertDictEqual(result.commands, {})

    def test_sub_command(self):
        """
        ensure single sub-command parse works as intended
        """
        result = self.parse(['echo', '-d', '-f', 'file', 'test'])
        echo   = result.commands['echo']
        self.assertEqual(len(echo), 1)
        self.assertDictEqual(result.args, {})
        self.assertDictEqual(result.flags, DEFAULT_OPTS)
        self.assertEqual(len(result.commands), 1)
        self.assertDictEqual(echo[0].flags, {'dry': True, 'file': Path('file')})

        result = self.parse(['echo', '--', '-d', '-f', 'file', 'test'])
        echo   = result.commands['echo']
        self.assertEqual(len(echo), 1)
        self.assertDictEqual(result.args, {})
        self.assertDictEqual(result.flags, DEFAULT_OPTS)
        self.assertEqual(len(result.commands), 1)
        self.assertDictEqual(echo[0].args, {'test': ['-d', '-f', 'file', 'test']})
        self.assertDictEqual(echo[0].flags, {'dry': False, 'file': None})

    def test_subsub_command(self):
        """
        ensure double sub-command parse works as intended
        """
        args = (['do', 'run', '--', '5'], ['do', 'run', '5'])
        for args in args:
            with self.subTest(args):
                result = self.parse(args)
                dos    = result.commands['do']
                do     = dos[0]
                runs   = do.commands['run']
                run    = runs[0]
                self.assertEqual(len(dos), 1)
                self.assertEqual(len(runs), 1)
                self.assertDictEqual(result.args, {})
                self.assertDictEqual(result.flags, DEFAULT_OPTS)
                self.assertDictEqual(do.args, {})
                self.assertDictEqual(do.flags, {'kill': False})
                self.assertDictEqual(run.args, {'dist1': 5, 'dist2': 42})
                self.assertDictEqual(run.flags, {'km': False})
                self.assertDictEqual(run.commands, {})

class ParserTestsV1(ParserTests):
    __test__ = True
    app: Command = APP_V1

class ParserTestsV2(ParserTests):
    __test__ = True
    app: Command = APP_V2
