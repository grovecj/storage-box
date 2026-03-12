# /test — Write & Run Tests for a Ticket

Given a ticket ID, spawn the quality-engineer to write comprehensive tests
for the implemented feature and ensure the 80% coverage gate is met.

---

## Usage

```
/test <ticket-id>
```

Example:
```
/test 003
```

---

## Workflow

### Step 1 — Context
Read:
- The ticket file (acceptance criteria define what *must* be tested)
- The architecture plan (data model and API contract define integration test targets)
- The implemented source files on the current branch
- Existing test files to understand patterns and avoid duplication

### Step 2 — Spawn quality-engineer
Provide:
1. Full ticket content (acceptance criteria are the test spec)
2. All source files implemented in this ticket
3. Architecture plan (API contracts, data model)
4. Existing test examples from the codebase (for pattern consistency)

The agent will produce:
- Unit tests for service functions, utilities, hooks
- Component tests for any React components
- Integration tests for API endpoints and database operations
- A coverage report

### Step 3 — Run and verify
Execute the test suite:
```bash
npm test
npm run test:coverage
```

If coverage falls below 80%:
- Identify the uncovered files
- Ask the quality-engineer to add targeted tests for the gaps
- Re-run until the gate passes

### Step 4 — Commit tests
```bash
git add .
git commit -m "test(<feature>): add coverage for <ticket-id>"
git push
```

Show the user:
- Coverage % achieved
- Test files created
- Whether the 80% gate passes
- Any deliberate coverage gaps and rationale

---

## Notes

- Run `/test` after `/implement`, before the PR is merged
- If coverage is genuinely impossible to reach 80% (e.g. highly side-effectful code), document the exception in the ticket and PR description
- Integration tests that require a database should use a local/test instance — never run against production
