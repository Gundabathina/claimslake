# Input variables for the IAM module.

variable "name_prefix" {
  description = "Name prefix for IAM roles/policies, such as claimslake-dev."
  type        = string
}

variable "account_id" {
  description = "AWS account ID, used to scope the Athena role trust policy."
  type        = string
}

variable "data_bucket_arns" {
  description = "List of data-lake bucket ARNs the roles are allowed to read."
  type        = list(string)
}

variable "athena_results_bucket_arn" {
  description = "ARN of the Athena query-results bucket (read/write for Athena)."
  type        = string
}

variable "tags" {
  description = "Tags applied to IAM roles."
  type        = map(string)
  default     = {}
}
