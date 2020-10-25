"""
basic test-suite used to ensure cli outputs expected response per given command
"""
import sys
from io import StringIO
from datetime import timedelta

import cli

#** Variables **#
tests = {
    'flag-not-defined': {
        'cmd': 'pcap -d',
        'fail': True,
        'expect': 'Command: pcap, Invalid Flag: -d',
    },
    'help-pre-args': {
        'cmd': 'help pcap run asdf',
        'fail': True,
        'expect': 'No Help topic for: app->pcap->run'
    },
    'help-pre-flag': {
        'cmd': '--debug help pcap run',
        'fail': False,
        'expect': ''
    },
    'double-flag': {
        'cmd': '--debug --debug pcap run',
        'fail': True,
        'expect': 'Incorrect Usage: flag: debug declared more than once',
    },
    'bad-global-flag': {
        'cmd': '-asdf',
        'fail': True,
        'expect': 'Command: VBoxD, Invalid Flag: -asdf',
    },
    'bad-command-flag': {
        'cmd': 'pcap -asdf',
        'fail': True,
        'expect': 'Command: pcap, Invalid Flag: -asdf',
    },
    'bad-sub-command-flag': {
        'cmd': 'pcap run -asdf',
        'fail': True,
        'expect': 'Command: run, Invalid Flag: -asdf',
    },
}

app = cli.App(
    name='VBoxD',
    usage='VirtualBox Daemon Management Tool',
    version='1.0.0',
    flags=[
        cli.StringFlag(
            name='user, u',
            usage='specify alternative user to run under'
        ),
        cli.StringFlag(
            name='log, l',
            usage='specify logging level for whole application',
            default='INFO'
        ),
        cli.BoolFlag(
            name='debug',
            usage='same as --log DEBUG'
        )
    ],
    commands=[
        # show config command
        cli.Command(
            name='show',
            usage='show current interpreted config',
            category='config management'
        ),
        # pcap command
        cli.Command(
            name='pcap',
            usage='run pcap on given vm interfaces',
            argsusage='[vm-name] [flags...]',
            flags=[
              cli.BoolFlag(name='tflag, s', usage='test flag under pcap'),
            ],
            commands=[
                cli.Command(
                    name='configure',
                    usage='configure vm to allow for pcap while active',
                    argsusage='[vm-name]',
                    flags=[
                        cli.BoolFlag(
                            name='force, f',
                            usage='force configuration to complete',
                            default=False,
                        )
                    ]
                ),
                cli.Command(
                    name='run',
                    usage='run pcap for given duration',
                    argsusage='[vm-name] [flags...]',
                    flags=[
                        cli.StringFlag(
                            name='output, o',
                            usage='file output for pcap',
                        ),
                        cli.DurationFlag(
                            name='duration, d',
                            usage='time spent capturing packets',
                            default=timedelta(seconds=0),
                        ),
                    ],
                ),
            ],
        ),
        # cpillar command
        cli.Command(
            name='cpillar',
            usage='collect hashes of given file-path into given file',
            argsusage='[vm-name] [path]',
            flags=[
                cli.StringFlag(
                    name='output o',
                    usage='output file',
                ),
                cli.StringFlag(
                    name='alg, a',
                    usage='specify hash algorithm',
                    default='sha1',
                ),
                cli.IntFlag(
                    name='workers, w',
                    usage='specify number of workers',
                    default=5,
                ),
                cli.IntFlag(
                    name='chunk, c',
                    usage='specify read chunk size',
                    default=4096,
                ),
                cli.IntFlag(
                    name='maxsize, mfs',
                    usage='specify max file size to hash',
                    default=0,
                ),
                cli.DurationFlag(
                    name='time, t',
                    usage='specify max time spent on single hash',
                    default=timedelta(0),
                ),
                cli.IntFlag(
                    name='drive, d',
                    usage='specify drive instance in case of multiple drives',
                )
            ],
            action=None,
        )
    ],
)

#** Functions **#

def _get_output(buf: StringIO) -> str:
    '''
    retrieve output from StringIO
    '''
    buf.seek(0, 0)
    return '\n'.join(['  '+l.rstrip() for l in buf.readlines() if l != '\n'])

def main():
    """run all tests"""
    for name, test in tests.items():
        # set outputs
        buf = StringIO()
        try:
            app.writer     = buf
            app.err_writer = buf
            app.run([sys.executable] + test['cmd'].split())
            # if test succeeded unexpectedly
            output = _get_output(buf)
            if test['fail']:
                print(f'test succeeded unexpectedly: {name}')
                print(f'Output:\n{output}')
                break

        except (Exception, BaseException):
            output = _get_output(buf)
            # if test failed unexpectedly
            if not test['fail']:
                print(f'test failed unexpectedly: {name}')
                print(f'Output:\n{output}')
                break

        # if test returned with unexpected output
        if test['expect'] not in output:
            print(f'test: {name}, missing expected output: {test["expect"]}')
            print(f'Output:\n{output}')
            break

    # show all tests passed
    else:
        print('All Tests Verified! Working!')

#** Init **#
if __name__ == '__main__':
    main()
