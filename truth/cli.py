"""Typer CLI entrypoint — single command: `truth "<question>"`."""
from __future__ import annotations

import asyncio

import typer
from dotenv import load_dotenv
from rich.console import Console

# Load .env from the project root before anything imports env-dependent modules.
load_dotenv()

from truth.debate import DEFAULT_CAP, run_debate  # noqa: E402


def main(
    question: str = typer.Argument(..., help="The question to debate."),
    cap: int = typer.Option(DEFAULT_CAP, "--cap", help="Hard cap on debate rounds."),
    no_web: bool = typer.Option(False, "--no-web", help="Disable web search (for testing)."),
) -> None:
    """Use AI to reach the capital-T Truth on any topic."""
    console = Console()
    debate_dir = asyncio.run(
        run_debate(question, cap=cap, allow_web=not no_web, console=console)
    )
    verdict = debate_dir / "VERDICT.md"
    console.print()
    console.rule("[bold]Final verdict")
    if verdict.exists():
        console.print(verdict.read_text())
    else:
        console.print("[bold red]No verdict was rendered.[/bold red]")
    console.print(f"\n[dim]Artifacts: {debate_dir}[/dim]")


def app() -> None:
    typer.run(main)


if __name__ == "__main__":
    app()
