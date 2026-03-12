# /implement — Ticket Implementation

Given a ticket ID, spawn the software-engineer agent to implement the feature
on a new branch and open a PR.

---

## Usage

```
/implement <ticket-id>
```

Example:
```
/implement 003
```

---

## Workflow

### Step 1 — Pre-flight checks
Before spawning the agent, verify:
- The ticket file exists
- The architecture plan exists in `docs/plans/*/README.md`
- All dependency tickets are marked complete (check ticket `Dependencies` field)
- Run `git status` — working directory should be clean

If dependencies aren't met, stop and tell the user which tickets must be completed first.

### Step 2 — Gather context
Collect and provide to the agent:
1. The full ticket file
2. The feature plan README
3. Any components produced by `/design` for this ticket
4. The current project structure (`src/` listing)
5. Relevant existing files (models, services, routes related to this feature)

### Step 3 — Spawn software-engineer
The agent will:
1. Create a feature branch (`feat/<ticket-id>-<short-name>`)
2. Implement the ticket per the architecture plan
3. Write baseline tests (quality-engineer fills gaps later)
4. Run the test suite
5. Commit with conventional commit messages
6. Open a PR with the standard description template

### Step 4 — Post-implementation
After the agent completes, run:
```bash
git log --oneline feat/<branch-name>  # confirm commits look right
npm test                               # confirm tests pass
```

Show the user:
- Branch name and PR link
- Summary of what was implemented
- Test results
- Suggested next step: `/test <ticket-id>` to have the quality-engineer harden coverage

---

## Parallel Execution (with git worktrees)

To implement multiple tickets simultaneously:

```bash
# Terminal 1
git worktree add ../storage-boxes-feat-003 feat/003-qr-labels
cd ../storage-boxes-feat-003
/implement 003

# Terminal 2 (new Claude Code session)
git worktree add ../storage-boxes-feat-004 feat/004-location-manager
cd ../storage-boxes-feat-004
/implement 004
```

Each session operates in isolation. Merge tickets in dependency order.
