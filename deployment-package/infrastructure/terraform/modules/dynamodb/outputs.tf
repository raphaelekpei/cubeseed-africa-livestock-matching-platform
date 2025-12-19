output "livestock_matching_table_name" {
  description = "Name of the Livestock Matching table"
  value       = aws_dynamodb_table.livestock_matching.name
}

output "livestock_matching_table_arn" {
  description = "ARN of the Livestock Matching table"
  value       = aws_dynamodb_table.livestock_matching.arn
}