# AWS provider. Region comes from a variable; credentials are resolved by the
# standard AWS chain (environment variables, shared config/profile, or an IAM
# role) - never hardcoded here. default_tags applies the common tag set to
# every taggable resource.

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}
