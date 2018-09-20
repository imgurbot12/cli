import cli
import sys

try: from StringIO import StringIO
except: from io import StringIO

tests = {
    'flag-not-defined': {
        'cmd': 'pcap -d',
        'fail': True,
        'expect': 'Incorrect Usage: flag provided but not defined: -d',
    },
    'help-pre-args': {
        'cmd': 'asdf help pcap run',
        'fail': True,
        'expect': "No help topic for 'asdf'"
    },
    'help-pre-flag': {
        'cmd': '--debug help pcap run',
        'fail': False,
        'expect': ""
    },
    'double-flag': {
        'cmd': 'pcap run --debug --debug',
        'fail': True,
        'expect': "Incorrect Usage: Flag: 'debug' is repeated!",
    },
    'bad-global-flag': {
        'cmd': '-asdf',
        'fail': True,
        'expect': 'Incorrect Usage: flag provided but not defined: -asdf',
    },
    'bad-command-flag': {
        'cmd': 'pcap -asdf',
        'fail': True,
        'expect': 'Incorrect Usage: flag provided but not defined: -asdf',
    },
    'bad-sub-command-flag': {
        'cmd': 'pcap run -asdf',
        'fail': True,
        'expect': 'Incorrect Usage: flag provided but not defined: -asdf',
    },
}

app = cli.App(
    name="VBoxD",
    usage="VirtualBox Daemon Management Tool",
    version="1.0.0",
    flags=[
        cli.StringFlag(name="user, u", usage="specify alternative user to run under"),
        cli.StringFlag(name="log, l", usage="specify logging level for whole application", default="INFO"),
        cli.BoolFlag(name="debug", usage="same as --log DEBUG",)
    ],
    commands=[
        # show config command
        cli.Command(name="show", usage="show current interpreted config", category="config management"),
        # pcap command
        cli.Command(
            name="pcap",
            usage="run pcap on given vm interfaces",
            argsusage="[vm-name] [flags...]",
            flags=[
              cli.BoolFlag(name='tflag, s', usage='test flag under pcap'),
            ],
            subcommands=[
                cli.Command(
                    name="configure",
                    usage="configure vm to allow for pcap while active",
                    argsusage="[vm-name]",
                    flags=[
                        cli.BoolFlag(
                            name="force, f",
                            usage="force configuration to complete",
                            default=False,
                        )
                    ]
                ),
                cli.Command(
                    name="run",
                    usage="run pcap for given duration",
                    argsusage="[vm-name] [flags...]",
                    flags=[
                        cli.StringFlag(
                            name="output, o",
                            usage="file output for pcap",
                        ),
                        cli.DurationFlag(
                            name="duration, d",
                            usage="time spent capturing packets",
                            default=0,
                        ),
                    ],
                ),
            ],
        ),
        # cpillar command
        cli.Command(
            name="cpillar",
            usage="collect hashes of given file-path into given file",
            argsusage="[vm-name] [path]",
            flags=[
                cli.StringFlag(
                    name="output o",
                    usage="output file",
                ),
                cli.StringFlag(
                    name="alg, a",
                    usage="specify hash algorithm",
                    default="sha1",
                ),
                cli.IntFlag(
                    name="workers, w",
                    usage="specify number of workers",
                    default=5,
                ),
                cli.IntFlag(
                    name="chunk, c",
                    usage="specify read chunk size",
                    default=4096,
                ),
                cli.IntFlag(
                    name="maxsize, mfs",
                    usage="specify max file size to hash",
                    default=0,
                ),
                cli.DurationFlag(
                    name="time, t",
                    usage="specify max time spent on single hash",
                    default=0,
                ),
                cli.IntFlag(
                    name="drive, d",
                    usage="specify drive instance in case of multiple drives",
                )
            ],
            action=None,
        )
    ],
)


def _get_output(output):
    """
    retrieve output from StringIO
    """
    output.seek(0, 0)
    return '\n'.join(['  ' + l.rstrip() for l in output.readlines() if l != '\n'])


for name, test in tests.items():
    # set outputs
    out = StringIO()
    try:
        app.writer = out
        app.errwriter = out
        app.run([sys.executable]+test['cmd'].split())
        # check if test was supposed to fail
        if test['fail']:
            print('test succeeded unexpectedly: %r\nOutput:\n%s' % (name, _get_output(out)))
            break
        else:
            output = _get_output(out)
            if test['expect'] not in output:
                print('test: %r, missing expected normal output: %r\nOutput:\n%s' % (name, test['expect'], output))
                break
    except (Exception, BaseException):
        if not test['fail']:
            print('test failed unexpectedly: %r\nOutput:\n%s' % (name, _get_output(out)))
            break
        else:
            output = _get_output(out)
            if test['expect'] not in output:
                print('test: %r, missing expected failure output: %r\nOutput:\n%s' % (name, test['expect'], output))
                break

print('All Tests Verified! Working!')
