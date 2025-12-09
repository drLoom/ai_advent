"""CLI commands for article scraping and summarization."""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional
from pathlib import Path
from datetime import datetime
import logging

from ai.article_scraper import ArticleScraper, Article
from ai.summarization_client import SummarizationClient, ArticleSummary
from ai.summary_validator import SummaryValidator

app = typer.Typer(help="Article summarization commands")
console = Console()
logger = logging.getLogger(__name__)

# Output directory for summaries
SUMMARIES_DIR = Path("./summaries")
SUMMARIES_DIR.mkdir(exist_ok=True)


@app.command()
def summarize(
    url: str = typer.Option(
        "https://www.adexchanger.com/technology/",
        "--url",
        "-u",
        help="URL to scrape articles from"
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of articles to summarize"
    ),
    validate: bool = typer.Option(
        False,
        "--validate",
        help="Validate summaries with another LLM"
    ),
    threshold: float = typer.Option(
        0.7,
        "--threshold",
        "-t",
        help="Minimum validation score (0-1)"
    ),
    summary_length: int = typer.Option(
        200,
        "--length",
        "-l",
        help="Maximum summary length in words"
    ),
    summarization_model: str = typer.Option(
        "anthropic/claude-3.5-haiku",
        "--model",
        "-m",
        help="Model for summarization"
    ),
    validation_model: str = typer.Option(
        "openai/gpt-4o-mini",
        "--validation-model",
        help="Model for validation"
    ),
    save_output: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save summaries and meta-summary to file"
    ),
):
    """
    Scrape, summarize, and optionally validate articles from a URL.

    Example:
        uv run python main.py article summarize --limit 5 --validate --save
    """
    console.print(f"\n[bold cyan]Article Summarization Pipeline[/bold cyan]")
    console.print(f"URL: {url}")
    console.print(f"Limit: {limit} articles")
    console.print(f"Summarization Model: {summarization_model}")
    if validate:
        console.print(f"Validation Model: {validation_model}")
    console.print(f"Validation: {'Enabled' if validate else 'Disabled'}\n")

    # Step 1: Scrape articles
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        scrape_task = progress.add_task("Scraping articles...", total=None)

        try:
            scraper = ArticleScraper()
            if "adexchanger.com" in url:
                articles = scraper.scrape_adexchanger_technology(limit=limit)
            else:
                console.print(f"[yellow]Warning: Generic scraping may not work well for {url}[/yellow]")
                articles = []

            progress.update(scrape_task, completed=True)

            if not articles:
                console.print("[red]No articles found![/red]")
                return

            console.print(f"[green]✓ Scraped {len(articles)} articles[/green]\n")

        except Exception as e:
            console.print(f"[red]Error scraping articles: {e}[/red]")
            return

    # Step 2: Fetch full content and summarize
    summaries = []
    validation_results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        summarize_task = progress.add_task("Summarizing articles...", total=len(articles))

        summarization_client = SummarizationClient(model=summarization_model)
        validator = SummaryValidator(model=validation_model) if validate else None

        for i, article in enumerate(articles, 1):
            progress.update(
                summarize_task,
                description=f"Summarizing article {i}/{len(articles)}: {article.title[:40]}..."
            )

            try:
                # Fetch full content
                if article.url:
                    content = scraper.fetch_article_content(article.url)
                    if not content:
                        content = article.excerpt or article.title
                else:
                    content = article.excerpt or article.title

                # Summarize
                summary = summarization_client.summarize_article(
                    title=article.title,
                    content=content,
                    url=article.url or "",
                    max_length=summary_length
                )
                summaries.append(summary)

                # Validate if requested
                if validate and validator:
                    validation = validator.validate_summary(
                        original_content=content,
                        summary=summary.summary,
                        threshold=threshold
                    )
                    validation_results.append(validation)

            except Exception as e:
                logger.error(f"Error processing article {article.title}: {e}")
                console.print(f"[yellow]Skipped: {article.title[:60]}...[/yellow]")

            progress.update(summarize_task, advance=1)

    # Display results
    console.print(f"\n[bold green]✓ Completed {len(summaries)} summaries[/bold green]\n")

    for i, summary in enumerate(summaries, 1):
        # Create panel for each summary
        content_lines = [
            f"[bold]{summary.title}[/bold]",
            f"[dim]{summary.url}[/dim]",
            "",
            f"[cyan]Summary:[/cyan]",
            summary.summary,
            "",
        ]

        if summary.key_points:
            content_lines.append("[cyan]Key Points:[/cyan]")
            for point in summary.key_points:
                content_lines.append(f"  • {point}")
            content_lines.append("")

        if summary.topics:
            topics_str = ", ".join(summary.topics)
            content_lines.append(f"[cyan]Topics:[/cyan] {topics_str}")

        # Add validation results if available
        if validate and i <= len(validation_results):
            validation = validation_results[i - 1]
            content_lines.append("")
            content_lines.append("[cyan]Validation:[/cyan]")

            # Create scores table
            scores_table = Table(show_header=True, box=None, padding=(0, 1))
            scores_table.add_column("Criterion", style="cyan")
            scores_table.add_column("Score", justify="right")
            scores_table.add_column("Status", justify="center")

            for criterion, score in validation.scores.items():
                status = "✓" if score >= threshold else "✗"
                status_color = "green" if score >= threshold else "red"
                scores_table.add_row(
                    criterion.replace("_", " ").title(),
                    f"{score:.2f}",
                    f"[{status_color}]{status}[/{status_color}]"
                )

            # Overall
            overall_status = "PASS" if validation.passes_threshold else "FAIL"
            overall_color = "green" if validation.passes_threshold else "red"

            content_lines.append("")
            from rich.table import Table as RichTable
            from io import StringIO
            import sys

            # Capture table output
            temp_console = Console(file=StringIO(), force_terminal=True)
            temp_console.print(scores_table)
            table_str = temp_console.file.getvalue()

            content_lines.append(table_str)
            content_lines.append(f"Overall: [{overall_color}]{validation.overall_score:.2f} {overall_status}[/{overall_color}]")

            if validation.feedback:
                content_lines.append(f"\nFeedback: {validation.feedback}")

            if validation.issues:
                content_lines.append("\nIssues:")
                for issue in validation.issues:
                    content_lines.append(f"  • {issue}")

        panel = Panel(
            "\n".join(content_lines),
            title=f"Article {i}/{len(summaries)}",
            border_style="cyan" if not validate or validation_results[i-1].passes_threshold else "yellow"
        )
        console.print(panel)
        console.print()

    # Create and save meta-summary if requested
    if save_output and summaries:
        console.print("[bold cyan]Creating meta-summary...[/bold cyan]\n")

        try:
            meta_summary = summarization_client.create_meta_summary(
                summaries=summaries,
                max_length=500
            )

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"articles_summary_{timestamp}.txt"
            output_path = SUMMARIES_DIR / filename

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("ARTICLE SUMMARIES REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Source: {url}\n")
                f.write(f"Total Articles: {len(summaries)}\n")
                f.write(f"Summarization Model: {summarization_model}\n")
                if validate:
                    f.write(f"Validation Model: {validation_model}\n")
                f.write("=" * 80 + "\n\n")

                f.write("META-SUMMARY\n")
                f.write("-" * 80 + "\n")
                f.write(meta_summary + "\n\n")

                f.write("ARTICLES ANALYZED:\n")
                for i, summary in enumerate(summaries, 1):
                    f.write(f"{i}. {summary.title}\n")
                f.write("\n")
                f.write("=" * 80 + "\n\n")

                # Write individual summaries
                for i, summary in enumerate(summaries, 1):
                    f.write(f"ARTICLE {i}: {summary.title}\n")
                    f.write(f"URL: {summary.url}\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"{summary.summary}\n\n")

                    if summary.key_points:
                        f.write("Key Points:\n")
                        for point in summary.key_points:
                            f.write(f"  • {point}\n")
                        f.write("\n")

                    if summary.topics:
                        f.write(f"Topics: {', '.join(summary.topics)}\n")

                    # Add validation results if available
                    if validate and i <= len(validation_results):
                        validation = validation_results[i - 1]
                        status = "PASS" if validation.passes_threshold else "FAIL"
                        f.write(f"\nValidation: {validation.overall_score:.2f} {status}\n")

                    f.write("\n" + "=" * 80 + "\n\n")

            # Display meta-summary with article titles
            meta_content = f"[dim]Model: {summarization_model}[/dim]\n\n"
            meta_content += meta_summary + "\n\n[cyan]Articles Analyzed:[/cyan]\n"
            for i, summary in enumerate(summaries, 1):
                meta_content += f"{i}. {summary.title}\n"

            meta_panel = Panel(
                meta_content,
                title="Meta-Summary of All Articles",
                border_style="green",
                padding=(1, 2)
            )
            console.print(meta_panel)
            console.print()
            console.print(f"[green]✓ Saved summaries to: {output_path}[/green]\n")

        except Exception as e:
            console.print(f"[red]Error creating meta-summary: {e}[/red]")


@app.command()
def scrape(
    url: str = typer.Option(
        "https://www.adexchanger.com/technology/",
        "--url",
        "-u",
        help="URL to scrape"
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of articles to scrape"
    ),
):
    """
    Just scrape articles without summarizing.

    Example:
        uv run python main.py article scrape --limit 5
    """
    console.print(f"\n[bold cyan]Scraping Articles[/bold cyan]")
    console.print(f"URL: {url}\n")

    try:
        scraper = ArticleScraper()
        if "adexchanger.com" in url:
            articles = scraper.scrape_adexchanger_technology(limit=limit)
        else:
            console.print(f"[yellow]Generic scraping not yet implemented[/yellow]")
            return

        if not articles:
            console.print("[red]No articles found![/red]")
            return

        console.print(f"[green]Found {len(articles)} articles:[/green]\n")

        # Display as table
        table = Table(show_header=True)
        table.add_column("#", style="cyan", width=3)
        table.add_column("Title", style="white")
        table.add_column("Date", style="dim")

        for i, article in enumerate(articles, 1):
            table.add_row(
                str(i),
                article.title[:80] + "..." if len(article.title) > 80 else article.title,
                article.date or "N/A"
            )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
