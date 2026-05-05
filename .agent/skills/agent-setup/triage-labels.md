# Triage labels

Label mapping for the five canonical triage roles. When a skill says "apply the `ready-for-agent` label", use the string in the right column.

| Role | Label in codestash/skills | Label in this repo |
|---|---|---|
| Maintainer needs to evaluate | `needs-triage` | `needs-triage` |
| Waiting on the reporter for more info | `needs-info` | `needs-info` |
| Fully specified, safe to hand to an agent | `ready-for-agent` | `ready-for-agent` |
| Requires a human to implement | `ready-for-human` | `ready-for-human` |
| Will not be actioned | `wontfix` | `wontfix` |

If the right column differs from the middle column, the skill must use the right-column strings when calling the issue tracker CLI.
