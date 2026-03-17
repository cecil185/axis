# Agent Instructions

## Parallel Team Mode

When multiple agents work in parallel on this codebase:

- **Single branch**: All agents work on the same branch — never create sub-branches
- **Atomic claiming**: Use `bd update <id> --claim --json` before starting; skip if claim fails
- **1 commit per issue** (ideally): Commit message format: `<issue-id>: <summary>`
- **Merge conflicts**: Resolve yourself — pull, rebase, fix conflicts, push:
  ```bash
  git pull --rebase
  # fix any conflicts manually
  git add -f <conflicted-files>
  git rebase --continue
  git push
  ```
- **After finishing an issue**: Run `bd ready --json` and claim the next available issue
- **Do NOT close issues** — user reviews and closes after PR
- **PR trigger**: After 6 issues are committed, the orchestrating agent opens a PR

---

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work atomically
```

**Before ending a session:** You must make UI changes to accompany your code changes. You MUST commit and push to remote. See [Landing the Plane](#landing-the-plane-session-completion) — work is NOT complete until `git push` succeeds. Create any future issues in beads.

## Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations to avoid hanging on confirmation prompts.

Shell commands like `cp`, `mv`, and `rm` may be aliased to include `-i` (interactive) mode on some systems, causing the agent to hang indefinitely waiting for y/n input.

**Use these forms instead:**
```bash
# Force overwrite without prompting
cp -f source dest           # NOT: cp source dest
mv -f source dest           # NOT: mv source dest
rm -f file                  # NOT: rm file

# For recursive operations
rm -rf directory            # NOT: rm -r directory
cp -rf source dest          # NOT: cp -r source dest
```

**Other commands that may prompt:**
- `scp` - use `-o BatchMode=yes` for non-interactive
- `ssh` - use `-o BatchMode=yes` to fail instead of prompting
- `apt-get` - use `-y` flag
- `brew` - use `HOMEBREW_NO_AUTO_UPDATE=1` env var

<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Version-controlled: Built on Dolt with cell-level merge
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" -d "Description" -t bug|feature|task -p 0-4 --json
# Or: --description="Detailed context"
# Types: bug, feature, task, epic, chore. Priority: 0 (critical) to 4 (backlog).
# Output includes "id" (e.g. job-rag-qmz); note it for linking dependencies.
```

**Dependencies** (blocker must exist first; add links after creating the blocked issue):

```bash
bd dep add <blocked-id> <blocker-id>   # <blocked-id> is blocked by <blocker-id>
bd dep tree <id>                       # Show dependency tree
bd dep cycles                          # Detect circular dependencies
```

Create parent issues first, then create children, then run `bd dep add` for each (blocked, blocker) pair.

**Claim and update:**

```bash
bd update <id> --claim --json
bd update bd-42 --priority 1 --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task atomically**: `bd update <id> --claim`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: Commit and push to remote; do NOT close the bead — the user closes it after reviewing the changes.

### Auto-Sync

bd automatically syncs with git:

- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` to get new work
- ❌ Do NOT work on an issue if claiming it failed
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**Session-end checklist (run in order):**

1. **File issues for remaining work** — Create issues for anything that needs follow-up.
2. **Run quality gates** (if code changed) — Tests, linters, builds.
3. **Update issue status** — Update in-progress items only.
4. **Push to remote** (required):
   ```bash
   git pull --rebase
   git push
   git status   # MUST show "up to date with origin"
   ```
5. **Clean up** — Clear stashes.
6. **Verify** — All changes committed and pushed to remote.
7. **Hand off** — Brief context for next session.

**CRITICAL RULES:**
- Work is NOT complete until `git push` has been run successfully.
- NEVER say "ready to push when you are" — you must push.
- If push fails, fix and retry until it succeeds.

<!-- END BEADS INTEGRATION -->
Use 'bd' for task tracking
Develop in docker containers using Makfile commands