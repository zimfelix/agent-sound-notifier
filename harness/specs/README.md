# Behavior specifications

A spec preserves product intent across sessions. Use a coherent area, not one file per edit. Do not copy the implementation or repeat the project brief.

Minimal shape (adapt headings, keep the information):

```markdown
# S001 — Outcome
Status: Modified
Source/scope: confirmed request; exclusions.

## Acceptance
- A1: independently observable result, including relevant failure cases.

## Check and work plan
Required checks and affected regression; next authorized action / consequential blocker.

## Evidence
A1: actual check, result, tested revision or uncommitted date.
Several criteria may share a check if it genuinely covers each of them.
```

`Modified`: new/changed behavior or missing required evidence. `Implemented`: all applicable acceptance criteria and required checks have current valid evidence. An unavailable live provider is not covered by a fake. Preserve existing expectations during refactors; change them only for a confirmed behavior change. Refresh affected evidence when code/configuration/data/environment changes, not all unrelated criteria by ritual. Keep only latest evidence, not a test diary.

A tiny correction can update an existing spec. A behavior-preserving refactor, docs change or visual adjustment does not need a new spec. The active spec may hold the continuation state; PROJECT links to it, without duplicating the checklist in PROJECT and an idea. Record the next authorized implementation action and a useful entry command, not only a regression command or an invented new approval gate. If the local milestone is complete, name the real decision/blocker for the next one; don't imply the whole product is finished.
