# Domain docs

Instructions for agents that need to understand the project's domain language and architectural history before exploring the codebase.

## Read before exploring

1. **Read `CONTEXT.md` first.** This file defines the domain language, system boundaries, and concepts that name things in the code. Don't assume a term means what it means in the outside world — check `CONTEXT.md` first.
2. **Read `docs/adr/`** for past architectural decisions. ADRs tell you *why* things are the way they are, not just what they are.

Only start reading source code after you've built up domain-context from these files. Use the vocabulary in `CONTEXT.md` when referring to concepts in your output.

## Single-context layout

Used for standalone repos (most repos):

```
repo-root/
  CONTEXT.md         ← primary domain language + system boundary
  docs/
    adr/             ← architectural decision records
      0001-...md
      0002-...md
```

## Multi-context layout

Used for monorepos or repos with multiple bounded contexts:

```
repo-root/
  CONTEXT-MAP.md     ← map of all bounded contexts + pointers to each
  packages/
    auth/
      CONTEXT.md     ← domain language for the auth context
      docs/adr/
    billing/
      CONTEXT.md
      docs/adr/
```

When working on a specific package, read the relevant `CONTEXT.md` and `docs/adr/` for that package. Read `CONTEXT-MAP.md` first to understand the overall layout and how contexts relate to each other.
