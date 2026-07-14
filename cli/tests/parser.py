"""
CLI Parser UnitTests
"""
from pathlib import Path
from typing import List
from unittest import TestCase

from ._apps import APP_V1
from .. import Arg, Command, Parser, ParsedCmd
from ..parser import Context, CommandRequired, Missing, Unexpected

#** Variables **#
__all__ = ['ParserTests']

#DONE: support repeated arguments

#TODO: parser should include quote/text strings
#TODO: when validating arg values - check if might actually be a flag
#      (allow if string is quote vs error if text)

#** Classes **#

class ParserTests(TestCase):
    app: Command = APP_V1

    def parse(self, args: List[str]) -> ParsedCmd:
        """
        """
        return Parser(self.app).parse(args)

    def assertPath(self, ctx: Context, path: List[str]):
        """
        """
        expected = [c.name for c in ctx.path]
        self.assertListEqual(expected, path)

    def test_flag_not_defined(self):
        """
        ensure error is raised on undefined-flags
        """
        tests = [
            (['echo', '-a'], ['echo'], ['-a']),
            (['-a'], [], ['-a']),
            (['do', 'run', '1', '-a'], ['do', 'run'], ['-a']),
        ]
        for args, path, unexpected in tests:
            with self.subTest(args):
                try:
                    self.parse(args)
                    self.assertFalse(True)
                except Unexpected as e:
                    self.assertPath(e.ctx, [self.app.name, *path])
                    self.assertListEqual(e.unexpected, unexpected)

    def test_flag_invalid(self):
        """
        ensure error invalid flag location
        """
        tests = [
            (['-f', 'echo', 'test'], [], ['-f']),
            (['echo', 'test', '-l'], ['echo'], ['-l']),
            (['echo', 'test', '-u'], ['echo'], ['-u']),
        ]
        for args, path, unexpected in tests:
            with self.subTest(args):
                try:
                    self.parse(args)
                    self.assertFalse(True)
                except Unexpected as e:
                    self.assertPath(e.ctx, [self.app.name, *path])
                    self.assertListEqual(e.unexpected, unexpected)

    def test_flag_double(self):
        """
        ensure error when flag is defined and used twice
        """
        tests = [
            (['-u', 'a', '-u', 'b'], [], ['-u', 'b']),
            (['-d', '-d'], [], ['-d']),
            (['-d', '--debug'], [], ['--debug']),
            (['--debug', '-d'], [], ['-d']),
            (['echo', 'test', '-f', 'a', '-f', 'b'], ['echo'], ['-f']),
        ]
        for args, path, unexpected in tests:
            with self.subTest(args):
                try:
                    self.parse(args)
                    self.assertFalse(True)
                except Unexpected as e:
                    self.assertPath(e.ctx, [self.app.name, *path])
                    self.assertListEqual(e.unexpected, unexpected)

    def test_invalid_command(self):
        """
        ensure error is raised with invalid command/argument
        """
        tests = [
            (['badcmd'], [], ['badcmd']),
            (['do', 'badcmd'], ['do'], ['badcmd']),
        ]
        for args, path, unexpected in tests:
            with self.subTest(args):
                try:
                    self.parse(args)
                    self.assertFalse(True)
                except Unexpected as e:
                    self.assertPath(e.ctx, [self.app.name, *path])
                    self.assertListEqual(e.unexpected, unexpected)

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

    def test_argument_missing(self):
        """
        ensure error is raised when arguments arent enough
        """
        tests = [
            (['echo'], ['echo'], [Arg('test')]),
            (['do', 'run'], ['do', 'run'], [Arg('dist1')]),
            (['do', 'fly'], ['do', 'fly'], [Arg('dist2')]),
        ]
        for args, path, missing in tests:
            with self.subTest(args):
                try:
                    self.parse(args)
                    self.assertFalse(True)
                except Missing as e:
                    self.assertPath(e.ctx, [self.app.name, *path])
                    self.assertEqual(len(e.missing), len(missing))
                    for actual, expect in zip(e.missing, missing):
                        self.assertEqual(actual.__class__, expect.__class__)
                        self.assertEqual(actual.name, expect.name)

    def test_argument_extra(self):
        """
        ensure error is raised when too many arguments are present
        """
        tests = [
            (['do', 'run', '1', '2', '3'], ['do', 'run'], ['3']),
            (['do', 'fly', '4', '5'], ['do', 'fly'], ['5']),
        ]
        for args, path, unexpected in tests:
            with self.subTest(args):
                try:
                    self.parse(args)
                    self.assertFalse(True)
                except Unexpected as e:
                    self.assertPath(e.ctx, [self.app.name, *path])
                    self.assertListEqual(e.unexpected, unexpected)

    def test_valid_command(self):
        """
        ensure valid commands work as intended
        """
        app_opts = {'user': 'root', 'log': 10, 'debug': False}
        result = self.parse(['-d'])
        self.assertDictEqual(result.args, {})
        self.assertDictEqual(result.flags, {**app_opts, 'debug': True})
        self.assertDictEqual(result.commands, {})

        result = self.parse(['echo', '-d', '-f', 'file', 'test'])
        echo   = result.commands['echo']
        self.assertDictEqual(result.args, {})
        self.assertDictEqual(result.flags, app_opts)
        self.assertDictEqual(echo.flags, {'dry': True, 'file': Path('file')})

        result = self.parse(['echo', '--', '-d', '-f', 'file', 'test'])
        echo   = result.commands['echo']
        self.assertDictEqual(result.args, {})
        self.assertDictEqual(result.flags, app_opts)
        self.assertDictEqual(echo.args, {'test': ['-d', '-f', 'file', 'test']})
        self.assertDictEqual(echo.flags, {'dry': False, 'file': None})

        args = [
            ['do', 'run', '--', '5'],
            ['do', 'run', '5'],
        ]
        for args in args:
            with self.subTest(args):
                result = self.parse(args)
                do     = result.commands['do']
                self.assertDictEqual(result.args, {})
                self.assertDictEqual(result.flags, app_opts)
                self.assertDictEqual(do.args, {})
                self.assertDictEqual(do.flags, {'kill': False})
                self.assertDictEqual(do.commands['run'].args, {'dist1': 5, 'dist2': 1})
                self.assertDictEqual(do.commands['run'].flags, {'km': False})
                self.assertDictEqual(do.commands['run'].commands, {})

