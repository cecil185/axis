---
name: axis-sprint
description: >-
  Launch a team of up to 5 parallel agents on the axis project — each claims
  one ready bead, implements it with TDD, commits, and picks up more work.
  When all agents finish, outputs a UI test checklist based on what shipped.
model: sonnet
effort: high
---

# Axis Sprint — Parallel Agent Team

## Step 1: Find ready work

Run `bd ready --json` to get all unblocked open beads. Take up to 5. If fewer
than 5 are ready, launch one agent per available bead. If none are ready, stop
and tell the user there is no available work.

## Step 2: Launch agents in parallel

For each bead (up to 5), launch a background agent using the `Agent` tool with
`run_in_background: true`. Send all agents in a **single message** so they run
concurrently.

Use `subagent_type: adlc:backend-engineer` for backend/logic issues and
`subagent_type: adlc:frontend-engineer` for UI/rendering issues. Decide based
on the bead title/description (keywords: "UI", "board", "render", "display",
"map", "tooltip" → frontend; everything else → backend).

Each agent prompt must be self-contained and include:

```
You are one of N parallel agents working on the axis game project at
/Users/cecil/Code/me/axis. Work on the single main branch — never create
sub-branches.

## Your task

Claim and implement bead <ID>: "<TITLE>"

**Description:** <FULL DESCRIPTION FROM bd ready>

## Step-by-step protocol

1. **Claim atomically**: Run `bd update <ID> --claim --json`. If claim fails or
   another agent already claimed it, stop immediately.

2. **Explore**: Read relevant source files before writing code.

3. **Implement**: Write tests first (TDD), then implementation.

4. **Run tests**: `just test` or `python -m pytest` — all must pass.

5. **Commit**: `git add <specific files> && git commit -m "<ID>: <short summary>"`
   Do NOT push — the user handles all git push operations.

6. **Next work**: Run `bd ready --json`, claim the next available unblocked
   issue, and repeat. Continue until no ready work remains.

## Rules
- Single branch, no sub-branches
- 1 commit per issue ideally
- Do NOT push to remote — user handles git push
- Use `bd update <id> --claim --json` to claim atomically
- Do NOT close beads — user closes after review
- Non-interactive flags always: cp -f, mv -f, rm -f, rm -rf
- Run `just --list` to discover available commands
```

## Step 3: Wait for all agents to complete

Do not do other work. Wait for all background agent completion notifications.
As each one arrives, note briefly: which bead finished and whether it passed.

## Step 4: Output UI test checklist

Once ALL agents have reported completion, produce a checklist of what to
manually verify in the UI. Use this logic:

**For every completed bead**, scan its title and description for UI-relevant
keywords and generate specific, concrete checks. Examples:

- "show units" / "unit count" / "label" → check that labels render on each
  territory marker without hovering; check they update after combat
- "tooltip" → hover each territory and confirm the tooltip content
- "Neutral" / "neutral territory" → find a neutral territory, confirm grey
  rendering, "N" label, correct tooltip, cannot be attacked
- "movement" / "reachable" → move a unit, confirm it can only reach valid
  destinations; check tanks can pass through friendly but stop at enemy
- "combat phase" / "roll" / "damage" → trigger a battle, confirm both sides
  take damage and the board updates correctly
- "IPC" / "income" / "economy" → if an income UI exists, check values match
  the 1–3 scale; if not, note it is backend-only with no UI to verify yet
- "win condition" → play to near-win state and confirm the victory screen
  triggers (or does not trigger prematurely for neutral territories)

Group the checklist by feature, not by agent. Mark items as **[visual]** (can
see it on screen), **[interactive]** (requires clicking/moving), or
**[backend-only]** (no UI to check yet). Keep it scannable — one bullet per
check, no prose.

End with a one-line summary: how many beads shipped, how many tests passed
(aggregate across agents), and whether any agent reported a failure.
