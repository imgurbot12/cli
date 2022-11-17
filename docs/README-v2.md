cli
---

I was tired of looking for a cli library powerful enough for what I needed along with
support for subcommands so instead I wrote my own taking inspiration from an 
[existing library](https://github.com/urfave/cli) in golang.

CLI is a simple, fast, and efficient library to control your command line application.

**NOTE: v2 of the api does not exlcude the use of v1. It's simply a convenient wrapper
around the same provided functionality. All objects act and operate the same way
as in v1 but with the added bonus of being able to use decorators to parse and supply
information conveniently and automatically.**

<!-- toc -->

- [Overview](#Overview)
- [Installation](#Installation)
- [Supported Platforms](#Supported-Platforms)
- [Getting Started](#Getting-Started)
- [Flags](#Flags)
- [Commands](#Commands)
- [Command Categories](#Command-Categories)
- [Exit Code](#Exit-Code)

<!-- tocstop -->

# Overview

Command line apps are usually so tiny that there is absolutely no reason why
your code should *not* be self-documenting. Things like generating help text and
parsing command flags/options should not hinder productivity when writing a
command line app.

**This is where cli comes into play.** cli makes command line programming easy,
organized, and expressive!

# Installation

Make sure you have a working python environment. Python 3.7+ is supported in the latest
version (v3). _If you need python 2 support you can use the tagged v1 version branch._

To install the library just run:
```bash
$ pip3 install git+https://github.com/imgurbot12/cli.git
```

# Support-Platforms

CLI is supported and tested on various versions of Python and Linux and MacOS.
Tests have yet to be done on windows but _should_ run without issue.

# Getting Started

Let's start with a simple "Hello World" application.

```python
import cli

@cli.app()
def hello_world(name: str = 'Stranger'):
  """
  Greet the World!

  :param name: name of person to greet
  """
  print(f'Hello {name}!')

hello_world.run()
```

Copy/Paste the code and try running the application for yourself:
```bash
$ python3 myapp.py      # runs app w/ no arguments
$ python3 myapp.py Dude # runs app w/ 'Dude' as `name` argument 
$ python3 myapp.py help # view a help page for the application
```

CLI generates a help command and unique help page for the application 
by default. This app already gives us a lot of power, with the option 
to include flags and subcommands which are covered below.

Here's what the help page should look like:
```bash
$ python3 myapp.py --help

NAME:
    hello_world - Greet the World!

USAGE:
    [arguments...] [flags...]

VERSION:
    0.0.1

COMMANDS:
    help, h - shows help for a command

GLOBAL OPTIONS:
    help, h - shows main help
```

Notice how the usage was actually parsed from the docstring
that was included in the function definition.

# Flags

Let's try and include some flags in the application as well:

```python
import cli

@cli.app()
def hello_world(name: str = 'Stranger', *, lang: str = 'english'):
  """
  Greet the World!

  :param name: name of person to greet
  :param lang: language to use in greeting
  """
  greeting = 'Hola' if lang == 'spanish' else 'Hello'
  print(f'{greeting} {name}!')

hello_world.run()
```

Any explicit **keyword only arguments** will be treated as flags for
the given application/command. The docstring parameter description
for the flag will also automatically be included in the flags related 
help page as well.

# Commands

Subcommands can also be defined for a more git-like interface.

```python
import cli

app = cli.App(
  name='Hello World!',
  usage='Greet the World!',
  version='0.0.1',
)

@app.command()
def hello(name: str = 'Stranger'):
  """
  Greet the World in English!

  :param name: name of person to greet
  """
  print(f'Hello {name}!')

@app.command()
def hola(name: str = 'extraño'):
  """
  Greet the World in Spanish!

  :param name: name of person to greet
  """
  print(f'Hola {name}!')

app.run()
```

# Command-Categories

For additional organization in apps that have many subcommands, you
can associate a category for each command to group them together in
the help output.

E.g.

```python
import cli

app = cli.App(
  name='Hello World!',
  usage='Greet the World!',
  version='0.0.1',
)

@app.command(category='Greeting')
def hello(name: str = 'Stranger'):
  """
  Greet the World in English!

  :param name: name of person to greet
  """
  print(f'Hello {name}!')

@app.command(category='Greeting')
def hola(name: str = 'extraño'):
  """
  Greet the World in Spanish!

  :param name: name of person to greet
  """
  print(f'Hola {name}!')

@app.command()
def foo(bar: str = 'bar'):
  """
  foobar
  """
  print(f'bar: {bar!r}')

app.run()
```

Will include:

```
COMMANDS:
    help, h - shows help for a command
    foo     - foobar

    Greeting:
        hello - Greet the World in English!
        hola  - Greet the World in Spanish!
```

# Exit-Code

Calling `app.run` will not automatically call `sys.exit`, which means that by
default the exit code will "fall through" to being `0`. An explicit code may
be set by returning a non-null error e.g.

```python
import cli

@cli.app()
def fail(ctx: cli.Context, *, fail: bool = False):
  if fail:
    ctx.exit_with_error('doing a fail!', 80)
  print('exited without a fail!')

fail.run()
```

# Async

CLI supports both async and non-async functions, even in combination.
You can similarly choose to run the entire app asynchronously or synchronously
independantly of the app's composition.

```python
import cli
import asyncio

@cli.app()
async def hello(ctx: cli.Context, name: str = 'World'):
  print(f'Hello {name}!', file=ctx.app.writer)

# run sync command functions alongside async ones
@hello.command
def foo():
  print('Foo!')

async def main():
  await hello.run(run_async=True)

# call app asynchronously
asyncio.run(main())

# or call entire app synchronously
hello.run(run_async=False)
```

