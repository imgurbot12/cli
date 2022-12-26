import io
import unittest
from typing import *

from .. import App
from .app import v1, v2

#** Functions **#

def read_buffer(buf: io.StringIO) -> str:
    """
    read all content from bytes buffer
    """
    buf.seek(0, 0)
    return '\n'.join(['  '+l.rstrip() for l in buf.readlines() if l != '\n'])

#** Tests **#

class BaseTests:
    app: App
    
    def t(self, 
        args:   List[str], 
        raises: Optional[Exception] = None,
        expect: Optional[str]       = None,
    ):
        """
        run the app with the given arguments/flags and check for response

        :param args:   arguments to pass to cli
        :param raises: exception expected to be raised
        :param expect: message expected in error
        """
        buffer = io.StringIO()
        try:
            self.app.writer = buffer
            self.app.err_writer = buffer
            self.app.run(['<cmd>', *args])
        except (Exception, BaseException) as e:
            if raises is None:
                raise e
            self.assertIsInstance(e, raises, msg='unexpected app error')
        finally:
            content = read_buffer(buffer)
            self.assertIn(expect, content, msg='unexpected app response')
   
    def test_help(self):
        """
        validate and test help utility
        """
        self.t(['help', 'do', 'ayylmao'], SystemExit, 'No Help topic for: app->do->ayylmao')
   
    def test_flags(self):
        """
        validate and test flag parsing
        """
        name = self.app.name
        with self.subTest('not defined'):
            self.t(['echo', '-a'], SystemExit, 'Command: echo, Invalid Flag: -a')
            self.t(['-a'], SystemExit, f'Command: {name}, Invalid Flag: -a')
            self.t(['do', 'run', '-a'], SystemExit, 'Command: run, Invalid Flag: -a')
        with self.subTest('invalid location'):
            self.t(['-f', 'echo'], SystemExit, f'Command: {name}, Invalid Flag: -f')
        with self.subTest('double usage'):
            msg =  'Incorrect Usage: flag: debug, d declared more than once'
            self.t(['-d', '--debug', 'echo'], SystemExit, msg)
            self.t(['-d', '-d', 'echo'], SystemExit, msg)
    
    def test_command(self):
        """
        validate and test command parsing
        """
        no_action = 'Incorrect Usage: no action taken'
        exact_arg = 'Incorrect Usage: action must have exactly 1 arguments'
        few_args  = 'Incorrect Usage: action must have at least 1 arguments'
        many_args = 'Incorrect Usage: action can have at maximum 2 arguments'
        with self.subTest('invalid command'):
            self.t(['badcmd'], SystemExit, no_action)
        with self.subTest('no action configured'):
            self.t(['do'], SystemExit, no_action)
        with self.subTest('not enough arguments'):
            self.t(['do', 'run'], SystemExit, exact_arg)
            self.t(['do', 'fly'], SystemExit, few_args)
        with self.subTest('too many arguments'):
            self.t(['do', 'run', '1', '2'], SystemExit, exact_arg)
            self.t(['do', 'fly', '1', '2', '3'], SystemExit, many_args)
        with self.subTest('valid commands'):
            self.t(['do', 'run', '5'], None, 'running')
            self.t(['do', 'fly', '5'], None, 'flying')

class TestAppV1(unittest.TestCase, BaseTests):
    
    @classmethod
    def setUpClass(cls):
        cls.app = v1

class TestAppV2(unittest.TestCase, BaseTests):
    
    @classmethod
    def setUpClass(cls):
        cls.app = v2

