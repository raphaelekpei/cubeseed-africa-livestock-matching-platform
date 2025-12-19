resource "aws_dynamodb_table" "livestock_matching" {
  name           = "livestock-matching-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "ProductName"

  attribute {
    name = "ProductName"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "livestock-matching-table"
    Type = "DynamoDB"
    TableType = "SingleTable"
  })
}