import typer
from click.core import ParameterSource
from click.types import BOOL
from rich.prompt import Prompt


def confirm_option_callback(ctx: typer.Context, param: typer.CallbackParam, value):
    # Only prompt if the value came from DEFAULT_MAP (config file) AND it's not a required value
    # If value comes from config file, we should use it without prompting
    source = ctx.get_parameter_source(param.name)

    # Don't prompt if value comes from command line, environment, or if prompt attribute is None
    if source == ParameterSource.COMMANDLINE or source == ParameterSource.ENVIRONMENT:
        return value

    # If from config file (DEFAULT_MAP), only prompt if user wants to confirm
    # But since we want to avoid prompting when using --config, just return the value
    if source == ParameterSource.DEFAULT_MAP:
        return value

    # For prompt source (interactive mode), ask for confirmation
    if source == ParameterSource.PROMPT:
        if param.prompt and value:
            promt_text = f"{param.prompt} \\[{value}]"  # required format i.e. only [ has to be escaped
            confirmed = Prompt.ask(promt_text)
            if confirmed == "":
                return value
            else:
                if param.type.name == BOOL.name and isinstance(confirmed, str):
                    # TODO improve this to error out on invalid input
                    return confirmed == "True"
                else:
                    return confirmed

    return value
