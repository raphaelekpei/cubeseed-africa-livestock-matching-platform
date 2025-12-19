output "livestock_products_table_name" {
  description = "Name of the LivestockProducts table"
  value       = aws_dynamodb_table.livestock_products.name
}

output "livestock_products_table_arn" {
  description = "ARN of the LivestockProducts table"
  value       = aws_dynamodb_table.livestock_products.arn
}

output "livestock_sellers_table_name" {
  description = "Name of the LivestockSellers table"
  value       = aws_dynamodb_table.livestock_sellers.name
}

output "livestock_sellers_table_arn" {
  description = "ARN of the LivestockSellers table"
  value       = aws_dynamodb_table.livestock_sellers.arn
}

# Environment configuration for data loader
output "data_loader_config" {
  description = "Configuration values for the data loader script"
  value = {
    aws_region           = var.aws_region
    project_name         = var.project
    environment          = var.environment
    products_table_name  = aws_dynamodb_table.livestock_products.name
    sellers_table_name   = aws_dynamodb_table.livestock_sellers.name
  }
}