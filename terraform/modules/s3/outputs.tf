# Outputs consumed by the iam, glue, and athena modules. Exposing ARNs and
# names here (rather than referencing S3 resources across modules) keeps the
# dependency graph acyclic: S3 is created first, other modules read its output.

output "data_bucket_ids" {
  description = "Map of data-layer name to bucket ID (bronze, silver, gold, quarantine)."
  value       = { for k, b in aws_s3_bucket.data : k => b.id }
}

output "data_bucket_arns" {
  description = "Map of data-layer name to bucket ARN."
  value       = { for k, b in aws_s3_bucket.data : k => b.arn }
}

output "all_data_bucket_arns" {
  description = "List of every data-bucket ARN, for IAM policy resource lists."
  value       = [for b in aws_s3_bucket.data : b.arn]
}

output "silver_bucket_id" {
  description = "Silver bucket ID (crawler target)."
  value       = aws_s3_bucket.data["silver"].id
}

output "gold_bucket_id" {
  description = "Gold bucket ID (crawler target)."
  value       = aws_s3_bucket.data["gold"].id
}

output "logs_bucket_id" {
  description = "Access-logs bucket ID."
  value       = aws_s3_bucket.logs.id
}

output "athena_results_bucket_id" {
  description = "Athena query-results bucket ID."
  value       = aws_s3_bucket.athena_results.id
}

output "athena_results_bucket_arn" {
  description = "Athena query-results bucket ARN."
  value       = aws_s3_bucket.athena_results.arn
}
