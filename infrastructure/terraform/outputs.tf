output "livestock_products_table_name" {
  description = "Name of the LivestockProducts DynamoDB table"
  value       = module.dynamodb_tables.livestock_products_table_name
}

output "livestock_products_table_arn" {
  description = "ARN of the LivestockProducts DynamoDB table"
  value       = module.dynamodb_tables.livestock_products_table_arn
}

output "livestock_sellers_table_name" {
  description = "Name of the LivestockSellers DynamoDB table"
  value       = module.dynamodb_tables.livestock_sellers_table_name
}

output "livestock_sellers_table_arn" {
  description = "ARN of the LivestockSellers DynamoDB table"
  value       = module.dynamodb_tables.livestock_sellers_table_arn
}

output "data_loader_config" {
  description = "Configuration for data loader script"
  value       = module.dynamodb_tables.data_loader_config
}

# Bedrock Agent outputs will be available after manual deployment