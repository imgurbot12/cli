"""
Complete Application Execution Tests
"""
import unittest
from io import StringIO
from typing import *

from .. import *
from .content import v1, v2

#** Variables **#
__all__ = ['TestAppV1', 'TestAppV2']

#** Functions **#

def read_buffer(buf: StringIO) -> str:
    """
    read all content from bytes buffer
    """
    buf.seek(0, 0)
    return '\n'.join(['  '+l.rstrip() for l in buf.readlines() if l != '\n'])

#** Classes **#

class Base(unittest.IsolatedAsyncioTestCase):
    app: AbsApplication

    def __init__(self, methodName: str = "runTest") -> None:
        if self.__class__ is Base:
            methodName = 'skipBaseClass'
        super().__init__(methodName)

    def skipBaseClass(self):
        pass

    @classmethod
    def setUpClass(cls):
        if hasattr(cls, 'app'):
            cls.buffer = StringIO()
            cls.app.writer     = cls.buffer
            cls.app.err_writer = cls.buffer

    def setUp(self):
        if hasattr(self, 'buffer'):
            self.buffer.truncate(0) 

    async def runapp(self, 
        args:   List[str],
        error:  Optional[Type[CliError]] = None,
        path:   Optional[List[str]]      = None,
        expect: Optional[str]            = None,
        stdout: Optional[str]            = None,
    ):
        """
        run the app with the given arguments/flags and check for response

        :param args:   arguments to pass to cli
        :param error:  exception expected to be raised
        :param expect: message expected in error
        :param stdout: message expected in stdout/stderr
        """
        try:
            await exec_app(self.app, ['<cmd>', *args])
        except CliError as e:
            # raise error if not expected
            if error is None: 
                raise e
            # error error is of the expected-type
            self.assertIsInstance(e, error, msg='unexpected app error')
            # ensure path matches for not-found-errors
            if isinstance(e, NotFoundError) and path:
                self.assertEqual(e.path, path, msg='unexpected app path')
            # ensure error message matches expected
            if expect is not None:
                self.assertEqual(e.message, expect, msg='unexpected error msg')
        finally:
            if stdout is not None:
                content = read_buffer(self.buffer)
                self.assertIn(stdout, content, msg='unexpected app response')

    async def test_valid_help(self):
        """
        ensure help functionality works as intended
        """
        await self.runapp(['help', 'do', 'run'])

    async def test_invalid_help(self):
        """
        ensure error is raied on invalid help page
        """
        await self.runapp(
            args=['help', 'do', 'ayylmao'],
            path=[self.app.name, 'do'],
            error=NotFoundError,
        )

    async def test_flag_not_defined(self):
        """
        ensure error is raised on undefined-flags
        """
        await self.runapp(
            args=['echo', '-a'],
            path=[self.app.name, 'echo'],
            error=NotFoundError,
        )
        await self.runapp(
            args=['-a'],
            path=[self.app.name],
            error=NotFoundError,
        )
        await self.runapp(
            args=['do', 'run', '-a'],
            path=[self.app.name, 'do', 'run'],
            error=NotFoundError,
        )

    async def test_flag_invalid(self):
        """
        ensure error on invalid flag location
        """
        await self.runapp(
            args=['-d', 'echo', 'test'],
            path=[self.app.name],
            error=NotFoundError,
        )
        await self.runapp(['echo', 'test', '-d'], expect='test')
 
    async def test_flag_double(self):
        """
        ensure error when flag is defined and used twice
        """
        message = "flag 'debug, d' declared more than once"
        await self.runapp(
            args=['-d', '--debug', 'echo'],
            error=UsageError,
            expect=message,
        )
        await self.runapp(
            args=['-d', '-d', 'echo'],
            error=UsageError,
            expect=message,
        )

    async def test_invalid_command(self):
        """
        ensure error is raised with an invalid command
        """
        message = 'no action taken'
        await self.runapp(
            args=['badcmd'],
            error=UsageError,
            expect=message,
        )
        await self.runapp(
            args=['do'],
            error=UsageError,
            expect=message,
        )

    async def test_no_arguments(self):
        """
        ensure error is raised when arguments arent enough
        """
        await self.runapp(
            args=['do', 'run'],
            error=UsageError,
            expect="'run' must have exactly 1 arguments",
        )
        await self.runapp(
            args=['do', 'fly'],
            error=UsageError,
            expect="'fly' must have at least 1 arguments"
        )

    async def test_more_arguments(self):
        """
        ensure error is raised when too many arguments are present
        """
        await self.runapp(
            args=['do', 'run', '1', '2'],
            error=UsageError,
            expect="'run' must have exactly 1 arguments",
        )
        await self.runapp(
            args=['do', 'fly', '1', '2', '3'],
            error=UsageError,
            expect="'fly' can have at maximum 2 arguments"
        )
    
    async def test_valid_command(self):
        """
        ensure valid commands work as intended
        """
        await self.runapp(['do', 'run', '5'], stdout='running')
        await self.runapp(['do', 'fly', '5'], stdout='flying')

class TestAppV1(Base):
    app = v1

class TestAppV2(Base):
    app = v2
