# Shared rules (apply to all agents)

These rules apply to every agent in this debate — Pro, Con, and Judge alike. They are non-negotiable.

## Formatting your turn

Every time you append a turn to `TRANSCRIPT.md` (or, in Round 0 for the advocates, write your opening to `PRO_OPENING.md` / `CON_OPENING.md`), the **first line of your turn must be a markdown H1** with this exact form:

```
# Round {N} — {Role}
```

Where `{N}` is the round number and `{Role}` is exactly one of `Pro`, `Con`, or `Judge`. Examples:

- `# Round 0 — Pro (opening)`
- `# Round 0 — Con (opening)`
- `# Round 1 — Pro`
- `# Round 3 — Judge`

**All other headers within your turn must be H2 (`##`) or deeper.** Never use a second H1 inside a single turn — the H1 is reserved for the turn header itself. This keeps the transcript navigable and the structure consistent across all rounds and agents.

Use H2 / H3 freely to organize your thinking. Suggested patterns:

- Advocates: `## Answers to outstanding questions`, `## Steelman of opponent's argument`, `## Rebuttal`, `## My case`, `## Questions for opponent`
- Judge: `## Commentary`, `## Questions for Pro`, `## Questions for Con` (or `## Continue` / `## Verdict` if applicable)

## Markdown hygiene

- Use blank lines between paragraphs, headers, and code blocks. Do not run paragraphs together.
- Quote sources with `>` blockquotes when quoting text directly.
- Use inline links: `[descriptive anchor text](URL)`. Do not paste bare URLs unless that is the citation.
- Use bullet lists or numbered lists when enumerating multiple points; do not bury lists inside running prose.
- Use **bold** for the load-bearing claim of a paragraph; use *italics* sparingly.
- Use a horizontal rule (`---`) only at the very end of your turn, never within it.
