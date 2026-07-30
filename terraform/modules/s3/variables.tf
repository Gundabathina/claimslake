# Input variables for the S3 module.

variable "name_prefix" {
  description = "Bucket name prefix such as claimslake-dev (project plus environment)."
  type        = string
}

variable "account_id" {
  description = "AWS account ID, appended to bucket names for global uniqueness."
  type        = string
}

variable "data_layers" {
  description = "Data-lake layers that each get a dedicated bucket."
  type        = list(string)
  default     = ["bronze", "silver", "gold", "quarantine"]
}

variable "kms_key_arn" {
  description = "Optional KMS key ARN for SSE-KMS. When null, buckets use SSE-S3 (AES256)."
  type        = string
  default     = null
}

variable "version_ancillary_buckets" {
  description = "Whether to enable versioning on the logs and Athena-results buckets."
  type        = bool
  default     = false
}

variable "athena_results_expiration_days" {
  description = "Days after which Athena query results expire. Set 0 to disable the lifecycle rule."
  type        = number
  default     = 30

  validation {
    condition     = var.athena_results_expiration_days >= 0
    error_message = "athena_results_expiration_days must be zero or a positive number of days."
  }
}

variable "tags" {
  description = "Tags applied to all buckets."
  type        = map(string)
  default     = {}
}
