"""Wrappers around claude_agent_sdk.query for each debate role."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)
from rich.console import Console

Side = Literal["pro", "con"]
Role = Literal["pro", "con", "judge"]

# Model ID is overridable via CLAUDE_MODEL env var. For Bedrock, set this to the
# inference profile ID shown in the AWS Bedrock console (e.g. "us.anthropic.claude-opus-4-7")
# along with CLAUDE_CODE_USE_BEDROCK=1 and AWS_REGION in .env.
MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")
THINKING_BUDGET = 20_000
MAX_TURNS = 60

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_SHARED = (_PROMPTS_DIR / "_shared.md").read_text()
ADVOCATE_SYSTEM = (_PROMPTS_DIR / "advocate.md").read_text() + "\n\n" + _SHARED
JUDGE_SYSTEM = (_PROMPTS_DIR / "judge.md").read_text() + "\n\n" + _SHARED


def _advocate_user_prompt(side: Side, round_num: int, debate_dir: Path) -> str:
    question = (debate_dir / "QUESTION.md").read_text().strip()
    opening_path = debate_dir / f"{side.upper()}_OPENING.md"
    transcript_path = debate_dir / "TRANSCRIPT.md"

    if round_num == 0:
        return f"""You are the **{side.upper()}** advocate. This is **Round 0** — your opening statement.

The question under debate:

> {question}

You are writing your opening **blind** — the opposing side is writing theirs simultaneously and you cannot see it.

Your task, in order:
1. Use `WebSearch` to research the question if it is empirical — aim for **5–10 targeted searches**, not dozens. For theoretical/philosophical questions, fewer or none, but reason with rigor.
2. Use extended thinking to work through the strongest form of your case — the crux, your best evidence and reasoning, the likely attacks you need to pre-empt.
3. **Write your opening using the `Write` tool to exactly this path: `{opening_path}`**.

The first line of your file must be exactly this H1 header:

```
# Round 0 — {side.capitalize()} (opening)
```

All other headers in your opening must be H2 (`##`) or deeper — see the Shared formatting rules in your system prompt. Be thorough and structured.

You **must** produce the file before finishing your turn. Research without writing is a failure. Do not read or write any other file.
"""
    return f"""You are the **{side.upper()}** advocate. This is **Round {round_num}**.

The question under debate:

> {question}

Your task, in order:
1. Read `{transcript_path}` to see the full debate so far — including the opponent's latest turn and any questions directed at you.
2. Research with `WebSearch` **as needed** for empirical points; reason rigorously for theoretical ones. A handful of targeted searches max.
3. **Append your turn to `{transcript_path}` using the `Edit` tool.**

The first line of your appended turn must be exactly this H1 header:

```
# Round {round_num} — {side.capitalize()}
```

All other headers in your turn must be H2 (`##`) or deeper. See the Shared formatting rules.

Your turn structure, in order:
- Answer any outstanding questions directed at {side.upper()} (or at both sides). Do this first.
- Steelman the opponent's latest argument.
- Rebut it.
- Advance your own case.
- Optionally ask the opponent or the Judge pointed questions.

You **must** produce the file edit before finishing your turn. **You never concede.** Hold your position — the Judge decides when the debate ends.
"""


def _judge_user_prompt(round_num: int, debate_dir: Path, force_verdict: bool = False) -> str:
    question = (debate_dir / "QUESTION.md").read_text().strip()
    transcript_path = debate_dir / "TRANSCRIPT.md"
    verdict_path = debate_dir / "VERDICT.md"

    if force_verdict:
        return f"""You are the **Judge**. The debate has hit its hard round cap without a verdict.

The question under debate:

> {question}

You **must** render a final verdict now. Read `{transcript_path}` in full and then write the file `{verdict_path}` with your outcome, crux, and reasoning, in the exact format specified in your system prompt. If the debate is genuinely unresolved, `outcome: unresolved` is acceptable — but you must name the crux and what evidence would resolve it.
"""

    return f"""You are the **Judge**. This is **Round {round_num}**.

The question under debate:

> {question}

Your task, in order:
1. Read `{transcript_path}` in full. Pay close attention to the two most recent turns (Pro and Con).
2. Choose one of three actions:
   - **Ask** — append your judge turn to `{transcript_path}` (using `Edit`) with commentary and specific questions for Pro, Con, or both.
   - **Continue** — append your judge turn with commentary and no questions, signalling the debate should continue.
   - **Verdict** — create the file `{verdict_path}` (using `Write`) with your final verdict. This ends the debate.
3. Check for fabricated or missing citations and un-steelmanned rebuttals; call them out in your commentary.

If you choose **Ask** or **Continue**, the first line of your appended turn must be exactly this H1 header:

```
# Round {round_num} — Judge
```

All other headers in your turn must be H2 (`##`) or deeper. Use sections like `## Commentary`, `## Questions for Pro`, `## Questions for Con`. See the Shared formatting rules.

Only render a verdict if Truth is clear, or if the debate has reached an unresolvable impasse you can name precisely. You **must** produce a file edit or write before finishing your turn.
"""


def _print_message(console: Console, role: Role, message) -> None:
    """Stream a single SDK message to the terminal."""
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                console.print(block.text, end="", style=_style_for(role), soft_wrap=True)
            elif isinstance(block, ToolUseBlock):
                name = block.name
                if name == "WebSearch":
                    q = block.input.get("query", "")
                    console.print(f"\n  [dim]🔍 WebSearch: {q}[/dim]")
                elif name in ("Edit", "Write"):
                    path = block.input.get("file_path", "")
                    console.print(f"\n  [dim]✎ {name}: {Path(path).name}[/dim]")
                elif name == "Read":
                    path = block.input.get("file_path", "")
                    console.print(f"\n  [dim]📖 Read: {Path(path).name}[/dim]")
    elif isinstance(message, ResultMessage):
        turns = getattr(message, "num_turns", None)
        cost = getattr(message, "total_cost_usd", None)
        if turns is not None or cost is not None:
            parts = []
            if turns is not None:
                parts.append(f"{turns} turns")
            if cost is not None:
                parts.append(f"${cost:.3f}")
            console.print(f"\n  [dim]· {role} session done ({', '.join(parts)})[/dim]")


def _style_for(role: Role) -> str:
    return {"pro": "green", "con": "red", "judge": "yellow"}[role]


async def run_advocate(
    *,
    side: Side,
    round_num: int,
    debate_dir: Path,
    console: Console,
    allow_web: bool = True,
) -> None:
    """Spawn an advocate agent session for one turn."""
    role: Role = side
    console.rule(f"[bold {_style_for(role)}]Round {round_num} — {side.capitalize()}")

    tools = ["Read", "Edit", "Write"]
    if allow_web:
        tools.append("WebSearch")

    options = ClaudeAgentOptions(
        system_prompt=ADVOCATE_SYSTEM,
        cwd=str(debate_dir),
        allowed_tools=tools,
        model=MODEL,
        permission_mode="acceptEdits",
        thinking={"type": "enabled", "budget_tokens": THINKING_BUDGET},
        max_turns=MAX_TURNS,
    )

    prompt = _advocate_user_prompt(side, round_num, debate_dir)
    async for message in query(prompt=prompt, options=options):
        _print_message(console, role, message)
    console.print()  # newline after the turn


async def run_judge(
    *,
    round_num: int,
    debate_dir: Path,
    console: Console,
    force_verdict: bool = False,
    allow_web: bool = True,
) -> None:
    """Spawn the Judge agent session for one turn."""
    console.rule(f"[bold {_style_for('judge')}]Round {round_num} — Judge")

    tools = ["Read", "Edit", "Write"]
    if allow_web:
        tools.append("WebSearch")

    options = ClaudeAgentOptions(
        system_prompt=JUDGE_SYSTEM,
        cwd=str(debate_dir),
        allowed_tools=tools,
        model=MODEL,
        permission_mode="acceptEdits",
        thinking={"type": "enabled", "budget_tokens": THINKING_BUDGET},
        max_turns=MAX_TURNS,
    )

    prompt = _judge_user_prompt(round_num, debate_dir, force_verdict=force_verdict)
    async for message in query(prompt=prompt, options=options):
        _print_message(console, "judge", message)
    console.print()
