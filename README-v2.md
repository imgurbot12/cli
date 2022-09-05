cli
---

[![forthebadge](https://forthebadge.com/images/badges/you-didnt-ask-for-this.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/built-with-love.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)

I was tired of lookin for a cli library powerful enough for what I needed along with
support for subcommands so instead I wrote my own taking inspiration from an 
[existing library](https://github.com/urfave/cli) in golang.

CLI is a simple, fast, and efficient library to control your command line application.

<!-- toc -->

- [Overview](#Overview)

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

# Support Platforms

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

Subcommands can also be defined for a more git-line interface.

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



