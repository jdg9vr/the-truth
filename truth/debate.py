"""Debate orchestrator: sets up the directory, runs rounds, detects termination."""
from __future__ import annotations

import asyncio
import re
from datetime import date
from pathlib import Path

from rich.console import Console

from truth.agents import run_advocate, run_judge

TRANSCRIPTS_ROOT = Path.cwd() / "transcripts"
DEFAULT_CAP = 20


def _slugify(question: str, max_len: int = 60) -> str:
    s = question.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len] or "debate"


def _make_debate_dir(question: str) -> Path:
    slug = _slugify(question)
    today = date.today().isoformat()
    base = TRANSCRIPTS_ROOT / f"{today}_{slug}"
    # If the dir already exists (e.g., same question run twice today), suffix it.
    candidate = base
    n = 2
    while candidate.exists():
        candidate = Path(f"{base}-{n}")
        n += 1
    candidate.mkdir(parents=True)
    return candidate


def _merge_openings(debate_dir: Path) -> None:
    """Concatenate PRO_OPENING.md + CON_OPENING.md into TRANSCRIPT.md.

    Each opening file already starts with its own H1 turn header (per the
    Shared formatting rules), so we just glue them together with a blank line.
    """
    pro_path = debate_dir / "PRO_OPENING.md"
    con_path = debate_dir / "CON_OPENING.md"
    transcript = debate_dir / "TRANSCRIPT.md"

    pro = (
        pro_path.read_text().strip()
        if pro_path.exists()
        else "# Round 0 — Pro (opening)\n\n_(Pro did not produce an opening.)_"
    )
    con = (
        con_path.read_text().strip()
        if con_path.exists()
        else "# Round 0 — Con (opening)\n\n_(Con did not produce an opening.)_"
    )

    transcript.write_text(f"{pro}\n\n{con}\n")


def _verdict_exists(debate_dir: Path) -> bool:
    return (debate_dir / "VERDICT.md").exists()


async def run_debate(
    question: str,
    *,
    cap: int = DEFAULT_CAP,
    allow_web: bool = True,
    console: Console | None = None,
) -> Path:
    """Run a full debate. Returns the debate directory path."""
    console = console or Console()
    debate_dir = _make_debate_dir(question)
    (debate_dir / "QUESTION.md").write_text(question.strip() + "\n")

    console.print(f"[bold]Debate directory:[/bold] {debate_dir}")
    console.print(f"[bold]Question:[/bold] {question}\n")

    # Round 0: parallel blind openings.
    console.rule("[bold]Round 0 — blind parallel openings")
    await asyncio.gather(
        run_advocate(side="pro", round_num=0, debate_dir=debate_dir, console=console, allow_web=allow_web),
        run_advocate(side="con", round_num=0, debate_dir=debate_dir, console=console, allow_web=allow_web),
    )
    _merge_openings(debate_dir)

    # Judge's first turn on combined openings.
    await run_judge(round_num=0, debate_dir=debate_dir, console=console, allow_web=allow_web)

    if _verdict_exists(debate_dir):
        console.print("\n[bold green]Verdict rendered. Debate ended.[/bold green]")
        return debate_dir

    # Rounds 1..cap
    for n in range(1, cap + 1):
        await run_advocate(side="pro", round_num=n, debate_dir=debate_dir, console=console, allow_web=allow_web)
        await run_advocate(side="con", round_num=n, debate_dir=debate_dir, console=console, allow_web=allow_web)
        await run_judge(round_num=n, debate_dir=debate_dir, console=console, allow_web=allow_web)

        if _verdict_exists(debate_dir):
            console.print(f"\n[bold green]Verdict rendered at round {n}. Debate ended.[/bold green]")
            return debate_dir

    # Cap hit — force a verdict.
    console.print(f"\n[bold red]Hard cap of {cap} rounds reached. Forcing verdict.[/bold red]")
    await run_judge(
        round_num=cap,
        debate_dir=debate_dir,
        console=console,
        force_verdict=True,
        allow_web=allow_web,
    )
    return debate_dir
