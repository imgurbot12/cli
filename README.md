cli
===

[![forthebadge](https://forthebadge.com/images/badges/you-didnt-ask-for-this.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/built-with-love.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)

I was tired of searching for a decent alternative to argparse that was both
easy to use and allowed for sub-arguments with all the power I wanted. So
instead I re-built an [existing-library](https://github.com/urfave/cli) from [golang](https://golang.org/)
and wrote it in python with most of the same features. ENJOY!! - Imgurbot12

P.S. This library took HEAVY inspiration from golang's third party library:
https://github.com/urfave/cli including this README. Go give them some love <3.

cli is a simple, fast, and fun package for building command line apps in Go. The
goal is to enable developers to write fast and distributable command line
applications in an expressive way.

<!-- toc -->

- [Overview](#overview)
- [Installation](#installation)
  * [Supported platforms](#supported-platforms)
- [Getting Started](#getting-started)
- [Examples](#examples)
  * [Arguments](#arguments)
  * [Flags](#flags)
    + [Alternate Names](#alternate-names)
  * [Subcommands](#subcommands)
  * [Subcommands categories](#subcommands-categories)
  * [Exit code](#exit-code)
  * [Customization](#customization)

<!-- tocstop -->

## Overview

Command line apps are usually so tiny that there is absolutely no reason why
your code should *not* be self-documenting. Things like generating help text and
parsing command flags/options should not hinder productivity when writing a
command line app.

**This is where cli comes into play.** cli makes command line programming fun,
organized, and expressive!

## Installation

Make sure you have a working Python environment.  Python version 2.7.6+ is supported.  [See
the install instructions for Python](https://docs.python.org/3/using/index.html).

To install cli, simply run:
```
$ pip install git+https://github.com/imgurbot12/cli
```

### Supported platforms

cli is tested against multiple versions of Python on Linux, I have not yet
tested it on any other platforms.

## Getting Started

One of the philosophies behind cli is that an API should be playful and full of
discovery. So a cli app can be as little as one line of code in `main()`.

<!-- {
  "args": ["&#45;&#45;help"],
  "output": "A new cli application"
} -->
``` python
import cli
import sys

app = cli.App(
    name="App name goes here",
    usage="App usage goes here",
    version="1.0.0",
    flags=[],
    commands=[],
).run(sys.argv)
```

This app will run and show help text, but is not very useful. Let's give an
action to execute and some help documentation:

<!-- {
  "output": "boom! I say!"
} -->
``` python
import cli
import sys

def boom(context):
    print("boom! I say!")

app = cli.App(
    name="boom",
    usage="make an explosive entrance",
    version="1.0.0",
    flags=[],
    commands=[],
    action=boom,
).run(sys.argv)
```

Running this already gives you a ton of functionality, plus support for things
like subcommands and flags, which are covered below.

## Examples

Being a programmer can be a lonely job. Thankfully by the power of automation
that is not the case! Let's create a greeter app to fend off our demons of
loneliness!

Start by creating a file named `greet.py` with the following code in it:

<!-- {
  "output": "Hello friend!"
} -->
``` python
import cli
import sys

def hello(context):
    print("Hello friend!")

app = cli.App(
    name="greet",
    usage="fight the loneliness!",
    version="1.0.0",
    flags=[],
    commands=[],
    action=hello,
).run(sys.argv)
```

Finally run our new script:

```
$ python greet.py
Hello friend!
```

cli also generates neat help text:

```
NAME:
    greet - fight the loneliness!
    
USAGE:
    [global options] command [command options] [arguments...]
    
VERSION:
    1.0.0

COMMANDS:
      help, h	shows a list of commands or help for one command
      
GLOBAL OPTIONS:
    --help		shows a list of commands
    --version, -v	print the version
```

### Arguments

You can lookup arguments by calling the `args()` function on `context`, e.g.:

<!-- {
  "output": "Hello \""
} -->
``` python
import cli
import sys

def hello(context):
    print("Hello %r" % (context.args().get(0)))

app = cli.App(
    name="greet",
    usage="fight the loneliness!",
    version="1.0.0",
    flags=[],
    commands=[],
    action=hello,
).run(sys.argv)
```

### Flags

Setting and querying flags is simple.

<!-- {
  "output": "Hello Nefertiti"
} -->
``` python
import cli
import sys

def hello(context):
    name = "Nefertiti"
    if context.narg() > 0:
        name = context.args().get(0)
    if context.flag("lang") == "spanish":
        print("Hola "+name)
    else:
        print("Hello "+name)

app = cli.App(
    name="greet",
    usage="fight the loneliness!",
    version="1.0.0",
    flags=[
        cli.StringFlag(
            name="lang",
            default="english",
            usage="language for the greeting",
        ),
    ],
    commands=[],
    action=hello,
).run(sys.argv)
```

#### Alternate Names

You can set alternate (or short) names for flags by providing a comma-delimited
list for the `Name`. e.g.

<!-- {
  "args": ["&#45;&#45;help"],
  "output": "&#45;&#45;lang value, &#45;l value.*language for the greeting.*default: \"english\""
} -->
``` python
import cli
import sys

app = cli.App(
    name="greet",
    usage="fight the loneliness!",
    version="1.0.0",
    flags=[
        cli.StringFlag(
            name="lang, l",
            default="english",
            usage="language for the greeting",
        ),
    ],
    commands=[],
).run(sys.argv)
```

That flag can then be set with `--lang spanish` or `-l spanish`. Note that
giving two different forms of the same flag in the same command invocation is an
error.

### Subcommands

Subcommands can be defined for a more git-like command line app.

<!-- {
  "args": ["template", "new"],
  "output": "new task template: .+"
} -->
``` python
import cli
import sys

def add(context):
    print("added task: "+context.args().first())

def complete(context):
    print("completed task: "+context.args().first())

def new_template(context):
    print("new task template: "+context.args().first())

def remove_template(context):
    print("removed task template: "+context.args().first())

app = cli.App(
    name="greet",
    usage="fight the loneliness!",
    version="1.0.0",
    flags=[],
    commands=[
        cli.Command(
            name="add",
            aliases=["a"],
            usage="add a task to the list",
            action=add,
        ),
        cli.Command(
            name="complete",
            aliases=["c"],
            usage="complete a task on the list",
            action=complete,
        ),
        cli.Command(
            name="template",
            aliases=["t"],
            usage="options for task templates",
            subcommands=[
                cli.Command(
                    name="new",
                    usage="add a new template",
                    action=new_template,
                ),
                cli.Command(
                    name="remove",
                    usage="remove an existing template",
                    action=remove_template,
                ),
            ],
        )
    ],
).run(sys.argv)
```

### Subcommands categories

For additional organization in apps that have many subcommands, you can
associate a category for each command to group them together in the help
output.

E.g.

``` python
import cli
import sys

app = cli.App(
    name="greet",
    usage="fight the loneliness!",
    version="1.0.0",
    flags=[],
    commands=[
        cli.Command(name="noop"),
        cli.Command(name="add", category="Template actions"),
        cli.Command(name="remove", category="Template actions")
    ],
).run(sys.argv)
```

Will include:

```
COMMANDS:
      help, h	shows a list of commands or help for one command
      noop	

    Template actions:
      add	
      remove
```

### Exit code

Calling `app.run` will not automatically call `sys.exit`, which means that by
default the exit code will "fall through" to being `0`.  An explicit exit code
may be set by returning a non-null error e.g.:

``` python
import cli
import sys

def do_exit(context):
    if context.flag("ginger-crouton"):
        context.app.exit_with_error("it is not in the soup", 80)

app = cli.App(
    name="greet",
    usage="fight the loneliness!",
    version="1.0.0",
    flags=[
        cli.BoolFlag(
            name="ginger-crouton",
            usage="is it in the goup?",
        )
    ],
    commands=[],
    action=do_exit,
).run(sys.argv)
```

#### Customization

All of the help text generation may be customized, and at multiple levels.  The
templates are exposed as app variables `app.help_template`, and
`app.cmd_help_template` which may be reassigned or augmented, and full override
is possible by assigning a compatible [jinja2](http://jinja.pocoo.org/) template,
e.g.:

<!-- {
  "output": "Ha HA.  I pwnd the help!!1"
} -->
``` python
import cli
import sys

# EXAMPLE: Append to an existing template
new_template = cli.default_app_help + """
WEBSITE: http://awesometown.example.com

SUPPORT: support@awesometown.example.com

"""

# EXAMPLE: Override a template
"""NAME:
    {{name}} - {{usage}}

USAGE:
    {%if visible_flags%}[global options]{%endif%}{%if commands%} command [command options]{%endif%} {%if argsusage%}{{argsusage}}{%else%}[arguments...]{%endif%}
    {%if authors%}
AUTHOR:
    {%for author in authors%}{{author}}{%endfor%}
    {%endif%}{%if commands%}
COMMANDS:
    {%for flag in visible_flags%}{{flag}}
    {%endfor%}{%endif%}{%if copyright%}
COPYRIGHT:
    {{copyright}}
    {%endif%}{%if version%}
VERSION:
    {{version}}
    {%endif%}
"""

app = cli.App(
    name="greet",
    usage="fight the loneliness!",
    version="1.0.0",
    help_template=new_template,
    flags=[
        cli.BoolFlag(
            name="ginger-crouton",
            usage="is it in the goup?",
        )
    ],
    commands=[],
).run(sys.argv)
```


