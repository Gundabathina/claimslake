# Outputs for the IAM module.

output "glue_crawler_role_arn" {
  description = "ARN of the Glue crawler role (passed to the glue module)."
  value       = aws_iam_role.glue_crawler.arn
}

output "glue_crawler_role_name" {
  description = "Name of the Glue crawler role."
  value       = aws_iam_role.glue_crawler.name
}

output "athena_role_arn" {
  description = "ARN of the Athena query role."
  value       = aws_iam_role.athena.arn
}
