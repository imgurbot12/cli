from __future__ import print_function
from .flags import BoolFlag
from .commands import Command
from jinja2 import Template

#** Variables **#
default_app_help = """NAME:
    {{name}}{%if usage%} - {{usage}}{%endif%}
    
USAGE:
    {%if visible_flags%}[global options]{%endif%}{%if commands%} command [command options]{%endif%} {%if argsusage%}{{argsusage}}{%endif%}[arguments...]
    
VERSION:
    {{version}}{%if description%}
    
DESCRIPTION:
    {{description}}{%endif%}{%if authors%}
    
AUTHOR{%if authors|length > 1%}S{%endif%}:{% for author in authors %}
    {{author}}{%endfor%}{%endif%}{%if visible_commands%}

COMMANDS:{%for category in visible_categories%}{%if category and category != "none"%}

    {{category}}:{%endif%}{% for cmd in visible_commands%}{%if cmd.category == category%}
      {{", ".join(cmd.names())}}{{"\t"}}{{cmd.usage}}{%endif%}{%endfor%}{%endfor%}{%endif%}{%if visible_flags%}
      
GLOBAL OPTIONS:{%for flag in visible_flags%}
    {{flag}}{{"\t"}}{{flag.usage}}{%endfor%}{%endif%}{%if copyright%}
    
COPYRIGHT:
    {{copyright}}{%endif%}          
"""

default_cmd_help = """NAME:
    {{name}} - {%if description%}{{description}}{%else%}{{usage}}{%endif%}

USAGE:
    {{name}} command{%if visible_flags%} [command options]{%endif%} {%if argsusage%}{{argsusage}}{%else%}[arguments...]{%endif%}

{%if is_command%}SUB{%endif%}COMMANDS:{%for category in visible_categories%}{%if category.name%}
    {{category.name}}:{%endif%}{%for cmd in visible_commands%}
      {{", ".join(cmd.names())}}{{"\t"}}{{cmd.usage}}{%endfor%}{%endfor%}{%if visible_flags%}

OPTIONS:{%for flag in visible_flags%}
    {{flag}}{{"\t"}}{{flag.usage}}{%endfor%}{%endif%}
"""
"""
"""

def _helpCommandAction(context):
    """action for helpCommand object"""
    args = context.args()
    if args.present():
        return show_cmd_help(context, args.first())
    show_app_help(context)

helpCommand = Command(
    name="help",
    aliases=["h"],
    usage="shows a list of commands or help for one command",
    argsusage="[command]",
    action=_helpCommandAction,
)

helpFlag = BoolFlag(name="help", usage="\tshows a list of commands")

#** Functions **#

def _get_app_args(app):
    """return dictionary of all required app variable and function returns"""
    allvars = vars(app).copy()
    allvars["visible_flags"] = app.visible_flags()
    allvars["visible_commands"] = app.visible_commands()
    allvars["visible_categories"] = app.visible_categories()
    return allvars

def _get_cmd_args(command):
    """return dictionary of all required command variable and function returns"""
    allvars = vars(command).copy()
    allvars["visible_flags"] = command.visible_flags()
    allvars["visible_commands"] = command.visible_commands()
    if isinstance(command, Command):
        allvars["is_command"] = True
        allvars["visible_categories"] = [""]
    else:
        allvars["is_command"] = False
        allvars["visible_categories"] = command.visible_categories()
    return allvars

def show_app_help(context):
    """
    build main help page using app variables and given template in app
    """
    allvars = _get_app_args(context.app)
    if context.app.help_template is not None:
        template = Template(context.app.help_template)
    else: template = Template(default_app_help)
    # write output
    print(template.render(**allvars), file=context.app.writer)

def show_cmd_help(context, command_str):
    """
    build command help page using app/command variables and given template in app
    """
    # determine template object
    if context.app.cmd_help_template is not None:
        template = Template(context.app.cmd_help_template)
    else: template = Template(default_cmd_help)
    # print default if command-str is empty
    if command_str == "":
        allvars = _get_app_args(context.app)
        print(template.render(**allvars), file=context.app.writer)
        return
    # iterate app-commands to find command-name
    for cmd in context.app.commands:
        if cmd.has_name(command_str):
            allvars = _get_cmd_args(cmd)
            print(template.render(**allvars), file=context.app.writer)
            return
    # run error if no command available
    context.app.not_found_error(context, command_str)

#TODO: need command's default action to be help page without getting in the way of sub-commands if they exist
#TODO: need help to be available for recusrsive sub-commands, (commands past first set of sub-commands)
