---
name: feature-split
description: Converts a feature request, PRD, or free-form description into a set of vertical-slice GitHub/GitLab/local issues, ordered by dependency, ready to be worked on. Use when a user has a feature or change they want to break down into actionable issues, or when asked to create issues from a requirement or document.
---

# To Issues

Turn a feature request, PRD, or free-form description into a set of ready-to-action issues, ordered by dependency. Each issue is a **vertical slice** — it delivers usable value end-to-end, not a horizontal layer.

## 1. Gather context

Read:
- `docs/agents/issue-tracker.md` — where to publish issues
- `docs/agents/triage-labels.md` — which label strings to apply
- `docs/agents/domain.md` — then read `CONTEXT.md` and `docs/adr/` as instructed there
- The user's input (feature request, PRD, or free-form text)

If `docs/agents/` doesn't exist, run the `agent-setup` skill first.

## 2. Explore the codebase

Before drafting issues, explore the relevant parts of the codebase to understand:
- What already exists that the issues can build on
- What interfaces are relevant
- What the natural vertical slices are given the existing architecture

Don't draft issues that ignore existing structure.

## 3. Draft vertical slices

Draft the issues. Each issue must be:

- **Vertical** — it crosses all relevant layers (API → service → DB, or UI → API → DB) and delivers something usable, not just a layer of implementation
- **Small** — achievable in one focused session; if it seems large, split it
- **Unambiguous** — the acceptance criteria must be verifiable without asking the author

Classify each issue as either:
- **HITL** (human-in-the-loop) — needs human judgment, creativity, or sign-off mid-task
- **AFK** (away-from-keyboard) — fully specifiable, safe to run without supervision

## 4. Quiz the user

Before publishing, present the draft issue list. Ask:
- Are there any missing slices?
- Are any slices too large?
- Which should be HITL vs AFK?
- Are there dependencies you weren't aware of?

Get sign-off on the full list before publishing.

## 5. Publish in dependency order

Publish issues in dependency order — the issue that must be done first goes first. When creating each issue, include any `Blocked by: #<N>` references.

Use this template for each issue:

```markdown
**Parent**: <parent issue number or "none">

**What to build**

<one paragraph describing the vertical slice>

**Acceptance criteria**

- [ ] <verifiable criterion>
- [ ] <verifiable criterion>

**Blocked by**

- #<N> (if applicable)
```

Apply the `needs-triage` label to each new issue.
