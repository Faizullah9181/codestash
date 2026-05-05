# CI/CD Pipelines

> **Part of:** [terraform-resource-creator](../SKILL.md)
> **Purpose:** GitHub Actions, GitLab CI, and pre-commit pipelines for Terraform/OpenTofu. Provider-agnostic.

---

## Table of Contents

1. [Pipeline Stages](#pipeline-stages)
2. [GitHub Actions — Full Pipeline](#github-actions--full-pipeline)
3. [GitHub Actions — Atlantis Alternative](#github-actions--atlantis-alternative)
4. [GitLab CI](#gitlab-ci)
5. [Pre-Commit Hooks](#pre-commit-hooks)
6. [Infracost Integration](#infracost-integration)
7. [OpenTofu Notes](#opentofu-notes)
8. [LLM Mistake Checklist](#llm-mistake-checklist)

---

## Pipeline Stages

Every Terraform CI pipeline must run these stages in order:

| Stage | Jobs | Blocks Deploy |
|-------|------|---------------|
| Validate | `fmt`, `validate`, `tflint` | Yes (on failure) |
| Security | `trivy`, `checkov` | Yes (configurable) |
| Plan | `terraform plan -out=tfplan` | Yes (on error) |
| Cost (optional) | `infracost` | No (advisory) |
| Apply | `terraform apply tfplan` | Requires approval (prod) |

**Golden rule:** Apply consumes the artifact produced by Plan. Never re-plan at apply time.

---

## GitHub Actions — Full Pipeline

### Validate + Plan workflow (`terraform-validate.yml`)

```yaml
# .github/workflows/terraform-validate.yml
name: Terraform Validate & Plan

on:
  pull_request:
    paths:
      - 'terraform/**'
      - '.github/workflows/terraform-*.yml'

permissions:
  contents: read
  pull-requests: write          # for plan comment on PR
  id-token: write               # for OIDC authentication

env:
  TF_VERSION: "1.9.0"
  WORKING_DIR: terraform/environments/prod

jobs:
  validate:
    name: Validate
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIR }}

    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      # OIDC auth — no long-lived secrets (AWS example)
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ vars.AWS_ACCOUNT_ID }}:role/github-actions-terraform
          aws-region: us-east-1

      - name: Terraform Format Check
        run: terraform fmt -recursive -check

      - name: Terraform Init
        run: terraform init -backend=false

      - name: Terraform Validate
        run: terraform validate

      - name: tflint
        uses: terraform-linters/setup-tflint@v4
        with:
          tflint_version: latest

      - run: tflint --init && tflint --format compact

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: validate

    steps:
      - uses: actions/checkout@v4

      - name: trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: config
          scan-ref: terraform/
          severity: HIGH,CRITICAL
          exit-code: '1'
          format: sarif
          output: trivy-results.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-results.sarif

  plan:
    name: Plan
    runs-on: ubuntu-latest
    needs: [validate, security]
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIR }}

    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ vars.AWS_ACCOUNT_ID }}:role/github-actions-terraform
          aws-region: us-east-1

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        id: plan
        run: terraform plan -var-file=terraform.tfvars -out=tfplan -no-color

      - name: Upload plan artifact
        uses: actions/upload-artifact@v4
        with:
          name: tfplan-${{ github.sha }}
          path: ${{ env.WORKING_DIR }}/tfplan
          retention-days: 7

      - name: Comment plan on PR
        uses: actions/github-script@v7
        if: github.event_name == 'pull_request'
        with:
          script: |
            const output = `#### Plan: \`${{ steps.plan.outcome }}\`

            <details><summary>Show Plan</summary>

            \`\`\`hcl
            ${{ steps.plan.outputs.stdout }}
            \`\`\`

            </details>

            *Triggered by: @${{ github.actor }}, SHA: \`${{ github.sha }}\`*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });
```

### Apply workflow (`terraform-apply.yml`)

```yaml
# .github/workflows/terraform-apply.yml
name: Terraform Apply

on:
  push:
    branches: [main]
    paths:
      - 'terraform/**'

permissions:
  contents: read
  id-token: write

env:
  TF_VERSION: "1.9.0"
  WORKING_DIR: terraform/environments/prod

jobs:
  apply:
    name: Apply
    runs-on: ubuntu-latest
    environment: production          # requires manual approval in GitHub Environments
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIR }}

    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ vars.AWS_ACCOUNT_ID }}:role/github-actions-terraform-apply
          aws-region: us-east-1

      - name: Terraform Init
        run: terraform init

      - name: Download plan artifact
        uses: actions/download-artifact@v4
        with:
          name: tfplan-${{ github.sha }}
          path: ${{ env.WORKING_DIR }}

      - name: Terraform Apply
        run: terraform apply -auto-approve tfplan
```

### OIDC trust policy (AWS — one-time bootstrap)

```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions_terraform" {
  name = "github-actions-terraform"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:my-org/my-repo:*"
        }
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}
```

---

## GitHub Actions — Atlantis Alternative

For teams using Atlantis (PR-based autoplan/apply):

```yaml
# atlantis.yaml
version: 3
automerge: false
delete_source_branch_on_merge: false

projects:
  - name: prod
    dir: terraform/environments/prod
    workspace: default
    autoplan:
      when_modified: ["**/*.tf", "../../modules/**/*.tf"]
      enabled: true
    apply_requirements:
      - approved
      - mergeable
```

---

## GitLab CI

```yaml
# .gitlab-ci.yml
variables:
  TF_VERSION: "1.9.0"
  TF_DIR: "terraform/environments/prod"

image:
  name: hashicorp/terraform:${TF_VERSION}
  entrypoint: [""]

stages:
  - validate
  - security
  - plan
  - apply

cache:
  key: "${CI_PROJECT_ID}-${CI_COMMIT_REF_SLUG}"
  paths:
    - ${TF_DIR}/.terraform/

.terraform-base:
  before_script:
    - cd ${TF_DIR}
    - terraform init -reconfigure

validate:
  extends: .terraform-base
  stage: validate
  script:
    - terraform fmt -recursive -check
    - terraform validate
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

trivy:
  stage: security
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy config ${TF_DIR} --severity HIGH,CRITICAL --exit-code 1
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

plan:
  extends: .terraform-base
  stage: plan
  script:
    - terraform plan -var-file=terraform.tfvars -out=tfplan -no-color
  artifacts:
    name: "tfplan-${CI_COMMIT_SHA}"
    paths:
      - ${TF_DIR}/tfplan
    expire_in: 7 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

apply:
  extends: .terraform-base
  stage: apply
  script:
    - terraform apply tfplan
  dependencies:
    - plan
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual          # requires manual trigger for production
  environment:
    name: production
```

---

## Pre-Commit Hooks

Pre-commit runs on every `git commit` before code reaches CI, catching issues early.

### Setup

```bash
# Install pre-commit
pip install pre-commit    # or: brew install pre-commit

# Install git hook scripts
pre-commit install

# Run against all files (first time)
pre-commit run --all-files
```

### Configuration (`.pre-commit-config.yaml`)

```yaml
repos:
  # ── Terraform hooks via antonbabenko/pre-commit-terraform ───────────────
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.92.0
    hooks:
      - id: terraform_fmt
        args:
          - --args=-recursive

      - id: terraform_validate
        args:
          - --args=-backend=false

      - id: terraform_tflint
        args:
          - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl

      - id: terraform_trivy
        args:
          - --args=--severity=HIGH,CRITICAL

      - id: terraform_checkov
        args:
          - --args=--framework terraform
          - --args=--quiet

      - id: terraform_docs
        args:
          - --hook-config=--path-to-file=README.md
          - --hook-config=--add-to-existing-file=true
          - --hook-config=--create-file-if-not-exist=true

  # ── General hooks ────────────────────────────────────────────────────────
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: detect-private-key
      - id: check-added-large-files
        args: ['--maxkb=500']
```

### tflint configuration (`.tflint.hcl`)

```hcl
config {
  call_module_type = "local"
}

# Enable provider-specific ruleset (choose the one(s) you use)
plugin "aws" {
  enabled = true
  version = "0.27.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

plugin "azurerm" {
  enabled = true
  version = "0.25.0"
  source  = "github.com/terraform-linters/tflint-ruleset-azurerm"
}

plugin "google" {
  enabled = true
  version = "0.28.0"
  source  = "github.com/terraform-linters/tflint-ruleset-google"
}

rule "terraform_deprecated_interpolation" { enabled = true }
rule "terraform_unused_declarations"      { enabled = true }
rule "terraform_naming_convention"        { enabled = true }
rule "terraform_required_version"         { enabled = true }
rule "terraform_required_providers"       { enabled = true }
```

### Common skip patterns (document reasons)

```hcl
# In .tflint.hcl
rule "terraform_required_providers" {
  enabled = true
  # Skip modules — they use >= lower bounds; root handles pinning
}
```

```hcl
#checkov:skip=CKV_AWS_144: Cross-region replication adds cost with no benefit for this dev environment
```

---

## Infracost Integration

Add cost estimation to PRs (advisory — never blocks):

```yaml
# Add to the plan job in your workflow
- name: Infracost estimate
  uses: infracost/actions/setup@v3
  with:
    api-key: ${{ secrets.INFRACOST_API_KEY }}

- name: Generate cost breakdown
  run: |
    infracost breakdown --path ${{ env.WORKING_DIR }} \
      --format json --out-file /tmp/infracost-base.json

- name: Comment cost diff on PR
  uses: infracost/actions/comment@v3
  with:
    path: /tmp/infracost-base.json
    behavior: update    # update the previous Infracost comment
```

---

## OpenTofu Notes

OpenTofu is a drop-in open-source alternative to Terraform (BUSL → MPL-2.0). Replace `terraform` commands with `tofu`:

```bash
# Install
brew install opentofu    # macOS
# or: https://opentofu.org/docs/intro/install/

# Usage
tofu init
tofu validate
tofu plan -out=tfplan
tofu apply tfplan
```

In workflows, use `opentofu/setup-opentofu` action instead of `hashicorp/setup-terraform`:

```yaml
- uses: opentofu/setup-opentofu@v1
  with:
    tofu_version: "1.7.0"
```

All patterns in this skill apply equally to OpenTofu unless noted.

---

## LLM Mistake Checklist

- [ ] Apply workflow downloads the plan **artifact from plan job** — not replanning at apply time
- [ ] Apply job uses `environment:` with required reviewers for prod — not just `main` branch push
- [ ] OIDC authentication used for cloud credentials — not long-lived access keys in secrets
- [ ] Plan output uploaded as artifact with `retention-days` set
- [ ] `terraform fmt -check` (not just `fmt`) used in CI — non-zero exit on diff
- [ ] Security scan (`trivy` or `checkov`) runs before plan, not after
- [ ] `pre-commit-config.yaml` is committed to the repo
- [ ] `detect-private-key` hook enabled
- [ ] tflint plugin version pinned in `.tflint.hcl`
- [ ] `checkov:skip` and `tflint-ignore` comments include justification
- [ ] Infracost is advisory only — never blocks apply
- [ ] Backend init uses partial config (`-backend-config` flags) for CI — not hardcoded credentials in `backend.tf`
