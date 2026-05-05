---
name: skill-scaffold
description: Creates a new agent skill — a SKILL.md with required frontmatter plus optional reference files (REFERENCE.md, EXAMPLES.md, scripts/). Gathers requirements from the user, drafts the skill, and reviews it against the description constraints. Use when the user wants to create a reusable agent skill, save a workflow as a skill, or add a new skill to this repo.
---

# Write a Skill

Create a new skill in `.agent/skills/`.

## 1. Gather requirements

Ask the user:
1. What does the skill do? (One sentence.)
2. When should it trigger? (What phrases, contexts, or situations?)
3. Does it need reference files, examples, or scripts?
4. Should it disable model invocation? (Is it a mode-switch with no procedure to follow?)

## 2. Draft

A skill is a directory under `.agent/skills/<skill-name>/` containing:

**Required: `SKILL.md`**

Frontmatter:
```yaml
---
name: <skill-name>            # required: kebab-case, matches the directory name
description: <description>   # required: see constraints below
disable-model-invocation: true  # optional: set for mode-switch skills only
---
```

Description constraints:
- Maximum 1024 characters
- Third person ("Guides...", "Creates...", "Converts...")
- Says what it does
- Includes "Use when [triggers]" — the situations that should invoke this skill

**Optional:**
- `REFERENCE.md` — domain knowledge, terminology, principles the skill should apply
- `EXAMPLES.md` — concrete examples of inputs/outputs
- `scripts/` — shell scripts or other executables the skill uses

## 3. Review

Before writing:
- Check the description is under 1024 characters
- Check the `name` matches the directory name
- Check the `Use when` clause covers the triggers the user described
- Check that any reference files are linked from `SKILL.md`

Then write the files.
