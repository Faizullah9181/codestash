# Deep Modules

A module is **deep** when its interface is small relative to its implementation. Depth is the property to optimise for. Leverage and locality are why.

```
┌─────────────────────────────────────────────────┐
│                  interface                       │  ← small
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                                                 │
│                                                 │
│               implementation                   │  ← large
│                                                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

A module is **shallow** when the interface is nearly as large as the implementation. The caller gains almost nothing.

```
┌─────────────────────────────────────────────────┐
│              interface (large)                  │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│           implementation (small)                │
└─────────────────────────────────────────────────┘
```

## Depth is good

- **Leverage**: callers exercise a large amount of behaviour per unit of interface they learn.
- **Locality**: when behaviour changes, there is one place to change it — not N call sites.

## The deletion test

Imagine deleting the module. If the complexity vanishes, the module earned its keep. If the complexity reappears at N call sites, it was a pass-through.

## Signs of a shallow module

- The interface is a thin wrapper around a single library call
- Callers frequently chain the module with another to get anything useful
- Unit tests of the module feel trivial; the "real" test is always somewhere above it
- Renaming the module's concept would require changes in callers (the abstraction leaked)
