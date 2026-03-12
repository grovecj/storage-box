# /design — UI Component Design

Given a ticket ID, spawn the ui-designer agent to produce production-ready
React components for the feature.

---

## Usage

```
/design <ticket-id>
```

Example:
```
/design 003
```

---

## Workflow

### Step 1 — Gather context
Read:
- The ticket file at `docs/plans/*/tickets/<ticket-id>-*.md`
- The plan README for that feature
- Existing components in `src/components/` to understand established patterns
- `CLAUDE.md` for any design system notes

### Step 2 — Spawn ui-designer
Provide the agent with:
1. The full ticket content
2. The feature's acceptance criteria
3. A summary of existing relevant components (names, props, rough purpose)
4. Any wireframes or design notes from the product ticket

### Step 3 — Output
The ui-designer will produce component code. Save components to:
```
src/components/<feature-slug>/<ComponentName>.tsx
```

If the agent produces multiple components, create the directory and save each file.

### Step 4 — Confirm with user
Show the user:
- Which components were created
- File paths
- A brief design summary (aesthetic direction chosen, key decisions)
- Next step: `/implement <ticket-id>` to wire them into the app

---

## Notes

- Design tickets typically need to run before the corresponding implement ticket
- If the ticket doesn't require new UI (backend only, data migrations, tests), skip this command
- Components produced here are used as-is by the software-engineer — avoid modifying them during implementation unless there's a technical blocker
