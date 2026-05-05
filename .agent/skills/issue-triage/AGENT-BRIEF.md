# AGENT-BRIEF spec

The AGENT-BRIEF format is the target output for triage. An issue that meets this spec is safe to assign to an agent with no further clarification needed.

## Principles

- **Durable**: no file paths, no line numbers. The codebase changes; the brief should survive a refactor.
- **Behavioural, not procedural**: describes what the system should do, not how to do it. Don't specify implementation steps.
- **Complete acceptance criteria**: every criterion is independently verifiable. "Works correctly" is not verifiable. "Returns HTTP 400 when the email field is missing" is.
- **Explicit scope**: names what is explicitly out of scope to prevent scope creep.

## Template

```markdown
**Category**: Bug | Enhancement

**Summary**

One sentence: what the issue is about.

**Current behaviour** (bugs only)

What happens now, described behaviourally.

**Desired behaviour**

What should happen instead, described behaviourally.

**Key interfaces**

The module, endpoint, or UI surface where this change lives (by name/concept, not file path).

**Acceptance criteria**

- [ ] <verifiable criterion — observable from the outside>
- [ ] <verifiable criterion>

**Out of scope**

- <explicitly excluded>
```

## Good vs bad examples

### Summary

❌ `Fix the bug in UserService.processPayment() on line 42`
✅ `Payment processing fails when a coupon code is applied to a subscription`

### Acceptance criteria

❌ `The payment flow works with coupons`
✅ `Applying a valid coupon code reduces the checkout total by the specified percentage`
✅ `Applying an expired coupon code returns a 422 with the message "Coupon has expired"`
✅ `Applying a coupon code to a free-tier subscription has no effect on the total`

### Key interfaces

❌ `src/services/payment/PaymentService.ts`
✅ `The payment service's checkout interface`
