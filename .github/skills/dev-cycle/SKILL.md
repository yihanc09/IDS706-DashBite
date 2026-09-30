---
name: dev-cycle
description: Run a fresh-chat Architect → Implementer → Manual Smoke Test → Reviewer workflow for a planned feature.
---

# Dev Cycle

Use this skill when a feature should move through three independent chats that
share only the repository, its append-only `docs/plan.md`, interfaces, and
tests.

## Workflow

### 1. Architect

Start a fresh chat with:

```text
/dev-cycle architect <feature request>
```

The Architect must:

- Inspect the repository and read `docs/plan.md` first.
- Append one stage to `docs/plan.md`; never rewrite earlier stages.
- Define the goal, interfaces, architecture boundaries, automated tests, and a
  pasteable Makefile-based Manual Smoke Test.
- Not implement application code.

### 2. Implementer

After the Architect chat is complete, start a separate fresh chat with:

```text
/dev-cycle implement <feature request>
```

The Implementer must:

- Read the plan and implement only the planned stage.
- Preserve earlier plan sections and update only the current stage's smoke
  commands if they drift.
- Add or update tests and run the smallest relevant suite, then the full suite
  when practical.
- Keep stage boundaries and the Makefile public interface intact.

### 3. Manual Smoke Test

Before review, run the exact Manual Smoke Test from the current
`docs/plan.md` section in the classroom. Prefer `make` targets; do not replace
the demonstration with ad-hoc Python commands when a target exists. Record
visible logs, files, and any process shutdown steps.

### 4. Reviewer

Only after the smoke test, start a third fresh chat with:

```text
/dev-cycle review <feature request>
```

The Reviewer must:

- Read the relevant `docs/plan.md` stage first.
- Review the implementation as if unaffiliated with the author.
- Verify architecture, tests, and the documented smoke test.
- Add stronger tests or fix real bugs, never weaken legitimate assertions.
- Run the full suite and summarize findings, changes, and status.

## Shared contract

Each chat starts fresh. The repository is the handoff. Keep one append-only
`docs/plan.md`; interfaces, Makefile targets, fixtures, and tests are the
shared evidence. Do not use hidden chat context as an implementation contract.

## Example

```text
/dev-cycle architect Add caching to the API
# inspect the appended plan
/dev-cycle implement Add caching to the API
# run the plan's Manual Smoke Test
/dev-cycle review Add caching to the API
```
