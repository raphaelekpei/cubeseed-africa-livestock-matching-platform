terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "dynamodb_tables" {
  source = "./modules/dynamodb"
  
  aws_region  = var.aws_region
  environment = var.environment
  project     = var.project
  
  tags = var.common_tags
}

# Output the table name for Chalice configuration
output "chalice_environment_variables" {
  description = "Environment variables for Chalice deployment"
  value = {
    LIVESTOCK_TABLE_NAME = module.dynamodb_tables.livestock_matching_table_name
    BEDROCK_MODEL_ID     = var.bedrock_model_id
  }
}