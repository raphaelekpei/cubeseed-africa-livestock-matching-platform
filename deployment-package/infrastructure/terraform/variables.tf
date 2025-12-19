variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project" {
  description = "Project name - will be used as prefix for table names"
  type        = string
  default     = "ai-livestock-matching"
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model ID for AI processing"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "ai-livestock-matching"
    ManagedBy   = "terraform"
    Service     = "livestock-matching-ai"
  }
}