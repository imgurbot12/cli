## cli

[![forthebadge](https://forthebadge.com/images/badges/you-didnt-ask-for-this.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/built-with-love.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)

A highly configurable, dynamic, fast, and easy solution to managing
a command-line application. The goal is to make cli development as simple
and effective as possible for any configuration enabling the developer to
focus on function over form.

Supports Python >= 3.8 and can run asynchronously or synchronously.

This library took inspiration from [urfave/cli](https://github.com/urfave/cli)
and [pallets/click](https://github.com/pallets/click).

### Install

```bash
$ pip install cli3
```

### Examples

#### Derivative vs declarative.

Derivative implementation.

```python
import cli
from typing import List, Optional

#NOTE: Arguments and options are separated by `*`
# Anything that is a positional parameter is treated as an argument.
# Anything that is key-word only is treated as an option.
@cli.command
def example(
  echo: List[str], *,
  test: Optional[int]  = None,
  bool: Optional[bool] = None,
):
  """
  this is an example

  :param echo: arguments to echo to output
  """
  cli.echo('example!', echo)

example()
```

Declarative implementation.

```python
import cli
from typing import List

#NOTE: arguments and flags will get passed if the param is present.
def action(echo: List[str]):
  cli.echo('example!', echo)

command = cli.Command(
  name='example',
  about='this is an example',
  version='0.0.1',
  args=[cli.Arg('echo', about='arguments to echo to output', repeat=True)],
  flags=[cli.Flag[int]('test'), cli.Flag[bool]('bool')],
  action=action,
)

command.run()
```

#### Command groups and extras.

Derivative implementation(s).

```python
import cli
from typing import Annotated, List

#NOTE: groups dont define their own args/options.
# They are intended to just be semantic helpers for actual commands.
# If you want functional commands within commands just use `@cli.command`.
@cli.group
def group(ctx: cli.Context):
  #NOTE: pass extra values to children commands!
  # They can be retrieved later in a variety of ways
  ctx.extra['extra_arg'] = 'value!'

#NOTE: command1/command2/command3 are identical in function

#NOTE: denote an argument as extra via a decorator
@group.command
@cli.extra('extra_arg')
def command1(args: List[int], extra_arg: str):
  cli.echo('command1', args, extra_arg)

#NOTE: use annotated type defintions to denote an extra
@group.command
def command2(args: List[int], extra_arg: Annotated[str, cli.Extra()]):
  cli.echo('command2', args, extra_arg)

#NOTE: or retrieve the extra directly from the context object.
# cli.Context will get passed if a param with the type-annotation is present.
@group.command
def command3(ctx: cli.Context, args: List[int]):
  extra_arg = ctx.get_extra('extra_arg', str)
  cli.echo('command3', args, extra_arg)

group()
```

Declarative implementation.

```python
import cli
from typing import List

def groupc(ctx: cli.Context):
    ctx.extra['extra_arg'] = 'value!'

#NOTE: arguments do not need to be marked or divided by arg/kwarg here.
# They are already defined declaratively within command definition.
# Everything is just passed according to name if present. (except for Context)
def command1(args: List[int], extra_arg: str):
    cli.echo('command1', args, extra_arg)

def command2(ctx: cli.Context, args: List[int]):
    extra_arg = ctx.get_extra('extra_arg', str)
    cli.echo('command2', args, extra_arg)

def command3(ctx: cli.Context, extra_arg: str):
    args = ctx.get_arg('args', List[int])
    cli.echo('command3', args, extra_arg)

group = cli.Command(
    name='group',
    action=groupc,
    commands=[
        cli.Command(
            name='command1',
            args=[cli.Arg[int]('args', repeat=True)],
            action=command1,
        ),
        cli.Command(
            name='command2',
            args=[cli.Arg[int]('args', repeat=True)],
            action=command2,
        ),
        cli.Command(
            name='command3',
            args=[cli.Arg[int]('args', repeat=True)],
            action=command3,
        ),
    ]
)

group()
```

#### Async support.

```python
import cli
import asyncio

#NOTE: commands support sync/async functions interchangably.
# You can call the cli asyncly with the `run_async()` function as well.

@cli.group
async def group():
    cli.echo('group called!')

@group.command('foo-command')
async def foo():
    cli.echo('foo called!')

@group.command('bar-command', about='this is a sync function')
def bar():
    cli.echo('bar called!')

run_async = False
if run_async:
    asyncio.run(group.run_async())
else:
    group()
```
