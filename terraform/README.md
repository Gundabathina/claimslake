# ClaimsLake — Terraform AWS Reference Architecture

Production-style Terraform describing an AWS data lake that mirrors the local
ClaimsLake pipeline (Bronze → Silver → Gold, plus quarantine). It uses
**Athena + Glue** for serverless querying and cataloging — no Redshift, so the
declared footprint stays low-cost.

> **This is a reference deployment. It has NOT been applied to any AWS account.**
> It is validated in CI (fmt + init + validate) but never planned or applied by
> this repository. Applying it is a deliberate, manual, cost-aware decision.

## Architecture overview

| Layer | AWS resource |
|-------|--------------|
| Bronze / Silver / Gold / Quarantine | One private, encrypted, versioned S3 bucket each |
| Access logs | Central S3 logs bucket (receives access logs from the data buckets; never logs to itself) |
| Catalog | Glue Data Catalog database + separate Silver and Gold crawlers (schemas inferred, never hardcoded) |
| Query engine | Athena workgroup with an enforced, encrypted results location |
| Query results | Dedicated S3 bucket with a lifecycle rule that expires old results |
| Access | Least-privilege IAM roles for the crawlers and for Athena (built from `aws_iam_policy_document`, no `*FullAccess`) |

Buckets are named `<project>-<environment>-<layer>-<account_id>` for global
uniqueness. Every bucket blocks public access and is encrypted (SSE-S3 by
default; SSE-KMS on the data buckets when `kms_key_arn` is set).

## Prerequisites

- Terraform >= 1.5 (CI pins 1.9.5).
- For `plan`/`apply` only: AWS credentials via the standard chain
  (`AWS_PROFILE`, environment variables, or an IAM role) with permission to
  create S3, Glue, IAM, and Athena resources. **`fmt`, `init -backend=false`,
  and `validate` need no credentials.**

## File & module structure

```
terraform/
  versions.tf              Terraform + AWS provider constraints; commented S3 backend
  providers.tf             AWS provider (region var + default_tags)
  variables.tf             Root variables with validation rules
  locals.tf                account_id (via aws_caller_identity), name prefix, tags
  main.tf                  Wires the four modules together
  outputs.tf               Bucket names, catalog db, workgroup, role ARNs
  terraform.tfvars.example Copy to terraform.tfvars and edit
  modules/
    s3/                    Data + logs + results buckets, encryption, versioning, logging, lifecycle
    iam/                   Least-privilege Glue crawler and Athena roles
    glue/                  Catalog database + Silver/Gold crawlers
    athena/                Workgroup with enforced, encrypted results
```

## Variable examples

See `terraform.tfvars.example`. Minimal:

```hcl
aws_region   = "us-east-1"
project_name = "claimslake"
environment  = "dev"
```

Optional: `kms_key_arn`, `version_ancillary_buckets`,
`athena_results_expiration_days`, and `extra_tags`. Every root variable has a
validation rule (region format, project-name charset, environment enum,
non-negative expiration).

## Commands

```bash
cd terraform

# Validate (no AWS credentials required) — this is what CI runs:
terraform fmt -check -recursive
terraform init -backend=false
terraform validate

# Plan / apply (REQUIRES AWS credentials — creates real resources, may incur cost):
terraform init
terraform plan
terraform apply
```

Note: `plan`/`apply` read the account ID through `aws_caller_identity` and will
call AWS STS, so they need valid credentials; `validate` does not.

### Remote state (optional)

`versions.tf` contains a commented-out `backend "s3"` block. The default
(no backend) lets `terraform init -backend=false` run anywhere. To use remote
state, create the state bucket and lock table first, then uncomment it and run
`terraform init`.

## Cost warning

Applying this creates real AWS resources. S3, Glue Data Catalog, and Athena are
low-cost and largely usage-based, but **not free**: you pay for stored data,
crawler runtime, and data scanned by Athena queries. Only `apply` in an account
you control and are willing to be billed for.

## Teardown

```bash
cd terraform
terraform destroy
```

Empty the S3 buckets first if versioning left object versions behind
(`terraform destroy` cannot delete non-empty versioned buckets).

## Status

Reference-only. Verified by the `Terraform` GitHub Actions workflow
(`fmt -check -recursive`, `init -backend=false`, `validate`). No credentials,
account IDs, bucket names, or regions are hardcoded anywhere in this directory.
