#!/usr/bin/env python3
"""
CLI tool for AI-powered document processing and indexing.
"""

import typer
from cli.index_commands import app as index_app
from cli.image_commands import app as image_app
from cli.article_commands import app as article_app

app = typer.Typer(
    help="AI-powered document processing and indexing CLI", no_args_is_help=True
)

app.add_typer(index_app, name="index", help="Document indexing commands")
app.add_typer(image_app, name="image", help="Image generation commands")
app.add_typer(article_app, name="article", help="Article scraping and summarization commands")


def main():
    app()


if __name__ == "__main__":
    main()
