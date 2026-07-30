# Input variables for the Glue module.

variable "name_prefix" {
  description = "Name prefix for Glue resources, such as claimslake-dev."
  type        = string
}

variable "glue_crawler_role_arn" {
  description = "ARN of the IAM role the crawlers assume (from the iam module)."
  type        = string
}

variable "silver_bucket_id" {
  description = "Silver bucket ID; the Silver crawler target."
  type        = string
}

variable "gold_bucket_id" {
  description = "Gold bucket ID; the Gold crawler target."
  type        = string
}

variable "tags" {
  description = "Tags applied to Glue resources."
  type        = map(string)
  default     = {}
}
