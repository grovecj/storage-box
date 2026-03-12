# /review — Pre-Merge Branch Review

Spawn the quality-engineer to review the current branch before merging.
Produces a categorized findings report and runs the full test suite.

---

## Usage

```
/review
```

Run this from the feature branch you want reviewed. No arguments needed —
the agent will diff the current branch against main automatically.

---

## Workflow

### Step 1 — Identify branch
```bash
git branch --show-current    # confirm you're on a feature branch
git diff main --stat         # show changed files
```

If on main, stop and tell the user to switch to the feature branch first.

### Step 2 — Gather context
Collect:
- Full diff of current branch vs main (`git diff main`)
- The ticket file this branch implements
- Test results (`npm test`)
- Coverage report (`npm run test:coverage`)

### Step 3 — Spawn quality-engineer in review mode
Provide the agent with all of the above. The agent will produce:
- **Summary**: 1-paragraph assessment
- **🔴 Must Fix**: Blocking issues (bugs, security, missing critical tests, coverage < 80%)
- **🟡 Should Fix**: Strong recommendations
- **💡 Suggestions**: Optional improvements
- **Test results**: Pass/fail
- **Coverage**: % and gate status

### Step 4 — Handle findings

**If 🔴 Must Fix items exist:**
Ask the user: "There are blocking issues. Would you like me to fix them automatically?"
- If yes: fix each item, commit as `fix: address review feedback`, re-run tests
- If no: present the list for manual resolution

**If only 🟡 / 💡 items:**
Present findings and let the user decide. Don't block the merge.

### Step 5 — Final status
Report:
- Overall: ✅ Ready to merge / ⚠️ Merge with noted issues / 🚫 Blocked
- PR checklist status
- Any items deferred to follow-up tickets

---

## When to Run

Typically run in this sequence:
1. `/implement <id>` — build it
2. `/test <id>` — harden coverage
3. `/review` — gate check before merging

Can also be run standalone if you've been coding manually outside of the agent workflow.
