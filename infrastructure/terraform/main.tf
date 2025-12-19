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

# Bedrock Agent will be deployed separately via AWS CLI/Console
# as Terraform doesn't support it yet