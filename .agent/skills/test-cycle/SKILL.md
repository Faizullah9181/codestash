---
name: test-cycle
description: Guides test-driven development using a philosophy of testing through public interfaces rather than internal implementations. Enforces planning, tracer-bullet approach, and incremental RED-GREEN-REFACTOR cycles. Use when writing new features with tests, when tests are entangled with implementations (mocking internal details), or when asked to add tests to existing code.
---

# TDD

Tests should be written through public interfaces, not internal implementations. That means they should test **behaviour** (what the module does), not **implementation** (how the module does it). Tests written through internal seams become a liability: they prevent refactoring and give false confidence.

## Philosophy

- Tests live at the **interface**. They exercise the module from the outside, exactly as a caller would.
- Tests should survive internal refactors. If a test has to change when the implementation changes, the test is testing the wrong thing.
- Test at the **deepest** interface available. Don't test the controller if you can test the service. Don't test the service if you can test a pure function.
- Mocks belong at **system boundaries** — databases, external APIs, time, filesystem. Never mock internal modules. See [mocking.md](mocking.md).
- The goal of TDD is **good interfaces**, not "tests first". The discipline of writing the test first is a forcing function — it ensures you design the interface before you implement it.

See [interface-design.md](interface-design.md), [mocking.md](mocking.md), [tests.md](tests.md).

## Anti-pattern: horizontal slices

Don't ask the user "what layer do you want tests for?" and work layer by layer (controller tests, service tests, repository tests). That's the old way. It produces:

- Tests that duplicate each other across layers
- Tests that mock internal seams (controller mocks service, service mocks repository)
- A test suite that prevents refactoring

Instead, write one test at the highest useful interface that still lets you make progress. That test covers all the layers below it.

## Workflow

### 1. Planning phase (HITL)

Before writing any code, confirm with the user:

1. **What is the interface?** — method signature, inputs, outputs, error modes. If the interface doesn't exist yet, design it now. See [interface-design.md](interface-design.md).
2. **What are the behaviours?** — enumerate the distinct behaviour cases to test (happy path, edge cases, error cases). Be specific: "returns empty list when no items match" is a behaviour; "handles edge cases" is not.
3. **What is the test plan?** — show the user the ordered list of test cases before writing any. Get sign-off.

Don't proceed until you have explicit answers to all three.

### 2. Tracer bullet (first RED → GREEN)

Write the **simplest possible test** for the most central behaviour. Run it. It must fail (RED). Then write the minimum implementation to make it pass (GREEN).

This proves:
- The test harness is wired up correctly
- The interface is callable
- The basic path works end-to-end

Don't implement more than needed. The tracer bullet should take 5–10 minutes max.

### 3. Incremental loop

For each remaining test case in the plan:

```
RED   → write the test; confirm it fails for the right reason
GREEN → write minimum code to pass
CHECK → run the full suite; all tests green?
```

After each GREEN, check if a refactor is warranted before the next RED. Short cycles. Don't batch.

### 4. Refactor phase

Once all test cases are green, review the implementation for duplication, shallow modules, long methods, and feature envy. See [refactoring.md](refactoring.md). Refactor only when the suite is green — never mid-cycle.

## Per-cycle checklist

- [ ] Test is at the public interface, not an internal seam
- [ ] Test asserts on behaviour (output / effect), not on how it was produced
- [ ] Test name describes the behaviour: `returns_empty_list_when_no_match`, not `test_method_1`
- [ ] Mocks are only at system boundaries (DB, external API, time, filesystem)
- [ ] No mocks of internal modules
- [ ] Test fails for the right reason (RED) before implementing
