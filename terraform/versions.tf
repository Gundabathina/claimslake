# Terraform and provider version constraints.
#
# Remote-state-ready: the S3 backend below is intentionally commented out so
# that "terraform init -backend=false" works with no pre-existing backend
# (as used in CI and for offline validation). To use remote state, create the
# backend bucket/table first, then uncomment and run "terraform init".

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # backend "s3" {
  #   bucket         = "REPLACE-with-your-tfstate-bucket"
  #   key            = "claimslake/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "REPLACE-with-your-lock-table"
  #   encrypt        = true
  # }
}
