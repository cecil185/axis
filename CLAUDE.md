# Agent Instructions

## Parallel Team Mode

When multiple agents work in parallel on this codebase:

- **Single branch**: All agents work on the same branch — never create sub-branches
- **1 commit per issue** (ideally): Commit message format: `<issue-id>: <summary>`
- **Merge conflicts**: Resolve yourself — pull, rebase, fix conflicts locally:
  ```bash
  git pull --rebase
  # fix any conflicts manually
  git add -f <conflicted-files>
  git rebase --continue
  ```
- **Do NOT close issues** — user reviews and closes after PR
- **Do NOT push to remote** — the user handles all `git push` operations

---

This project uses **Linear** for issue tracking. Issues are in the [Axis project](https://linear.app/cecils-projects/project/axis-26251b120abe) under the Cecil's Projects workspace (team key: CEC).

## Quick Reference

Issues are tracked in Linear under the Axis project (CEC-5 through CEC-19 and beyond).

**Before ending a session:** You must make UI changes to accompany your code changes. Commit your work locally — do NOT push to remote (the user handles `git push`). See [Landing the Plane](#landing-the-plane-session-completion). Create any future issues in Linear.

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

## Issue Tracking with Linear

**IMPORTANT**: This project uses **Linear** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

Issues live in the **Axis** project at https://linear.app/cecils-projects/project/axis-26251b120abe (team: Cecil's Projects, key: CEC).

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `1` - Urgent
- `2` - High (major features, important bugs)
- `3` - Normal (default)
- `4` - Low (polish, optimization, backlog)

### Workflow for AI Agents

1. **Check ready work**: Look for unblocked issues in the Axis Linear project
2. **Work on it**: Implement, test, document
3. **Discover new work?** Create a new Linear issue in the Axis project with appropriate blockedBy dependencies
4. **Complete**: Commit locally (do NOT push — the user handles pushing); do NOT close the issue — the user closes it after reviewing the changes.

### Important Rules

- ✅ Use Linear for ALL task tracking
- ✅ Link discovered work with blockedBy dependencies
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT duplicate tracking systems

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until all changes are committed locally.

**Session-end checklist (run in order):**

1. **File issues for remaining work** — Create Linear issues for anything that needs follow-up.
2. **Run quality gates** (if code changed) — Tests, linters, builds.
3. **Update issue status** — Update in-progress items only.
4. **Commit locally** (required):
   ```bash
   git pull --rebase
   git status   # Verify all changes are committed
   ```
5. **Clean up** — Clear stashes.
6. **Verify** — All changes committed locally.
7. **Hand off** — Brief context for next session; let the user know the branch is ready for them to push.

**CRITICAL RULES:**
- Work is NOT complete until all changes are committed locally.
- Do NOT run `git push` — the user handles all pushes to remote.
- If you have uncommitted changes, commit them before ending the session.

Develop in docker containers using Makefile commands
