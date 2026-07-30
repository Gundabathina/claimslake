# Derived values shared across the root module.
#
# aws_caller_identity reads the active account ID at plan/apply time. NOTE:
# "terraform validate" and "init -backend=false" do NOT need credentials, but
# "plan"/"apply" will call STS and therefore require valid AWS credentials.

data "aws_caller_identity" "current" {}

locals {
  account_id  = data.aws_caller_identity.current.account_id
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "claimslake"
    },
    var.extra_tags,
  )
}
