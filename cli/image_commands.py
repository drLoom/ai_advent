"""CLI commands for image generation."""
import typer
import re
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from typing import Optional

from ai.image_client import ImageClient
from models.models import IMAGE_MODEL, IMAGE_DEFAULT_SIZE, IMAGE_DEFAULT_QUALITY

app = typer.Typer(help="Image generation commands")
console = Console()

# Default directory for saved images
IMAGES_DIR = Path("images")


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Text description of the image to generate"),
    model: str = typer.Option(
        IMAGE_MODEL,
        "--model",
        "-m",
        help="Image generation model to use"
    ),
    size: str = typer.Option(
        IMAGE_DEFAULT_SIZE,
        "--size",
        "-s",
        help="Image size (e.g., '1024x1024', '512x512')"
    ),
    quality: str = typer.Option(
        IMAGE_DEFAULT_QUALITY,
        "--quality",
        "-q",
        help="Image quality/detail level or number of steps"
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        help="Random seed for reproducibility"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path to save the image"
    ),
    no_log: bool = typer.Option(
        False,
        "--no-log",
        help="Disable request logging"
    )
):
    """
    Generate an image from a text prompt using AI.

    Examples:

        # Basic usage (auto-saves to ./images)
        uv run python main.py image generate "a beautiful sunset over mountains"

        # Specify size and quality
        uv run python main.py image generate "cyberpunk city" --size 512x512 --quality high

        # Use seed for reproducibility
        uv run python main.py image generate "cat in space" --seed 42

        # Save to custom location
        uv run python main.py image generate "abstract art" --output output.png
    """
    try:
        # Auto-generate output path if not specified
        if output is None:
            # Create images directory if it doesn't exist
            IMAGES_DIR.mkdir(exist_ok=True)

            # Generate filename from timestamp and sanitized prompt
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = re.sub(r'[^\w\s-]', '', prompt)[:50].strip().replace(' ', '_')
            output = str(IMAGES_DIR / f"{timestamp}_{safe_prompt}.png")

        # Initialize client
        client = ImageClient(log_requests=not no_log)

        # Display request info
        console.print("\n[bold cyan]Image Generation Request[/bold cyan]")
        console.print(f"Model: [yellow]{model}[/yellow]")
        console.print(f"Prompt: [green]{prompt}[/green]")
        console.print(f"Size: [yellow]{size}[/yellow]")
        console.print(f"Quality: [yellow]{quality}[/yellow]")
        if seed is not None:
            console.print(f"Seed: [yellow]{seed}[/yellow]")
        console.print(f"Output: [cyan]{output}[/cyan]")
        console.print()

        # Generate image with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating image...", total=None)

            response = client.generate_image(
                prompt=prompt,
                model=model,
                size=size,
                quality=quality,
                seed=seed,
                save_to=output
            )

            progress.update(task, completed=True)

        # Display results
        console.print("\n[bold green]✓ Image Generated Successfully![/bold green]\n")

        # Create results table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Image URL", response.image_url)
        table.add_row("Latency", f"{response.latency_ms:.2f} ms")
        if response.cost_estimate:
            table.add_row("Cost Estimate", f"${response.cost_estimate:.4f}")
        if output:
            table.add_row("Saved To", output)

        console.print(table)
        console.print()

        # Show URL for easy access
        console.print(f"[dim]View your image at:[/dim]")
        console.print(f"[link={response.image_url}]{response.image_url}[/link]\n")

        # Remind about logging
        if not no_log:
            console.print(
                "[dim]Request logged to: image_generation.log[/dim]\n"
            )

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def logs(
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Number of recent logs to show"
    ),
    log_file: str = typer.Option(
        "image_generation.log",
        "--file",
        "-f",
        help="Log file to read"
    )
):
    """
    Display recent image generation logs.

    Examples:

        # Show last 10 logs
        uv run python main.py image logs

        # Show last 20 logs
        uv run python main.py image logs --limit 20
    """
    try:
        log_path = Path(log_file)

        if not log_path.exists():
            console.print(
                f"[yellow]No log file found at: {log_file}[/yellow]"
            )
            console.print(
                "[dim]Generate some images first to create logs.[/dim]"
            )
            return

        # Read log file
        with open(log_path, 'r') as f:
            lines = f.readlines()

        if not lines:
            console.print("[yellow]Log file is empty[/yellow]")
            return

        # Get last N lines
        recent_lines = lines[-limit:] if len(lines) > limit else lines

        console.print(f"\n[bold cyan]Recent Image Generation Logs[/bold cyan]")
        console.print(f"[dim]Showing last {len(recent_lines)} of {len(lines)} total logs[/dim]\n")

        # Display logs
        for line in recent_lines:
            # Parse and format log line
            if " - " in line:
                parts = line.strip().split(" - ", 3)
                if len(parts) >= 4:
                    timestamp = parts[0]
                    level = parts[2]
                    message = parts[3]

                    level_color = {
                        "INFO": "green",
                        "WARNING": "yellow",
                        "ERROR": "red"
                    }.get(level, "white")

                    console.print(
                        f"[dim]{timestamp}[/dim] [{level_color}]{level}[/{level_color}] {message}"
                    )
            else:
                console.print(line.strip())

        console.print()

    except Exception as e:
        console.print(f"[red]Error reading logs: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def info():
    """
    Display information about image generation configuration.
    """
    console.print("\n[bold cyan]Image Generation Configuration[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Default Model", IMAGE_MODEL)
    table.add_row("Default Size", IMAGE_DEFAULT_SIZE)
    table.add_row("Default Quality", IMAGE_DEFAULT_QUALITY)
    table.add_row("Images Directory", str(IMAGES_DIR))
    table.add_row("Log File", "image_generation.log")

    console.print(table)
    console.print()

    console.print("[bold]Available Parameters:[/bold]")
    console.print("  • [cyan]prompt[/cyan]: Text description of the image")
    console.print("  • [cyan]model[/cyan]: Model to use (default: google/gemini-2.5-flash-image-preview)")
    console.print("  • [cyan]size[/cyan]: Image dimensions (e.g., 1024x1024, 512x512)")
    console.print("  • [cyan]quality[/cyan]: Quality level or steps (e.g., 'standard', 'high', or number like '20')")
    console.print("  • [cyan]seed[/cyan]: Random seed for reproducible results")
    console.print("  • [cyan]output[/cyan]: Custom output path (default: auto-generated in ./images)")
    console.print()

    console.print("[dim]Images are automatically saved to ./images directory with timestamped filenames.[/dim]")
    console.print("[dim]Use --output to specify a custom save location.[/dim]")
    console.print()


if __name__ == "__main__":
    app()
