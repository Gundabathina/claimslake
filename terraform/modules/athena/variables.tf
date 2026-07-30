# Input variables for the Athena module.

variable "name_prefix" {
  description = "Name prefix for the Athena workgroup, such as claimslake-dev."
  type        = string
}

variable "athena_results_bucket_id" {
  description = "Bucket ID where Athena writes query results."
  type        = string
}

variable "kms_key_arn" {
  description = "Optional KMS key ARN for result encryption. When null, results use SSE-S3."
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags applied to the Athena workgroup."
  type        = map(string)
  default     = {}
}
