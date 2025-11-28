#!/usr/bin/env python3
"""
CLI tool for AI-powered document processing and indexing.
"""

import typer
from cli.index_commands import app as index_app

app = typer.Typer(
    help="AI-powered document processing and indexing CLI", no_args_is_help=True
)

app.add_typer(index_app, name="index", help="Document indexing commands")


def main():
    app()


if __name__ == "__main__":
    main()
