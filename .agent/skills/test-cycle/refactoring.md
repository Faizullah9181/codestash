# Refactoring

Refactor only when the test suite is green. Never refactor mid-cycle.

## When to refactor

After every GREEN in the TDD loop, ask: is the implementation clean enough to proceed? If not, refactor now — before the next RED. Don't batch refactors to the end.

Signs that refactoring is warranted:

- **Duplication** — the same logic appears in two or more places
- **Long methods** — a function does more than one conceptual thing
- **Shallow modules** — a wrapper around a single call, no behaviour hidden
- **Feature envy** — a function is more interested in another module's data than its own
- **Primitive obsession** — using strings/numbers where a domain type would add safety and clarity

## How to refactor under tests

1. Run the suite. Confirm it's green.
2. Make one structural change.
3. Run the suite again. Still green?
4. Commit or continue.

Never make a structural change and a behavioural change in the same step. If both are needed, do the structural change first, confirm green, then do the behavioural change.

## Refactoring is not adding features

If you notice a missing feature while refactoring, add it to the test plan and implement it in the next RED cycle. Don't extend behaviour while refactoring.
