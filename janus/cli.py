from typing import Union

import typer

from janus import __app_name__, __version__, alert_configs_cli, db_users_cli
from janus.logging import logger, setDebugLogLevel

app = typer.Typer()

app = typer.Typer()
app.add_typer(alert_configs_cli.app, name="alert-configs")
app.add_typer(db_users_cli.app, name="db-users")


@app.command()
def version() -> None:
    """Print version information about the application"""
    _version_callback(True)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


def _debug_logging_callback(value: bool) -> None:
    if value:
        setDebugLogLevel()


@app.callback()
# @use_yaml_config(default_value="config.yaml")
def main(
    version: Union[bool, None] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logs",
        callback=_debug_logging_callback,
        is_eager=False,
        rich_help_panel="Customization and Utils",
    ),
):
    logger.debug("Starting janus ...")
    logger.debug("[DEBUG LOGGING ENABLED]")


### TOOD
### verify integrations - import failing due to missing webhook config
### Find way to avoid creating duplicates
