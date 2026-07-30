# Root outputs: the key identifiers an operator needs after apply.

output "data_bucket_ids" {
  description = "Map of data-lake layer to S3 bucket name (bronze/silver/gold/quarantine)."
  value       = module.s3.data_bucket_ids
}

output "logs_bucket_id" {
  description = "S3 access-logs bucket name."
  value       = module.s3.logs_bucket_id
}

output "athena_results_bucket_id" {
  description = "S3 bucket that stores Athena query results."
  value       = module.s3.athena_results_bucket_id
}

output "glue_database_name" {
  description = "Glue Data Catalog database name."
  value       = module.glue.database_name
}

output "glue_crawler_names" {
  description = "Names of the Silver and Gold Glue crawlers."
  value       = [module.glue.silver_crawler_name, module.glue.gold_crawler_name]
}

output "athena_workgroup_name" {
  description = "Athena workgroup name."
  value       = module.athena.workgroup_name
}

output "glue_crawler_role_arn" {
  description = "IAM role ARN assumed by the Glue crawlers."
  value       = module.iam.glue_crawler_role_arn
}

output "athena_role_arn" {
  description = "IAM role ARN for running Athena queries."
  value       = module.iam.athena_role_arn
}
