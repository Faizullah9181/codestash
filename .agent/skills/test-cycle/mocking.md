# Mocking

Mock only at **system boundaries**. Everything inside the system should run for real.

## What is a system boundary?

A system boundary is a place where your code crosses into something you don't own and can't run in a test cheaply or deterministically:

- **External HTTP APIs** (Stripe, SendGrid, Twilio, etc.)
- **Databases** — unless you have a local substitute (PGLite, in-memory SQLite, etc.)
- **Time** (`Date.now()`, `new Date()`, `datetime.now()`)
- **Filesystem** (when testing business logic, not I/O helpers)
- **Message queues / event buses** (external ones)
- **Random number generators**

## What is NOT a system boundary?

- Internal modules (services, repositories, helpers within the codebase)
- Framework code you own (your own middleware, adapters)
- A database you can run locally in tests (use a local substitute instead of a mock)

## Anti-patterns

### Mocking internal modules

```typescript
// Bad: mocks an internal seam
jest.mock("./userRepository")
const repo = require("./userRepository")
repo.findUser.mockResolvedValue({ id: "1", name: "Alice" })
```

This test will pass even if `UserService` is completely broken, as long as it calls `findUser`. The mock is testing the wiring, not the behaviour.

### Mocking to avoid a hard-to-test interface

If you need to mock an internal module to make something testable, the interface is wrong. Redesign the interface (see [interface-design.md](interface-design.md)) instead of adding a mock.

## How to handle each boundary type

| Boundary | Approach |
|---|---|
| External HTTP API | Mock the HTTP client at the transport layer (e.g. `nock`, `httpretty`, `respx`) or use a local server fixture |
| Database (no local substitute) | Mock the repository interface (port), not the DB driver |
| Database (has local substitute) | Run the substitute in tests, no mock needed |
| Time | Inject a clock interface; tests provide a fixed clock |
| Filesystem | Inject a filesystem interface; tests provide an in-memory implementation |
| RNG | Inject a seed or a function |
