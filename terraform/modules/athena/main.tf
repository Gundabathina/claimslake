# ---------------------------------------------------------------------------
# Athena module: a workgroup that enforces a central query-results location
# and encrypts results. Enforcement (enforce_workgroup_configuration) stops
# users overriding the secure result location per query.
# ---------------------------------------------------------------------------

resource "aws_athena_workgroup" "this" {
  name        = "${var.name_prefix}-wg"
  description = "ClaimsLake Athena workgroup with enforced, encrypted results."
  state       = "ENABLED"
  tags        = var.tags

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.athena_results_bucket_id}/output/"

      encryption_configuration {
        encryption_option = var.kms_key_arn == null ? "SSE_S3" : "SSE_KMS"
        kms_key           = var.kms_key_arn
      }
    }
  }
}
