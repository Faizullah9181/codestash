---
name: tf-add
description: Create, scaffold, and wire Terraform resources and modules for any cloud provider. Use when adding a new resource, scaffolding a module, connecting outputs across modules, setting up remote state, writing Terraform tests, or building CI/CD pipelines for Terraform/OpenTofu.
license: Apache-2.0
metadata:
  author: codestash
  version: 2.0.0
---

# Terraform Resource Creator

Diagnose-first, workflow-driven skill for creating and wiring Terraform/OpenTofu resources for any cloud provider. Core file is a workflow; depth lives in references loaded on demand.

## Response Contract

Every resource-creation response must include:

1. **Assumptions & version floor** — runtime (`terraform` or `tofu`), version, provider(s), backend, execution path (local/CI/Cloud/Atlantis), environment criticality. State assumptions explicitly.
2. **Task category addressed** — one of: new resource, module scaffold, cross-module wiring, remote state setup, test authoring, CI/CD pipeline, security hardening.
3. **Chosen approach & tradeoffs** — what was generated, what was skipped, why.
4. **Validation plan** — exact commands (`fmt`, `validate`, `plan -out`) tailored to the runtime and risk level.
5. **Rollback notes** — for any destructive or state-mutating change: how to undo, what evidence to preserve.

Never emit an `apply` command without a reviewed plan artifact and explicit environment confirmation.

---

## Workflow

1. **Capture context** — provider(s), runtime + version, backend type, environment criticality (dev / staging / prod).
2. **Classify the task** using the routing table below; load the matching reference file(s).
3. **Scaffold or modify** — generate HCL following naming rules and block-ordering rules.
4. **Wire upward** — expose `id`, `arn`/`urn`/`self_link` from module outputs; consume in parent `locals` and `outputs.tf`.
5. **Apply the feature-flag pattern** for any conditionally created resource.
6. **Validate** — run the validation sequence below before presenting final output.
7. **Emit the Response Contract**.

---

## Routing Table

| Task | Primary Reference |
|------|------------------|
| New resource or module scaffold | [Resource Patterns: Block Ordering](references/resource-patterns.md#block-ordering--structure), [Module Guide: Scaffold](references/module-guide.md#full-module-scaffold) |
| Cross-module wiring / outputs | [Resource Patterns: Output Patterns](references/resource-patterns.md#output-patterns), [Module Guide: Wiring](references/module-guide.md#wiring-into-root) |
| `count` vs `for_each` decision | [Resource Patterns: Count vs For_Each](references/resource-patterns.md#count-vs-for_each) |
| Moved / import blocks (refactor) | [Resource Patterns: Refactoring](references/resource-patterns.md#refactoring-patterns) |
| Provider version pinning | [Resource Patterns: Version Management](references/resource-patterns.md#version-management) |
| Module hierarchy / architecture | [Module Guide: Hierarchy](references/module-guide.md#module-hierarchy) |
| Writing Terraform tests | [Module Guide: Testing](references/module-guide.md#testing-strategy) |
| Secrets, scanning, least-privilege | [Security](references/security.md) |
| Remote backends, locking, recovery | [State Backends](references/state-backends.md) |
| GitHub Actions / GitLab CI / pre-commit | [CI/CD](references/ci-cd.md) |

---

## When to Use This Skill

**Activate when:** creating or extending Terraform/OpenTofu resources or modules for any cloud (AWS, Azure, GCP, DigitalOcean, or any provider), wiring module outputs, setting up remote state, authoring native tests or Terratest, building CI/CD pipelines, applying security or compliance controls to IaC.

**Don't use for:** basic HCL syntax Claude already knows, cloud provider API reference (link to docs), non-Terraform infrastructure questions.

---

## Core Principles

### Module Hierarchy

| Type | When to Use | Scope |
|------|-------------|-------|
| **Resource module** | Single logical group of connected resources | VPC + subnets, SG + rules, DB + firewall rule |
| **Infrastructure module** | Collection of resource modules for a purpose | Complete networking or compute stack |
| **Composition** | Complete environment | Spans multiple infrastructure modules, environment-specific |

Flow: resource → resource module → infrastructure module → composition.

### Directory Layout

```
environments/   # prod/ staging/ dev/ — per-env compositions with backend.tf
modules/        # networking/ compute/ data/ — reusable resource/infrastructure modules
examples/       # minimal/ complete/ — documentation + integration test fixtures
```

Separate **environments** from **modules**. `terraform.tfvars` and `backend.tf` only at composition level, never inside modules. Keep modules single-responsibility.

See [Module Guide](references/module-guide.md) for architecture principles, naming, variable/output contracts, and the anti-pattern list.

### Naming Conventions (summary)

| Element | Rule | Example |
|---------|------|---------|
| Module directory | `lowercase-hyphens` | `modules/managed-db/` |
| Primary resource label | `this` (singletons) | `resource "aws_instance" "this"` |
| Secondary resource label | descriptive | `resource "aws_iam_policy" "read_only"` |
| Variables | `context_attribute` | `vpc_cidr_block`, `db_instance_class` |
| Outputs | `{type}_{attribute}` — no `this_` prefix | `security_group_id`, `private_subnet_ids` |
| Feature flags | `create_<resource>` | `create_database`, `create_nat_gateway` |
| Root config vars | `<resource>_<attr>` | `database_size`, `cluster_version` |

See [Resource Patterns: Naming](references/resource-patterns.md#naming-conventions) for full rules.

### Block Ordering (summary)

Resource blocks: `count`/`for_each` first (blank line after) → arguments (alphabetical or logical) → `tags` → `depends_on` → `lifecycle`.
Variable blocks: `description` → `type` → `default` → `sensitive` → `nullable` → `validation`.

See [Resource Patterns: Block Ordering](references/resource-patterns.md#block-ordering--structure) for full rules and examples.

### Feature Flag Pattern

Every conditionally-created resource uses this pattern:

```hcl
# variables.tf
variable "create_<name>" {
  description = "Set to true to create the <name> resource"
  type        = bool
  default     = false
}

# main.tf
module "<name>" {
  source = "./modules/<name>"
  count  = var.create_<name> ? 1 : 0

  name        = var.<name>_name
  environment = var.environment
  tags        = var.tags
}
```

When a resource depends on another conditionally-created resource, guard with both flags:
```hcl
count = var.create_db && var.create_vpc ? 1 : 0
subnet_ids = module.vpc[0].private_subnet_ids
```

---

## Count vs For_Each — Quick Rule

| Scenario | Use | Why |
|----------|-----|-----|
| Boolean condition (create / don't) | `count = condition ? 1 : 0` | Optional singleton toggle |
| Items may be reordered or removed | `for_each = toset(list)` | Stable resource addresses |
| Reference by named key | `for_each = map` | Named access, no index churn |
| Multiple named resources | `for_each` | Better identity stability |

**Never** use list index as long-lived identity — removing a middle element reshuffles every address. See [Resource Patterns: Count vs For_Each](references/resource-patterns.md#count-vs-for_each) for the full decision matrix and safe migration playbook.

---

## Testing Strategy

| Situation | Approach | Tools | Cost |
|-----------|----------|-------|------|
| Quick syntax check | Static analysis | `validate`, `fmt` | Free |
| Pre-commit validation | Static + lint | `validate`, `tflint`, `trivy`, `checkov` | Free |
| Terraform 1.6+, simple logic | Native test framework | `terraform test` | Free–Low |
| Pre-1.6, or Go expertise available | Integration testing | Terratest | Low–Med |
| Security / compliance focus | Policy as code | OPA, Sentinel | Free |
| Cost-sensitive, mock providers | Native tests + mocks | `terraform test` (1.7+) | Free |

### Native Test Rules (1.6+)

- `command = plan` — for input-derived values only (no computed attributes)
- `command = apply` — required for computed values (ARNs, IPs, generated names) and **set-type** nested blocks
- Set-type blocks cannot be indexed with `[0]` — use `for` expressions or `one()` after `command = apply`

See [Module Guide: Testing](references/module-guide.md#testing-strategy) for full patterns, mock provider examples, and the LLM-mistake checklist.

---

## Validation Sequence

```bash
# 1. Format (non-destructive)
terraform fmt -recursive

# 2. Schema validation (no backend needed)
terraform init -backend=false
terraform validate

# 3. Lint
tflint --init && tflint

# 4. Security scan
trivy config .
checkov -d . --framework terraform

# 5. Plan with saved artifact
terraform plan -var-file=terraform.tfvars -out=tfplan

# 6. Review plan actions
terraform show -json tfplan | jq '.resource_changes[].change.actions'
```

Run in order. Do not `apply` until `validate`, `tflint`, and `plan` are clean.
