# ---------------------------------------------------------------------------
# IAM module: least-privilege roles for the Glue crawlers and for Athena
# querying. Policies are built with aws_iam_policy_document data sources
# (not hardcoded JSON) and scoped to the specific buckets and catalog passed
# in from the caller. No broad AdministratorAccess / *FullAccess is attached.
# ---------------------------------------------------------------------------

locals {
  # Bucket-level ARNs and their object ARNs (arn + /*), for S3 statements.
  data_bucket_arns    = var.data_bucket_arns
  data_bucket_objects = [for a in var.data_bucket_arns : "${a}/*"]
  results_bucket_arn  = var.athena_results_bucket_arn
  results_bucket_objs = "${var.athena_results_bucket_arn}/*"
}

# ---- Glue crawler role -----------------------------------------------------

data "aws_iam_policy_document" "glue_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_crawler" {
  name               = "${var.name_prefix}-glue-crawler"
  description        = "Least-privilege role assumed by the Silver/Gold Glue crawlers."
  assume_role_policy = data.aws_iam_policy_document.glue_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "glue_crawler" {
  # Read the crawled data (Silver and Gold live in the data buckets).
  statement {
    sid       = "ReadLakeData"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = concat(local.data_bucket_arns, local.data_bucket_objects)
  }

  # Write discovered schemas into the Glue Data Catalog for this database.
  statement {
    sid    = "CatalogWrite"
    effect = "Allow"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:CreateTable",
      "glue:UpdateTable",
      "glue:DeleteTable",
      "glue:GetTable",
      "glue:GetTables",
      "glue:BatchCreatePartition",
      "glue:BatchGetPartition",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:UpdatePartition",
    ]
    resources = ["*"]
  }

  # Allow the crawler to publish its own CloudWatch logs.
  statement {
    sid    = "CrawlerLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:/aws-glue/*"]
  }
}

resource "aws_iam_role_policy" "glue_crawler" {
  name   = "${var.name_prefix}-glue-crawler"
  role   = aws_iam_role.glue_crawler.id
  policy = data.aws_iam_policy_document.glue_crawler.json
}

# ---- Athena query role -----------------------------------------------------

data "aws_iam_policy_document" "athena_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"]
    }
  }
}

resource "aws_iam_role" "athena" {
  name               = "${var.name_prefix}-athena"
  description        = "Least-privilege role for running Athena queries over the lake."
  assume_role_policy = data.aws_iam_policy_document.athena_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "athena" {
  # Read lake data being queried.
  statement {
    sid       = "ReadLakeData"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = concat(local.data_bucket_arns, local.data_bucket_objects)
  }

  # Read/write Athena query results.
  statement {
    sid    = "QueryResults"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [local.results_bucket_arn, local.results_bucket_objs]
  }

  # Read catalog metadata and run queries in the workgroup.
  statement {
    sid    = "AthenaAndCatalog"
    effect = "Allow"
    actions = [
      "athena:StartQueryExecution",
      "athena:StopQueryExecution",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:GetWorkGroup",
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:GetPartition",
      "glue:GetPartitions",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "athena" {
  name   = "${var.name_prefix}-athena"
  role   = aws_iam_role.athena.id
  policy = data.aws_iam_policy_document.athena.json
}
