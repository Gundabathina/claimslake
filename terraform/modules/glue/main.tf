# ---------------------------------------------------------------------------
# Glue module: one Data Catalog database plus separate Silver and Gold
# crawlers. Crawlers infer schemas from the S3 data (schemas are NOT
# hardcoded), each pointed only at its own bucket, with a schema-change
# policy that keeps the catalog in sync without dropping partitions.
# ---------------------------------------------------------------------------

resource "aws_glue_catalog_database" "this" {
  name        = replace("${var.name_prefix}_catalog", "-", "_")
  description  = "ClaimsLake Data Catalog database for Silver and Gold tables."

  tags = var.tags
}

# Crawl the Silver layer. update_behavior keeps table schemas current; delete
# behavior is DEPRECATE_IN_DATABASE so removed data is flagged, not dropped.
resource "aws_glue_crawler" "silver" {
  name          = "${var.name_prefix}-silver"
  description   = "Crawls the Silver bucket and catalogs its tables."
  role          = var.glue_crawler_role_arn
  database_name = aws_glue_catalog_database.this.name
  tags          = var.tags

  s3_target {
    path = "s3://${var.silver_bucket_id}/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }
}

resource "aws_glue_crawler" "gold" {
  name          = "${var.name_prefix}-gold"
  description   = "Crawls the Gold bucket and catalogs its tables."
  role          = var.glue_crawler_role_arn
  database_name = aws_glue_catalog_database.this.name
  tags          = var.tags

  s3_target {
    path = "s3://${var.gold_bucket_id}/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }
}
