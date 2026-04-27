# The Truth — Working Notes

## Mission

Use AI to resolve debates and reach the capital-T Truth on any topic. The enemy is sycophancy: frontier models hedge, both-sides, and mirror the user. This repo builds scaffolding that forces AI past that failure mode.

## Core design principles

1. **Adversarial multi-agent.** Sycophancy is a property of a single agent trying to please a user. Pit agents against each other — one argues *for*, one argues *against*, a judge evaluates on argument strength alone. No individual agent has a gradient toward flattery.
2. **Type the question first.** Different question classes need different machinery:
   - **Empirical** — resolves with evidence. Weight sources, require citations, disqualify hallucinations.
   - **Normative** — resolves conditional on value axioms. Job is to surface which axioms each side is assuming, then evaluate consistency.
   - **Metaphysical** — may be underdetermined by accessible evidence. Win condition is the strongest form of each position and where they bottom out.
3. **No hedging.** Agents must commit to a position. "Evidence insufficient, here is what would resolve it" is a valid position; "it depends / both sides have points" is not.
4. **Steelman mandated.** Any agent must be able to state the opposing view so well its proponent would agree before attacking it.
5. **Cite, don't assert.** Empirical claims need sources. Hallucinated citations are disqualifying.
6. **Show work.** Conclusions without auditable reasoning are useless. The user has to be able to walk the chain.

## Anti-patterns

- A single "truth-finder" prompt. That is exactly what sycophancy eats.
- Treating normative and empirical questions with the same pipeline.
- Letting agents hedge their way to a tie.
- Summarizing a debate into mush instead of declaring a winner (or explicitly: "this is underdetermined, here is why").

## Collaboration notes for Claude

- Don't soften disagreements. If the user's premise is wrong or contested, say so directly — this repo is *about* fighting that instinct.
- When designing or reviewing agent prompts, check them against the principles above. Prompts that allow hedging or skip steelmanning are bugs.
- The user (Josh) prefers terse responses and action over planning once direction is set.
