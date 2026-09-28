# Retro

A Retro is a short, honest audit of a work stream — done **before** starting
the next chunk of similar work, not a post-mortem filed away and forgotten.
This folder holds one dated file per retro.

This project has no paid-generation spend to audit (see the sibling `8bit`
project's `retro/` for that shape). Here the "spend" being audited is
engineering time and AI-assisted tool/token usage: tool calls, files read
(and re-read), turns spent on redirected or discarded work, and branches or
drafts opened then abandoned.

## When to run one

- Before starting a new phase or a substantial new work stream.
- After any session that included a reverted decision, a discarded branch,
  or visible back-and-forth from an ambiguous prompt.
- Whenever asked to.

## What a retro contains

1. **Spend audit** — every unit of real cost (tool calls, turns, drafted
   work later discarded — whatever the record actually supports), tagged
   productive / wasted / unconfirmed, with the *root cause* of each waste —
   not just "this didn't work out." No token-count API is available to this
   process; state that limitation plainly rather than inventing a number.
2. **Critical retrospective** — what went wrong, stated plainly, covering
   both sides: agent behavior, and process/collaboration gaps — including
   the quality of the prompts and requirements the human side supplied. No
   blame framing, no hedging either.
3. **Conclusions** — the lessons, as terse bullets. If a bullet needs a
   paragraph to justify itself, it's not a conclusion yet.
4. **Guidelines** — a short checklist derived directly from the root causes
   above. Every guideline should trace back to a specific thing that went
   wrong, and should be concrete enough to act on next time, not generic
   best-practice filler.

## Rules

- Root-cause everything. "The plan changed" is not a finding; "the decision
  to drop Fase 4 arrived one message after a full backlog draft for it had
  already been written, so the draft was pure waste" is.
- Distinguish **wasted** (redone/discarded), **unconfirmed spend** (done
  speculatively, never actually used), and **productive** spend. Different
  failure modes, different fixes.
- Verify counts against the record (`git log`, `gh pr/issue list`, the
  session transcript) — don't trust a running tally kept only in
  conversation.
- Keep it shorter than the work it's reviewing.

See the `/retro` skill (`~/.claude/skills/retro/`) for the process that
produces these files.
