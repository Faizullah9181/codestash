# Issue tracker: local markdown

Issues for this repo live as markdown files under `.scratch/`. This is a simple, git-friendly alternative to hosted issue trackers that requires no external tooling.

## Layout

```
.scratch/
  <feature-slug>/
    PRD.md
    issues/
      01-setup-database.md
      02-create-api-route.md
```

## Issue file format

Each issue file must have a `Status:` line (first or second line) using one of the canonical triage states:

```markdown
# <title>

Status: needs-triage

## What to build

...

## Acceptance criteria

...
```

Valid status values: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.

## Conventions

- **Create an issue**: Write a new `.md` file under `.scratch/<feature-slug>/issues/`. File names are `NN-<slug>.md` — zero-padded two-digit number, then a short kebab-case slug.
- **Read an issue**: Read the file.
- **List issues**: `ls .scratch/<feature>/issues/`. Optionally `grep -r "Status:" .scratch/ --include="*.md"` to filter by status.
- **Comment on an issue**: Append a `## Comments` section with timestamped subsections to the file.
- **Apply a label / change status**: Edit the `Status:` line.
- **Close**: Set status to `wontfix` with a brief closing note, or delete the file if it was never started.

## When a skill says "publish to the issue tracker"

Write a new issue file.

## When a skill says "fetch the relevant ticket"

Read the file the user points at, or grep `.scratch/` for matching titles.
