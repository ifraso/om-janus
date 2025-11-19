"""OM Janus entry point script."""
# janus/__main__.py

from janus import __app_name__, cli


def main():
    cli.app(prog_name=__app_name__)


if __name__ == "__main__":
    main()
