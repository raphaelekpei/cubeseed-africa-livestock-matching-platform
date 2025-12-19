output "livestock_matching_table_name" {
  description = "Name of the Livestock Matching DynamoDB table"
  value       = module.dynamodb_tables.livestock_matching_table_name
}

output "livestock_matching_table_arn" {
  description = "ARN of the Livestock Matching DynamoDB table"
  value       = module.dynamodb_tables.livestock_matching_table_arn
}

output "chalice_config_update" {
  description = "Configuration values to update in Chalice .chalice/config.json"
  value = {
    environment_variables = {
      LIVESTOCK_TABLE_NAME = module.dynamodb_tables.livestock_matching_table_name
      BEDROCK_MODEL_ID     = var.bedrock_model_id
    }
  }
}

output "iam_policy_arns" {
  description = "DynamoDB table ARNs for IAM policy configuration"
  value = {
    table_arn = module.dynamodb_tables.livestock_matching_table_arn
    index_arn = "${module.dynamodb_tables.livestock_matching_table_arn}/index/*"
  }
}