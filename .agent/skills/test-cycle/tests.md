# Tests

What good tests look like vs. bad tests. Use this as a reference when reviewing or writing tests.

## Good tests

### Integration-style: test through the public interface

```typescript
// Good: constructs the real module, tests through the interface
const service = new OrderService(new InMemoryOrderRepository(), new FakePricingAPI())
const order = await service.placeOrder({ items: ["A", "B"], userId: "u1" })
expect(order.status).toBe("confirmed")
expect(order.total).toBe(150)
```

- Tests observable behaviour
- Survives internal refactors
- No knowledge of internal structure

### Behaviour-not-implementation names

```
✓ returns_empty_list_when_no_orders_exist
✓ rejects_order_when_item_out_of_stock
✓ applies_discount_for_premium_users
✗ test_place_order
✗ test_method_1
✗ it_works
```

### One behaviour per test

Each test case should be falsifiable by exactly one bug. If removing one line of production code makes three tests fail, either the tests overlap or the line is doing three things.

## Bad tests

### Mocking internal modules

```typescript
// Bad: mocks an internal seam
const mockRepo = { save: jest.fn(), findById: jest.fn() }
const service = new OrderService(mockRepo)
await service.placeOrder(...)
expect(mockRepo.save).toHaveBeenCalledWith(expect.objectContaining({ status: "confirmed" }))
```

This test couples to `OrderService`'s implementation. If you change the internal call from `.save()` to `.upsert()`, the test breaks even though the behaviour is unchanged.

### Testing private methods

Private methods are implementation details. If a private method needs its own test, that's a sign it should be extracted into its own module with a public interface.

### Over-specified mocks

```typescript
// Bad: asserts on call counts and exact arguments of internal calls
expect(emailSender.send).toHaveBeenCalledTimes(1)
expect(emailSender.send).toHaveBeenCalledWith("alice@example.com", "Your order is confirmed", expect.any(String))
```

Better: assert on the observable effect (did the email arrive? does the order have status "notified"?) and let the implementation decide how.
