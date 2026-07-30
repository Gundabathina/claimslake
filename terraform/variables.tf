# Root input variables. Region, project name, and environment are configurable;
# each important variable carries a validation rule.

variable "aws_region" {
  description = "AWS region to deploy into, such as us-east-1."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "aws_region must be a valid region code such as us-east-1 or eu-west-2."
  }
}

variable "project_name" {
  description = "Project name; used in resource names and tags."
  type        = string
  default     = "claimslake"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,30}[a-z0-9]$", var.project_name))
    error_message = "project_name must be lowercase alphanumeric with hyphens (3-32 chars)."
  }
}

variable "environment" {
  description = "Deployment environment (dev, staging, or prod)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "kms_key_arn" {
  description = "Optional KMS key ARN for S3 and Athena encryption. Null uses SSE-S3 (AES256)."
  type        = string
  default     = null
}

variable "version_ancillary_buckets" {
  description = "Enable versioning on the logs and Athena-results buckets."
  type        = bool
  default     = false
}

variable "athena_results_expiration_days" {
  description = "Days before Athena query results expire. Set 0 to disable."
  type        = number
  default     = 30

  validation {
    condition     = var.athena_results_expiration_days >= 0
    error_message = "athena_results_expiration_days must be zero or positive."
  }
}

variable "extra_tags" {
  description = "Additional tags merged into the common tag set."
  type        = map(string)
  default     = {}
}
