# ---------------------------------------------------------------------------
# Root module: composes the S3, IAM, Glue, and Athena modules into the
# ClaimsLake AWS data-lake reference architecture. Module order follows the
# dependency graph: S3 first, then IAM/Athena consume its outputs, then Glue
# consumes both S3 and IAM. Terraform resolves this automatically from the
# references below - no explicit depends_on is required.
# ---------------------------------------------------------------------------

module "s3" {
  source = "./modules/s3"

  name_prefix                    = local.name_prefix
  account_id                     = local.account_id
  kms_key_arn                    = var.kms_key_arn
  version_ancillary_buckets      = var.version_ancillary_buckets
  athena_results_expiration_days = var.athena_results_expiration_days
  tags                           = local.common_tags
}

module "iam" {
  source = "./modules/iam"

  name_prefix               = local.name_prefix
  account_id                = local.account_id
  data_bucket_arns          = module.s3.all_data_bucket_arns
  athena_results_bucket_arn = module.s3.athena_results_bucket_arn
  tags                      = local.common_tags
}

module "glue" {
  source = "./modules/glue"

  name_prefix           = local.name_prefix
  glue_crawler_role_arn = module.iam.glue_crawler_role_arn
  silver_bucket_id      = module.s3.silver_bucket_id
  gold_bucket_id        = module.s3.gold_bucket_id
  tags                  = local.common_tags
}

module "athena" {
  source = "./modules/athena"

  name_prefix              = local.name_prefix
  athena_results_bucket_id = module.s3.athena_results_bucket_id
  kms_key_arn              = var.kms_key_arn
  tags                     = local.common_tags
}
