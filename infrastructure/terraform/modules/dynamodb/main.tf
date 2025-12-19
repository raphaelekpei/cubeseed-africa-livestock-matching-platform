resource "aws_dynamodb_table" "livestock_products" {
  name           = "${var.project}-${var.environment}-livestock-products"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "ProductId"

  attribute {
    name = "ProductId"
    type = "S"
  }

  attribute {
    name = "Species"
    type = "S"
  }

  attribute {
    name = "LivestockType"
    type = "S"
  }

  global_secondary_index {
    name            = "SpeciesIndex"
    hash_key        = "Species"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "LivestockTypeIndex"
    hash_key        = "LivestockType"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "${var.project}-${var.environment}-livestock-products"
    Type = "DynamoDB"
  })
}

resource "aws_dynamodb_table" "livestock_sellers" {
  name           = "${var.project}-${var.environment}-livestock-sellers"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "SellerId"

  attribute {
    name = "SellerId"
    type = "S"
  }

  attribute {
    name = "City"
    type = "S"
  }

  attribute {
    name = "State"
    type = "S"
  }

  global_secondary_index {
    name            = "CityIndex"
    hash_key        = "City"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "StateIndex"
    hash_key        = "State"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "${var.project}-${var.environment}-livestock-sellers"
    Type = "DynamoDB"
  })
}