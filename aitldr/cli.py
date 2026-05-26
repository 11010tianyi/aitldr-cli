"""
Command-line interface for aitldr.
"""

import sys
import click
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text

from . import __version__
from .config import Config, load_config, get_config_dir
from .core import (
    lookup_page,
    lookup_command,
    is_natural_language,
    is_destructive_command,
    refresh_page,
    PageSource,
)
from .cache import save_rating

console = Console()


@click.group()
@click.version_option(version=__version__)
def cli():
    """AI-native TLDR CLI with AI fallback for missing pages."""
    pass


@cli.command()
@click.argument("query", required=False)
@click.option("--explain", "-e", is_flag=True, help="Explain the command")
@click.option("--refresh", "-r", is_flag=True, help="Refresh AI-generated page")
@click.option("--offline", "-o", is_flag=True, help="Offline mode, no AI generation")
@click.option("--model", "-m", help="Specify AI model provider")
def show(query: str, explain: bool, refresh: bool, offline: bool, model: str):
    """
    Show TLDR page for a command or natural language query.

    Examples:
        aitldr tar
        aitldr "删除7天前的日志"
        aitldr --explain "删除7天前的日志"
    """
    config = load_config()

    # Override model if specified
    if model:
        config.model.provider = model

    # Use config default for explain if not specified
    if not explain:
        explain = config.general.explain_default

    if not query:
        console.print("[red]Error: No query provided.[/red]")
        console.print("Usage: aitldr <command> or \"<natural language query>\"")
        sys.exit(1)

    # Check if natural language or command
    if is_natural_language(query):
        # Generate command from natural language
        command, explanation = lookup_command(query, config, explain)

        if not command:
            console.print("[red]Error: Could not generate command.[/red]")
            console.print("Make sure your API key is configured.")
            sys.exit(1)

        # Display command
        console.print("\n[bold cyan]Command:[/bold cyan]")
        syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)
        console.print(syntax)

        # Display explanation if requested or available
        if explanation:
            console.print(Panel(explanation, title="[bold]Explanation[/bold]", border_style="cyan"))

        # Check for destructive commands
        if is_destructive_command(command):
            console.print("\n[yellow on black]WARNING: Destructive command![/yellow on black]")
            console.print("[yellow]This operation may cause irreversible data loss.[/yellow]")

    else:
        # Look up TLDR page
        if refresh:
            console.print(f"Refreshing AI page for '{query}'...")
            success = refresh_page(query, config)
            if success:
                console.print("[green]Page refreshed successfully![/green]")
            else:
                console.print("[red]Failed to refresh page.[/red]")
                sys.exit(1)

        content, source = lookup_page(query, config, offline)

        if not content:
            console.print(f"[red]No TLDR page found for '{query}'.[/red]")
            if offline:
                console.print("[yellow]Use --offline to disable AI generation.[/yellow]")
            sys.exit(1)

        # Display content
        if source.source == "ai_cache":
            console.print("[dim][AI Generated Page (cached)][/dim]\n")
        elif source.source == "ai_generated":
            console.print("[dim][AI Generated Page][/dim]\n")

        # Parse and display markdown
        console.print(content)

        # Add AI disclaimer
        if source.source in ("ai_cache", "ai_generated"):
            console.print("\n[dim]AI-generated pages may contain inaccuracies. Verify before use.[/dim]")


@cli.command()
@click.argument("command")
@click.argument("direction", type=click.Choice(["up", "down"]))
def rate(command: str, direction: str):
    """Rate an AI-generated page."""
    rating = 1 if direction == "up" else -1
    save_rating(command, rating)
    console.print(f"[green]Rated '{command}' {direction}. Thanks for your feedback![/green]")


@cli.command()
@click.argument("command")
def submit(command: str):
    """Submit an AI-generated page to the official tldr-pages repository."""
    config = load_config()

    from .cache import get_ai_page

    content = get_ai_page(command)

    if not content:
        console.print(f"[red]No AI-generated page found for '{command}'.[/red]")
        sys.exit(1)

    console.print(Panel(
        f"""AI-generated pages should be manually reviewed before submission.

To submit '{command}' to tldr-pages:
1. Review the page at {config.get_config_dir()}/ai/{command}.md
2. Edit if needed
3. Remove the AI metadata header
4. Create a PR at https://github.com/tldr-pages/tldr""",
        title="[bold]Submission Guide[/bold]",
        border_style="yellow"
    ))


@cli.command()
def init():
    """Initialize aitldr configuration."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    from .config import save_config, Config

    save_config(Config())

    console.print(f"[green]Configuration initialized at {config_dir}[/green]")
    console.print("\nEdit config.toml to set your API keys and preferences.")


@cli.command()
def status():
    """Show current configuration status."""
    config = load_config()

    console.print(Panel(
        f"""[bold]aitldr Configuration[/bold]

General:
  Explain default: {config.general.explain_default}
  Cache enabled: {config.general.cache_enabled}

Model:
  Provider: {config.model.provider}
  Model: {config.model.model}

OpenAI:
  API Key: {'*' * 20 if config.openai.api_key else '[red]Not configured[/red]'}

DeepSeek:
  API Key: {'*' * 20 if config.deepseek.api_key else '[red]Not configured[/red]'}

Ollama:
  Endpoint: {config.ollama.endpoint}
  Model: {config.ollama.model}

Config directory: {get_config_dir()}""",
        title="[bold]Status[/bold]",
        border_style="cyan"
    ))


def main():
    """Main entry point."""
    cli()