# /plan — Feature Planning

Given a feature request or idea, coordinate the product-designer and software-architect
in parallel to produce a complete plan with actionable tickets.

---

## Usage

```
/plan <feature description or request>
```

Example:
```
/plan Add the ability to generate and print QR code labels for boxes so users
can scan a box to instantly see its contents
```

---

## Workflow

### Step 1 — Read context
Before spawning agents, read:
- `CLAUDE.md` (project conventions, domain vocabulary)
- `docs/plans/` directory listing (to determine the next ticket ID range)
- `src/` high-level structure (to understand what already exists)

### Step 2 — Spawn agents in parallel
Spawn both agents simultaneously with the feature request and relevant codebase context:

**product-designer**: Ask for user stories, flows, acceptance criteria, and proposed ticket breakdown.

**software-architect**: Ask for data model changes, API contracts, system design, and implementation sequence.

Provide both agents with:
1. The full feature request
2. Relevant existing code snippets (especially models, API routes, and key components)
3. Current ticket ID range (so they number tickets consistently)

### Step 3 — Synthesize
Combine the outputs into a unified plan. Resolve any conflicts (e.g. if the architect's data model implies changes to the product designer's user flows). Produce:

**`docs/plans/<feature-slug>/README.md`** containing:
- Feature overview and goals
- User stories (from product-designer)
- Architecture summary (from software-architect)
- Data model changes
- Implementation sequence
- Open questions requiring decisions

**`docs/plans/<feature-slug>/tickets/`** — one file per ticket:
- Use the ticket format defined in `CLAUDE.md`
- Order by implementation sequence (dependencies first)
- Mark which agent executes each ticket (ui-designer, software-engineer, quality-engineer)

### Step 4 — Present summary
Show the user:
- Feature name and 1-line summary
- Ordered ticket list with IDs, titles, complexity, and assigned agent
- Any open questions that need a decision before work begins
- Suggested starting point (usually the first unblocked ticket)

---

## Notes

- Don't start implementing — this command produces a plan only
- If the feature is very small (1-2 tickets), still create the plan files for traceability
- If the feature seems too large for one plan, suggest splitting it
