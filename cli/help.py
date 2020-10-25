"""
all functions and definitons used to render help page
"""
from typing import Any, List, Optional

from jinja2 import Environment

from .flag import BoolFlag
from .context import Context
from .command import CommandBase, Command

#** Variables **#
__all__ = [
    'help_action',

    'help_flag',
    'help_command',
]

help_app_template = """
NAME:
    {{name}}{%if usage%} - {{usage}}{%endif%}

USAGE:
    {% if visible_flags %}[global flags]{% endif %}
    {%- if commands %} command [command flags]{% endif %}
    {%- if argsusage %} {{ argsusage }}{% else %} [arguments...]{% endif %}

VERSION:
    {{ version }}

{%- if description %}

DESCRIPTION:
    {{description}}
{%- endif %}

{%- if authors %}

AUTHOR{%if authors|length > 1%}S{%endif%}:
{%- for author in authors %}
    {{ author }}
{%- endfor %}
{%- endif %}

{%- if visible_commands %}

COMMANDS:
    {%-for category in visible_categories%}
        {%- set cbuffer = calc_buffer(visible_commands, category) %}
        {%- set active_category = category and category != "*" %}
        {%- if active_category %}

    {{ category }}:
        {%- endif %}
        {%- for cmd in visible_commands %}
            {%- if cmd.category == category %}
    {% if active_category %}    {% endif -%}
    {{ cmd.to_string()|buffer(cbuffer) }} - {{ cmd.usage }}
            {%- endif %}
        {%- endfor %}
    {%- endfor %}
{%- endif %}

{%- if visible_flags %}

GLOBAL OPTIONS:
{%- set fbuffer = calc_buffer(visible_flags) %}
{%- for flag in visible_flags %}
    {{ flag.to_string()|buffer(fbuffer) }} - {{ flag.usage }}
{%- endfor %}
{%- endif %}

{%- if copyright %}

COPYRIGHT:
    {{ copyright }}
{% endif %}
"""

help_cmd_template = """
NAME:
    {{name}}{%if usage%} - {{usage}}{%endif%}

{%- if visible_commands %}

COMMANDS:
    {%-for category in visible_categories%}
        {%- set cbuffer = calc_buffer(visible_commands, category) %}
        {%- set active_category = category and category != "*" %}
        {%- if active_category %}

    {{ category }}:
        {%- endif %}
        {%- for cmd in visible_commands %}
            {%- if cmd.category == category %}
    {% if active_category %}    {% endif -%}
    {{ cmd.to_string()|buffer(cbuffer) }} - {{ cmd.usage }}
            {%- endif %}
        {%- endfor %}
    {%- endfor %}
{%- endif %}

{%- if visible_flags %}

GLOBAL OPTIONS:
{%- set fbuffer = calc_buffer(visible_flags) %}
{%- for flag in visible_flags %}
    {{ flag.to_string()|buffer(fbuffer) }} - {{ flag.usage }}
{%- endfor %}
{%- endif %}
"""

#: jinja2 template environment object
env = Environment()

#** Functions **#

def jinja_buffer(value: Any, buffer: int) -> str:
    """add buffer to end of string based on length of value"""
    return value + ' '*(buffer-len(value))

def jinja_calc_buffer(fields: List[Any], category: Optional[str] = None) -> int:
    """calculate buffer for list of fields based on their length"""
    if category:
        fields = [f for f in fields if f.category == category]
    return max(len(f.to_string()) for f in fields)

def get_vars(cmd: CommandBase) -> dict:
    """collect variables to use for template generation"""
    kwargs = vars(cmd).copy()
    kwargs.update({
        'visible_flags':      cmd.visible_flags(),
        'visible_commands':   cmd.visible_commands(),
        'visible_categories': cmd.visible_categories(),
    })
    return kwargs

def help_action(ctx: Context, cmd: Optional[Command] = None):
    """action used to render help content"""
    # recurse arguments to find sub-command
    command = cmd or ctx.app
    if ctx.args.present():
        path = 'app'
        for arg in ctx.args:
            for cmd in command.commands:
                if cmd.has_name(arg):
                    path   += '->' + cmd.name
                    command = cmd
                    break
            else:
                ctx.app.not_found_error(ctx, command, path)
    # set template based on given command
    template = ctx.app.help_app_template or help_app_template
    if command != ctx.app:
        template = ctx.app.help_cmd_template or help_cmd_template
    # get arguments from command and render template
    kwargs    = get_vars(command)
    jtemplate = env.from_string(template.strip())
    print(jtemplate.render(**kwargs), file=ctx.app.writer)

#** Init **#
env.filters['buffer'] = jinja_buffer
env.globals['calc_buffer'] = jinja_calc_buffer

#: primary flag to open app help-page
help_flag = BoolFlag(name='help, h', usage='shows main help')

#: primary command to open specified command help-page
help_command = Command(
    name='help',
    aliases=['h'],
    usage='shows help for a command',
    argsusage='[commands...]',
    action=help_action
)
