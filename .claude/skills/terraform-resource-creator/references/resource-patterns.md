# Resource Patterns & Code Structure

> **Part of:** [terraform-resource-creator](../SKILL.md)
> **Purpose:** Canonical HCL patterns — block ordering, naming, count/for_each, outputs, modern features, and common LLM mistakes.

---

## Table of Contents

1. [Block Ordering & Structure](#block-ordering--structure)
2. [Naming Conventions](#naming-conventions)
3. [Count vs For_Each](#count-vs-for_each)
4. [Output Patterns](#output-patterns)
5. [Version Management](#version-management)
6. [Refactoring Patterns](#refactoring-patterns)
7. [Modern Terraform Features (1.x)](#modern-terraform-features-1x)
8. [LLM Mistake Checklist](#llm-mistake-checklist)

---

## Block Ordering & Structure

### Resource Block — strict ordering

```hcl
# ✅ GOOD
resource "aws_nat_gateway" "this" {
  count = var.create_nat_gateway ? 1 : 0    # ← FIRST, blank line after

  allocation_id = aws_eip.this[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(var.tags, {
    Name = "${var.name}-nat"
  })

  depends_on = [aws_internet_gateway.this]  # ← after tags

  lifecycle {                               # ← very last
    create_before_destroy = true
  }
}
```

Order:
1. `count` or `for_each` — always first, blank line separating it from rest
2. Required arguments — alphabetical or logical grouping
3. Optional arguments
4. `tags` — last real argument
5. `depends_on` — after tags, only when Terraform can't infer the dependency
6. `lifecycle` — absolutely last

### Variable Block — strict ordering

```hcl
# ✅ GOOD
variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
  default     = "dev"
  nullable    = false

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be one of: dev, staging, prod."
  }
}
```

Order: `description` → `type` → `default` → `sensitive` → `nullable` → `validation`

Always include `description`. Never skip `type`.

### Locals Block

Group logically, comment each group:

```hcl
locals {
  # Computed names
  name_prefix = "${var.project}-${var.environment}"
  bucket_name = "${local.name_prefix}-assets"

  # Conditional resource attributes
  vpc_id = var.create_vpc ? module.vpc[0].vpc_id : var.existing_vpc_id

  # Shared tags applied to all resources
  common_tags = merge(var.tags, {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}
```

---

## Naming Conventions

| Element | Rule | ✅ Good | ❌ Bad |
|---------|------|---------|--------|
| Module directory | `lowercase-hyphens` | `modules/managed-db/` | `modules/ManagedDB/` |
| Primary resource label | `this` for singleton | `aws_instance.this` | `aws_instance.main` |
| Secondary resource label | descriptive | `aws_iam_policy.read_only` | `aws_iam_policy.policy2` |
| Variables | `context_attribute` — no bare words | `vpc_cidr_block`, `db_engine` | `cidr`, `engine` |
| Outputs | `{type}_{attribute}` — omit `this_` | `security_group_id` | `this_security_group_id` |
| Plural outputs | use plural for lists | `private_subnet_ids` | `private_subnet_id` |
| Feature flags | `create_<resource>` | `create_database` | `database_enabled` |

**Reserve `this` for genuine singletons only.** If a module will ever manage two instances of the same resource type, use descriptive labels from the start.

---

## Count vs For_Each

### Decision Matrix

| Scenario | Use | Why |
|----------|-----|-----|
| Boolean — create or skip | `count = condition ? 1 : 0` | Minimal, expressive toggle |
| Simple numeric replication, order matters | `count = N` | Fine for fixed-size arrays |
| Items may be added/removed from middle | `for_each = toset(list)` | Stable resource addresses |
| Reference resource by name | `for_each = map` | Key-based access |
| Multiple configs from a map variable | `for_each = var.config_map` | One resource per map entry |

### Identity Churn — the core risk

```hcl
# ❌ BAD — remove middle item, all subsequent resources recreate
resource "aws_subnet" "private" {
  count             = length(var.azs)
  availability_zone = var.azs[count.index]
}
# var.azs = ["a","b","c"] → remove "b" → "c" is now index 1, forces replace

# ✅ GOOD — remove any key, only that subnet is destroyed
resource "aws_subnet" "private" {
  for_each          = toset(var.azs)
  availability_zone = each.key
}
```

### Safe Migration: count → for_each

```hcl
# Add moved blocks to avoid destroy/recreate
moved {
  from = aws_subnet.private[0]
  to   = aws_subnet.private["us-east-1a"]
}
moved {
  from = aws_subnet.private[1]
  to   = aws_subnet.private["us-east-1b"]
}
```

After applying, remove the `moved` blocks.

### Cross-module count guards

When a child module depends on a conditionally-created parent:
```hcl
module "db_firewall" {
  source = "./modules/db-firewall"
  count  = var.create_database && var.create_vpc ? 1 : 0

  db_cluster_id = module.database[0].id
  vpc_id        = module.vpc[0].vpc_id
}
```

---

## Output Patterns

### Module outputs — minimum required

Every module must export at minimum: `id` + the cloud-specific identifier (`arn`, `urn`, `self_link`).

```hcl
output "id" {
  description = "Resource ID"
  value       = aws_instance.this.id
}

output "arn" {
  description = "Resource ARN"
  value       = aws_instance.this.arn
}

output "private_ip" {
  description = "Private IP address"
  value       = aws_instance.this.private_ip
}
```

### Sensitive outputs

```hcl
output "db_uri" {
  description = "Database connection URI"
  value       = aws_db_instance.this.endpoint
  sensitive   = true
}
```

### try() for optional resources

```hcl
# Root outputs.tf — safe access for feature-flagged modules
output "nat_gateway_id" {
  description = "NAT gateway ID, or null if not created"
  value       = try(module.nat_gateway[0].id, null)
}
```

### Output naming pattern

`{resource_type}_{attribute}` — never prefix with `this_`:

```hcl
output "security_group_id"    { ... }   # ✅
output "private_subnet_ids"   { ... }   # ✅ — plural for lists
output "this_security_group"  { ... }   # ❌
output "subnet_id"            { ... }   # ❌ — ambiguous singular
```

---

## Version Management

### Provider version constraints

```hcl
terraform {
  required_version = ">= 1.6.0"   # minimum tested version

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"          # allows patch bumps, blocks major
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0, < 4.0"   # explicit upper bound for breaking changes
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.68"
    }
  }
}
```

### Rules

- **Modules**: use `>=` lower-bound only — let the composition pin the exact version
- **Compositions / root**: use `~> X.Y` (pessimistic constraint) to allow patch upgrades
- Pin in `.terraform.lock.hcl` — always commit this file
- Never use `version = "latest"` or omit version entirely

### Lockfile management

```bash
# Update all providers to latest allowed versions
terraform init -upgrade

# Re-generate lockfile for multiple platforms (CI runs on linux)
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_amd64 \
  -platform=darwin_arm64
```

---

## Refactoring Patterns

### Moved blocks (Terraform 1.1+)

Use when renaming a resource or moving it into/out of a module — avoids destroy + recreate.

```hcl
# Rename resource
moved {
  from = aws_security_group.main
  to   = aws_security_group.this
}

# Extract into module
moved {
  from = aws_instance.app
  to   = module.compute.aws_instance.this
}
```

Remove `moved` blocks after the state migration is applied and verified.

### Import blocks (Terraform 1.5+)

Bring existing cloud resources under Terraform management:

```hcl
import {
  to = aws_vpc.this
  id = "vpc-0a1b2c3d4e5f"
}
```

Generate the matching configuration from the import:
```bash
terraform plan -generate-config-out=imported.tf
# Review imported.tf, clean up, then apply
```

### removed block (Terraform 1.7+)

Remove a resource from state without destroying the real infrastructure:

```hcl
removed {
  from = aws_instance.legacy

  lifecycle {
    destroy = false
  }
}
```

---

## Modern Terraform Features (1.x)

### Write-only arguments (1.11+)

Keeps sensitive values out of state:

```hcl
resource "aws_db_instance" "this" {
  identifier     = var.name
  engine         = "postgres"
  instance_class = var.instance_class

  password_wo         = var.db_password       # write-only: never stored in state
  password_wo_version = var.db_password_version  # bump to rotate
}
```

### Ephemeral resources (1.10+)

Values exist only in memory during the apply — never written to state:

```hcl
ephemeral "aws_secretsmanager_secret_version" "db_creds" {
  secret_id = "prod/database/credentials"
}

resource "aws_db_instance" "this" {
  password = ephemeral.aws_secretsmanager_secret_version.db_creds.secret_string
}
```

### optional() in object variables (1.3+)

```hcl
variable "database_config" {
  description = "Database configuration"
  type = object({
    name             = string
    engine           = string
    instance_class   = string
    backup_retention = optional(number, 7)
    deletion_protection = optional(bool, true)
    tags             = optional(map(string), {})
  })
}
```

### check blocks (1.5+)

Post-apply assertions that do not block apply:

```hcl
check "health_check" {
  data "http" "app" {
    url = "https://${aws_lb.this.dns_name}/health"
  }

  assert {
    condition     = data.http.app.status_code == 200
    error_message = "Application health check failed"
  }
}
```

---

## LLM Mistake Checklist

Before finalizing any generated HCL, verify:

- [ ] `count`/`for_each` is FIRST in resource blocks, not buried in the middle
- [ ] `depends_on` is NOT used where Terraform can infer dependency from attribute reference
- [ ] `for_each` used instead of `count` for any list that users may reorder or remove from
- [ ] `moved` blocks added whenever a resource is renamed or module-extracted
- [ ] `import` blocks used (not `terraform import` CLI) for any existing resource
- [ ] Output names don't start with `this_`
- [ ] Plural output names for list/set values
- [ ] Sensitive values marked `sensitive = true` in outputs
- [ ] No secrets in variable `default` values
- [ ] Provider versions pinned with `~>` not `>=` in compositions
- [ ] `terraform.tfvars` and `backend.tf` only at composition level, never in modules
- [ ] `README.md` exists in every published module
