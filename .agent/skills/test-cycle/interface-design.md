# Interface Design for Testability

How to design interfaces so that:
- Tests stay at the interface, not the implementation
- The interface survives refactors
- Dependencies are injected, not reached for

## Principles

### Accept dependencies, don't reach for them

Bad:
```typescript
class UserService {
  async getUser(id: string) {
    const db = new Database()      // ← reached for
    return db.findUser(id)
  }
}
```

Good:
```typescript
class UserService {
  constructor(private db: UserRepository) {}  // ← injected

  async getUser(id: string) {
    return this.db.findUser(id)
  }
}
```

The second form is testable without mocking module internals.

### Return results, don't produce side effects in helpers

A function that returns a value is easy to test. A function that mutates state is harder. Push side effects to the edge.

### Keep the surface area small

Every parameter, method, and overload is something the test has to know about. Fewer entry points = more leverage per test.

## Testing through the interface

Tests should construct the module under test with real (or fake) dependencies, call it through its interface, and assert on observable outputs.

```typescript
// Good: test through the interface
const service = new UserService(new InMemoryUserRepository())
const user = await service.getUser("123")
expect(user.name).toBe("Alice")

// Bad: test the implementation detail
const spy = jest.spyOn(db, "findUser")
await service.getUser("123")
expect(spy).toHaveBeenCalledWith("123")
```

The spy test breaks when you rename the internal method or swap the DB library. The interface test doesn't.
