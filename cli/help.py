from __future__ import print_function
from .flags import BoolFlag
from .commands import Command
from jinja2 import Template

#** Variables **#
default_app_help = """NAME:
    {{name}}{%if usage%} - {{usage}}{%endif%}
    
USAGE:
    {%if visible_flags%}[global options]{%endif%}{%if commands%} command [command options]{%endif%} {%if argsusage%}{{argsusage}}{%else%}[arguments...]{%endif%}
    
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
        # iterate arguments until the last sub-cmd has been found
        argpath = ''
        subcommand = None
        commands = context.app.commands
        for arg in args:
            found = False
            for cmd in commands:
                if cmd.has_name(arg):
                    argpath += arg+'->'
                    commands, subcommand, found = cmd.subcommands, cmd, True
                    break
            # error on invalid command for help attempt
            if not found:
                context.app.not_found_error(context, argpath+arg)
        # show help page for last found sub-cmd
        return show_cmd_help(context, subcommand)
    show_app_help(context.app)


helpCommand = Command(
    name="help",
    aliases=["h"],
    usage="shows a list of commands or help for one command",
    argsusage="[command]",
    action=_helpCommandAction,
)

helpFlag = BoolFlag(name="help", usage="\tshows a list of commands")
helpFlag._builtin = True

#** Functions **#

def _get_app_args(app):
    """return dictionary of all required app variable and function returns"""
    allvars = vars(app).copy()
    allvars["visible_flags"] = [flag for flag in app.visible_flags() if not flag._builtin]
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


def show_app_help(app):
    """
    build main help page using app variables and given template in app
    """
    allvars = _get_app_args(app)
    if app.help_template is not None:
        template = Template(app.help_template)
    else: template = Template(default_app_help)
    # write output
    print(template.render(**allvars), file=app.writer)


def show_cmd_help(context, command):
    """
    build command help page using app/command variables and given template in app
    """
    # determine template object
    if context.app.cmd_help_template is not None:
        template = Template(context.app.cmd_help_template)
    else: template = Template(default_cmd_help)
    # if command is global-command, print base help
    if command.name == '':
        show_app_help(context.app)
        return
    # print command help after retrieving arguments
    allvars = _get_cmd_args(command)
    print(template.render(**allvars), file=context.app.writer)
