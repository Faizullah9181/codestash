# State Backends

> **Part of:** [terraform-resource-creator](../SKILL.md)
> **Purpose:** Remote backend setup, state locking, workspace isolation, migration, recovery, and cross-stack data sharing patterns.

---

## Table of Contents

1. [Backend Principles](#backend-principles)
2. [AWS S3 Backend](#aws-s3-backend)
3. [Azure Blob Backend](#azure-blob-backend)
4. [GCS Backend](#gcs-backend)
5. [Terraform Cloud / HCP Terraform](#terraform-cloud--hcp-terraform)
6. [State Locking](#state-locking)
7. [Workspaces vs. Directories](#workspaces-vs-directories)
8. [State Migration](#state-migration)
9. [State Recovery & Repair](#state-recovery--repair)
10. [Cross-Stack Data Sharing](#cross-stack-data-sharing)
11. [LLM Mistake Checklist](#llm-mistake-checklist)

---

## Backend Principles

1. **Never use local backend in team environments or production** — local state is deleted when the workspace is lost and cannot be locked.
2. **State must be encrypted at rest** — use server-side encryption on all remote backends.
3. **Enable versioning** — allows rollback to pre-bad-apply state.
4. **Enable locking** — prevents concurrent applies from corrupting state.
5. **Restrict access** — state contains secrets; IAM access should be least-privilege.
6. **Backend config belongs only in compositions** — never in modules.

---

## AWS S3 Backend

### Infrastructure (bootstrapped separately)

```hcl
# bootstrap/main.tf — run once, manage manually
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-terraform-state-${var.account_id}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.terraform_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Locking — DynamoDB (Terraform < 1.10)
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
```

### Backend configuration (Terraform < 1.10)

```hcl
# environments/prod/backend.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-123456789012"
    key            = "prod/main/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/mrk-abc123"
    dynamodb_table = "terraform-locks"
  }
}
```

### Backend configuration (Terraform 1.10+ — native locking)

```hcl
# environments/prod/backend.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-123456789012"
    key            = "prod/main/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/mrk-abc123"
    use_lockfile   = true          # replaces DynamoDB — requires versioning enabled
  }
}
```

### Key naming convention

```
{environment}/{service}/{terraform.tfstate}
# Examples:
prod/networking/terraform.tfstate
prod/compute/terraform.tfstate
staging/networking/terraform.tfstate
dev/compute/terraform.tfstate
```

### Backend init with partial config (recommended for CI)

```hcl
# backend.tf — empty block, config injected at init
terraform {
  backend "s3" {}
}
```

```bash
terraform init \
  -backend-config="bucket=my-terraform-state-123456789012" \
  -backend-config="key=prod/main/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="encrypt=true" \
  -backend-config="dynamodb_table=terraform-locks"
```

---

## Azure Blob Backend

### Infrastructure

```hcl
resource "azurerm_resource_group" "state" {
  name     = "rg-terraform-state"
  location = var.location
}

resource "azurerm_storage_account" "state" {
  name                     = "tfstate${var.environment}${var.suffix}"
  resource_group_name      = azurerm_resource_group.state.name
  location                 = azurerm_resource_group.state.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  min_tls_version          = "TLS1_2"

  blob_properties {
    versioning_enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_storage_container" "state" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.state.name
  container_access_type = "private"
}
```

### Backend configuration

```hcl
# environments/prod/backend.tf
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "tfstateprod12345"
    container_name       = "tfstate"
    key                  = "prod/main/terraform.tfstate"
    use_oidc             = true   # workload identity federation in CI
  }
}
```

Locking is automatic — Azure Blob provides native lease-based locking.

---

## GCS Backend

### Infrastructure

```hcl
resource "google_storage_bucket" "terraform_state" {
  name          = "my-terraform-state-${var.project_id}"
  location      = var.region
  force_destroy = false

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true

  lifecycle_rule {
    action { type = "Delete" }
    condition { num_newer_versions = 10 }  # keep last 10 versions
  }
}
```

### Backend configuration

```hcl
# environments/prod/backend.tf
terraform {
  backend "gcs" {
    bucket = "my-terraform-state-my-project-id"
    prefix = "prod/main"
  }
}
```

Locking is automatic via GCS object locks.

---

## Terraform Cloud / HCP Terraform

```hcl
terraform {
  cloud {
    organization = "my-org"

    workspaces {
      name = "myapp-prod"
      # OR use tags for dynamic workspace selection:
      # tags = ["prod", "aws"]
    }
  }
}
```

HCP Terraform provides locking, versioning, remote execution, and secret injection (workspace variables) automatically.

---

## State Locking

### Why locking matters

Without locking, two concurrent `apply` operations can corrupt state by writing conflicting resource metadata.

### Stuck lock

When a lock is left by a crashed process:

```bash
# List current lock
terraform force-unlock --help

# Force-unlock (get lock ID from error message)
terraform force-unlock LOCK_ID

# Confirm before running
terraform plan -out=tfplan
```

⚠️ Only force-unlock when you are certain no other apply is actually in progress.

---

## Workspaces vs. Directories

### When to use workspaces

Workspaces share the **same backend, same code** — only state is isolated. Use for:
- Ephemeral feature-branch environments with identical infrastructure topology
- Quick test environments that match production config exactly

```bash
terraform workspace new feature-payments
terraform workspace list
terraform workspace select prod
```

### When to use directories (preferred)

Use separate directories under `environments/` for:
- **Prod / staging / dev** — often different sizes, flags, policies
- **Different regions** — different backends
- **Different teams** — different access controls on state

Directory per environment is the safe default. Workspaces add complexity and accidental prod-applies risk.

---

## State Migration

### Local → remote

```bash
# 1. Add backend.tf with remote config
# 2. Re-init — Terraform will ask to copy state
terraform init

# Terraform will prompt:
# "Do you want to copy existing state to the new backend?"
# Answer: yes
```

### Remote → different remote

```bash
# 1. Update backend.tf with new config
terraform init -migrate-state

# Terraform will prompt to confirm migration
```

### Manual state copy (when init migration fails)

```bash
# Pull state to file
terraform state pull > terraform.tfstate.backup

# Update backend.tf
# Re-init
terraform init

# Push the state file
terraform state push terraform.tfstate.backup
```

---

## State Recovery & Repair

### Roll back to previous state version

**AWS S3:**
```bash
# List versions
aws s3api list-object-versions \
  --bucket my-terraform-state \
  --prefix prod/main/terraform.tfstate

# Restore specific version
aws s3api copy-object \
  --bucket my-terraform-state \
  --copy-source "my-terraform-state/prod/main/terraform.tfstate?versionId=VERSION_ID" \
  --key prod/main/terraform.tfstate
```

### Remove a resource from state (stop managing it)

```bash
# List all resources in state
terraform state list

# Remove without destroying
terraform state rm aws_instance.legacy_app

# Or use removed block (Terraform 1.7+, preferred)
removed {
  from = aws_instance.legacy_app
  lifecycle { destroy = false }
}
```

### Rename / move in state

```bash
# Before Terraform 1.1 (CLI)
terraform state mv module.old_name.aws_instance.this module.new_name.aws_instance.this

# Terraform 1.1+ (preferred — declarative, reviewed in plan)
moved {
  from = module.old_name.aws_instance.this
  to   = module.new_name.aws_instance.this
}
```

### Import existing resource (Terraform 1.5+ blocks — preferred)

```hcl
import {
  to = aws_vpc.this
  id = "vpc-0a1b2c3d"
}
```

```bash
# Generate config from import
terraform plan -generate-config-out=generated.tf
# Review generated.tf, clean up, then apply
terraform apply
```

---

## Cross-Stack Data Sharing

### Remote state data source

```hcl
data "terraform_remote_state" "networking" {
  backend = "s3"
  config = {
    bucket = "my-terraform-state"
    key    = "prod/networking/terraform.tfstate"
    region = "us-east-1"
  }
}

# Consume
module "compute" {
  source     = "./modules/compute"
  vpc_id     = data.terraform_remote_state.networking.outputs.vpc_id
  subnet_ids = data.terraform_remote_state.networking.outputs.private_subnet_ids
}
```

**Use sparingly** — creates tight coupling between stacks. Prefer:
1. Module composition (same root, same team)
2. Cloud-managed lookups (`data "aws_vpc"` by tag) for loosely-coupled teams

### Cloud resource lookup (preferred for cross-team)

```hcl
# Look up by tag — no state coupling
data "aws_vpc" "shared" {
  tags = {
    Name        = "shared-vpc-${var.environment}"
    ManagedBy   = "networking-team"
  }
}
```

---

## LLM Mistake Checklist

- [ ] `backend.tf` is at composition / environment level only — never inside modules
- [ ] `terraform.tfvars` is at composition level only
- [ ] Backend has encryption enabled (`encrypt = true` for S3)
- [ ] Backend bucket has versioning enabled
- [ ] Locking configured (DynamoDB for S3 < 1.10, `use_lockfile = true` for S3 ≥ 1.10)
- [ ] State bucket blocks all public access
- [ ] `prevent_destroy = true` on state bucket
- [ ] Never use `terraform workspace` for prod/staging/dev — use directories
- [ ] `terraform_remote_state` only at true ownership boundaries, not just because it's convenient
- [ ] State migration uses `terraform init -migrate-state` or `state pull` + `state push`, not manual file copy
- [ ] `moved` blocks used for renames (not `terraform state mv` which leaves no record)
