# Retro: the Fase 4 decision, and closing the project's scope

Scope: one continuous Claude Code session, 2026-09-25 11:12 UTC → 2026-09-28
08:51 UTC (session file `99c4a213-a65a-45fa-b939-c7527f55c21a.jsonl`),
covering the "are we ready for Phase 4?" readout, the `dev`→`main`
promotion, the Fase 4 backlog draft, its reversal, the scope-closure docs,
and building this project's `/retro` skill. Written using that skill.

**Scope limit, stated plainly:** this does *not* audit the ~14 earlier
sessions (2026-09-18 to 2026-09-25) that actually built Fases 1–3 — those
transcripts exist but weren't read for this retro. Claiming to have audited
them without doing so would violate the skill's own "verify against the
record" rule worse than just saying so. If a Fases-1-3 build retro is
wanted, it needs its own pass over those files.

## Spend audit

No token-count API was available this session. The proxy used instead —
tool calls, turns, and git/PR records — comes from parsing the session's
own JSONL transcript and re-querying `git`/`gh` at write time, not from a
running tally kept in conversation.

**Grounded counts:** 76 real tool calls (39 `Bash`, 10 `Read`, 7 `Edit`,
6 `Grep`, 4 `Skill`, 4 `AskUserQuestion`, 3 `Write`, 1 each `Glob` /
`ListAgents` / `ExitPlanMode`) across 8 user turns. 3 PRs opened, all
merged (#127, #128, #129), zero reverted after merge.

| Item | Status | Root cause |
|---|---|---|
| `dev`→`main` promotion (PR #127) | **Productive** | Delivered the first explicitly requested outcome; CI green, merged clean. |
| Fase 4 `Backlog.md` EPIC F4 draft (TF4.1–TF4.20, ~20 tasks, one commit on `docs/backlog-fase-4`) | **Wasted** | Fully written before "drop Fase 4" arrived one message later. Never pushed; branch deleted, nothing lost from the remote, but the drafting work itself (reading the brief's Fase 4 section, matching `Backlog.md`'s format, writing 20 task lines) was real and discarded. |
| `grill-me` skill launch for the Fase 4 decisions doc | **Wasted** | Same root cause as above — interrupted before its first question was answered, so essentially zero work was salvageable, but also essentially zero was spent beyond one skill load and one question. |
| Locating "the retro process we stashed somewhere" (grep across this repo, `git stash list`, `git log --all`, a Desktop-wide `find`) | **Partly wasted** | The first two lookups (this repo, git history) were reasonable diligence. The third and fourth (memory files, Desktop-wide find) came *before* asking the user, when asking was already the better move — it turned out to be a different Claude Code project entirely, which no local search could have found. |
| Scope-closure docs (`Claude.md`, `decisions-proceso.md`, `Backlog.md`, both READMEs, `docs/retro/README.md`; PRs #128, #129) | **Productive** | Delivered the second requested outcome; CI green on both, merged. |
| First commit attempt for the scope-closure docs | **Unconfirmed spend, environmental** | Blocked mid-turn by "the server-side auto mode classifier gave no verdict"; the composed commit message had to be retyped after plan mode resolved. Not a prompting or agent-judgment issue — a tool-layer gap. |
| `/retro` skill draft (`~/.claude/skills/retro/SKILL.md`) | **Productive, but unconfirmed until reused** | Built and used once (this file). A skill earns "productive" for real once it's invoked a second time on a different project/work stream, per its own rule that a fix/pattern isn't proven until it's checked against more than the one case that prompted it. |
| Companion hookup (`/companion`, mid-sequence) | **Productive** | Small, explicit, one-shot request handled between CI poll waits at no real cost to the main thread of work. |

**Read twice: `Backlog.md`.** Not waste — it was re-read after a
stash-pop auto-merge that could have changed it underneath the plan, which
is exactly the "verify, don't assume" behavior the skill's own rules call
for, not a redundant read.

## Critical retrospective

**Agent mistakes:**
- Executed all three parts of "1. merge, 2. create Fase 4 tasks, 3. call
  grill-me" in the order given, including the heaviest deliverable (a
  20-task backlog draft) *before* the discovery step (`grill-me`) that
  would have surfaced, within its first question, whether Fase 4 was even
  still happening. Running grill-me first — or at least flagging that the
  backlog draft was provisional until grill-me confirmed the direction —
  would have avoided drafting work that had a real chance of being
  premature.
- Kept searching for the "stashed" retro doc (git stash, git log --all,
  a Desktop-wide find) for two more tool calls past the point where asking
  "where should I look?" was clearly the more efficient move — the answer
  turned out to be information only the user had (a different project
  entirely), which no amount of local searching would have found.
- Handled the `docs/backlog-fase-4` cleanup via a stash/pop across a
  branch switch rather than a plain revert of the one commit — worked, but
  was more fiddly than necessary for a single unpushed commit.

**Process/collaboration gaps — including the prompts themselves:**
- The three-part instruction bundled a genuinely still-open question
  (was Fase 4 actually starting?) with a concrete execution request (draft
  its backlog tasks), in the same message where the previous turn's
  readout had just listed several unresolved Fase 4 planning gaps. Asking
  for the backlog *and* the grilling session in one breath meant the
  backlog had no chance to reflect what the grilling would have found.
- "We stashed somewhere info about retro process" carried no pointer —
  not even "check the other project" until asked directly. A single
  detail (project name, rough date, "it's in 8bit") would have collapsed
  a multi-tool, cross-project search into one lookup.
- Two genuinely large pivots landed in the same short window: "start
  Fase 4" → (after a full readout) "merge + draft tasks + grill me" →
  (one message later) "actually, drop Fase 4 entirely." Neither pivot was
  unreasonable on its own — the second one, especially, was a good call,
  since a course project on a fixed budget gains more from a process
  retro than from an unstarted Fase 4 — but the second reversal landing
  after the backlog draft was already written is exactly what made that
  draft wasted rather than merely unused.

**What went well — keep doing this:**
- Every destructive-adjacent git action (branch deletion, `dev`→`main`
  merges) went through an explicit confirmation, even on branches
  provably safe to touch (unpushed, fully merged). No history or branch
  was lost across two full direction reversals.
- The single-question `AskUserQuestion` on skill scope (global vs.
  project-local) resolved a real fork in one round-trip instead of
  guessing or over-asking.
- Opening with "are we ready for Phase 4?" — a genuinely open, diagnostic
  question rather than an assumption — produced an accurate, specific
  readout (stale `main`, missing decisions doc, no backlog tasks) that
  the rest of the session's decisions were correctly built on.

## Conclusions

- A reversal costs the most when it lands *after* a deliverable is fully
  drafted, not when the first sign of reconsideration appears.
- Bundling "go build X" with "and also discover Y" in one instruction
  risks X being obsolete by the time Y would have informed it.
- A single pointer collapses a multi-tool, cross-project search into one
  lookup — "somewhere" costs real tool calls to resolve.
- No token-count API existed this session; tool-call/turn counts and
  git/PR records are the honest substitute, not a token estimate — and
  this file says so rather than fabricating a number.
- Re-reading a file after an operation that could have changed it is
  verification, not waste; the distinction matters for which spend-audit
  bucket it goes in.

## Guidelines

1. When an instruction bundles a concrete deliverable with an open-ended
   discovery step whose outcome could change that deliverable, run the
   discovery step first — or explicitly mark the deliverable as
   provisional until discovery confirms the premise still holds.
2. When told something exists "somewhere" with no pointer, do at most two
   targeted searches before asking where to look, rather than exhausting
   every guess first — especially once the search has left the current
   project's own files.
3. Before executing a multi-part instruction where one part assumes a
   decision the previous turn's readout just called into question, name
   that assumption out loud in the first line of the response, not just
   in a closing summary.
4. Ground every "how much did this cost" claim in `git log`, `gh pr
   list`, or the session transcript at write time — a remembered count is
   a draft, not a fact, until checked against the record.
5. Keep destructive-adjacent git operations behind an explicit confirm
   even when the target is provably safe (unpushed, fully merged) —
   asking is cheap, and the answer being predictable doesn't make the
   check worthless.
