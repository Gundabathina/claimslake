# ---------------------------------------------------------------------------
# S3 module: data-lake buckets for the Bronze -> Silver -> Gold pipeline plus
# a quarantine bucket, a central access-logs bucket, and an Athena query
# results bucket. Every bucket is private and encrypted; data buckets are
# versioned and ship their access logs to the logs bucket.
# ---------------------------------------------------------------------------

# Data-lake layer buckets (bronze, silver, gold, quarantine). Keyed by layer
# so downstream configuration can iterate the same set consistently.
resource "aws_s3_bucket" "data" {
  for_each = toset(var.data_layers)

  bucket = "${var.name_prefix}-${each.key}-${var.account_id}"
  tags   = merge(var.tags, { Layer = each.key })
}

# Central bucket that receives S3 server access logs from the data buckets.
resource "aws_s3_bucket" "logs" {
  bucket = "${var.name_prefix}-logs-${var.account_id}"
  tags   = merge(var.tags, { Layer = "logs" })
}

# Athena query-results bucket. Kept separate from lake data so a lifecycle
# rule can expire transient result files without touching curated data.
resource "aws_s3_bucket" "athena_results" {
  bucket = "${var.name_prefix}-athena-results-${var.account_id}"
  tags   = merge(var.tags, { Layer = "athena-results" })
}

locals {
  # All buckets that must be locked down (private + encrypted). The logs and
  # results buckets are included; only *access logging* treats them specially.
  all_buckets = merge(
    { for k, b in aws_s3_bucket.data : k => b.id },
    {
      logs           = aws_s3_bucket.logs.id
      athena_results = aws_s3_bucket.athena_results.id
    },
  )
}

# Block all forms of public access on every bucket.
resource "aws_s3_bucket_public_access_block" "this" {
  for_each = local.all_buckets

  bucket                  = each.value
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Server-side encryption on every bucket. Defaults to SSE-S3 (AES256); set
# var.kms_key_arn to switch to SSE-KMS without editing the module.
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  for_each = local.all_buckets

  bucket = each.value

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = var.kms_key_arn != null
  }
}

# Versioning: enabled on data buckets (recoverable lake data). The logs and
# results buckets follow var.version_ancillary_buckets (off by default).
resource "aws_s3_bucket_versioning" "data" {
  for_each = aws_s3_bucket.data

  bucket = each.value.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "ancillary" {
  for_each = {
    logs           = aws_s3_bucket.logs.id
    athena_results = aws_s3_bucket.athena_results.id
  }

  bucket = each.value
  versioning_configuration {
    status = var.version_ancillary_buckets ? "Enabled" : "Suspended"
  }
}

# Ship access logs from each data bucket to the logs bucket under a per-bucket
# prefix. The logs bucket is deliberately NOT configured here, preventing
# access-log recursion (a bucket logging to itself).
resource "aws_s3_bucket_logging" "data" {
  for_each = aws_s3_bucket.data

  bucket        = each.value.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/${each.value.id}/"
}

# Expire transient Athena query results. Guarded by a positive expiration so
# the module never emits an invalid empty lifecycle configuration.
resource "aws_s3_bucket_lifecycle_configuration" "athena_results" {
  count = var.athena_results_expiration_days > 0 ? 1 : 0

  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "expire-query-results"
    status = "Enabled"

    filter {}

    expiration {
      days = var.athena_results_expiration_days
    }
  }
}
