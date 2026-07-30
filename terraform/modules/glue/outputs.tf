# Outputs for the Glue module.

output "database_name" {
  description = "Glue Data Catalog database name."
  value       = aws_glue_catalog_database.this.name
}

output "silver_crawler_name" {
  description = "Name of the Silver Glue crawler."
  value       = aws_glue_crawler.silver.name
}

output "gold_crawler_name" {
  description = "Name of the Gold Glue crawler."
  value       = aws_glue_crawler.gold.name
}
