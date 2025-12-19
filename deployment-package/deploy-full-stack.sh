#!/bin/bash

# Full Stack Deployment Script for AI Livestock Matching Service
# This script deploys infrastructure, loads data, and deploys the Chalice application

set -e  # Exit on any error

echo "🚀 AI Livestock Matching Service - Full Stack Deployment"
echo "========================================================"

# Set AWS credentials (configure via AWS CLI or environment variables)
# export AWS_ACCESS_KEY_ID="your-access-key-id"
# export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"

# Configuration
PROJECT_NAME="ai-livestock-matching"
ENVIRONMENT="dev"
REGION="us-east-1"

echo "📋 Deployment Configuration:"
echo "   Project: $PROJECT_NAME"
echo "   Environment: $ENVIRONMENT"
echo "   Region: $REGION"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it first."
    exit 1
fi

if ! command -v chalice &> /dev/null; then
    echo "❌ Chalice is not installed. Installing..."
    pip install chalice
fi

if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Step 1: Deploy Infrastructure
echo "🏗️  Step 1: Deploying Infrastructure with Terraform..."
cd infrastructure/terraform

# Create terraform.tfvars
cat > terraform.tfvars << EOF
aws_region  = "$REGION"
environment = "$ENVIRONMENT"
project     = "$PROJECT_NAME"

bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

common_tags = {
  Project     = "$PROJECT_NAME"
  Environment = "$ENVIRONMENT"
  ManagedBy   = "terraform"
  Owner       = "deployment-script"
  Service     = "livestock-matching-ai"
}
EOF

# Initialize and apply Terraform
terraform init
terraform plan
terraform apply -auto-approve

# Get table names from Terraform output
PRODUCTS_TABLE=$(terraform output -raw livestock_products_table_name)
SELLERS_TABLE=$(terraform output -raw livestock_sellers_table_name)

echo "✅ Infrastructure deployed successfully!"
echo "   Products Table: $PRODUCTS_TABLE"
echo "   Sellers Table: $SELLERS_TABLE"
echo ""

cd ../..

# Step 2: Load Sample Data
echo "📊 Step 2: Loading Sample Data..."

# Set environment variables for data loader
export PRODUCTS_TABLE_NAME="$PRODUCTS_TABLE"
export SELLERS_TABLE_NAME="$SELLERS_TABLE"
export AWS_REGION="$REGION"
export PROJECT_NAME="$PROJECT_NAME"
export ENVIRONMENT="$ENVIRONMENT"

# Install data loader dependencies
cd data/data_loader
pip install -r requirements.txt

# Run data loader
python livestock_data_loader.py

echo "✅ Sample data loaded successfully!"
echo ""

cd ../..

# Step 3: Update Chalice Configuration
echo "⚙️  Step 3: Updating Chalice Configuration..."

# Update .chalice/config.json with actual table names
cat > .chalice/config.json << EOF
{
    "version": "2.0",
    "app_name": "livestock-matching-ai",
    "stages": {
        "dev": {
            "api_gateway_stage": "api",
            "autogen_policy": false,
            "iam_policy_file": "policy-dev.json",
            "environment_variables": {
                "PRODUCTS_TABLE_NAME": "$PRODUCTS_TABLE",
                "SELLERS_TABLE_NAME": "$SELLERS_TABLE",
                "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0"
            }
        }
    }
}
EOF

# Get AWS Account ID for IAM policy
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Update .chalice/policy-dev.json with actual table ARNs
cat > .chalice/policy-dev.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$PRODUCTS_TABLE",
                "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$PRODUCTS_TABLE/index/*",
                "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$SELLERS_TABLE",
                "arn:aws:dynamodb:$REGION:$ACCOUNT_ID:table/$SELLERS_TABLE/index/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:$REGION::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            ]
        }
    ]
}
EOF

echo "✅ Chalice configuration updated!"
echo ""

# Step 4: Deploy Chalice Application
echo "🚀 Step 4: Deploying Chalice Application..."

# Install Chalice dependencies
pip install -r requirements.txt

# Deploy Chalice application
chalice deploy --stage dev

# Get API Gateway URL
API_URL=$(chalice url --stage dev)

echo "✅ Chalice application deployed successfully!"
echo ""

# Step 5: Test Deployment
echo "🧪 Step 5: Testing Deployment..."

# Test health endpoint
echo "Testing health endpoint..."
curl -s "$API_URL/health" | python -m json.tool

echo ""
echo "Testing search endpoint..."
curl -s -X POST "$API_URL/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Find goats in Lagos"}' | python -m json.tool

echo ""
echo "🎉 Full Stack Deployment Complete!"
echo "=================================="
echo ""
echo "📋 Deployment Summary:"
echo "   Products Table: $PRODUCTS_TABLE"
echo "   Sellers Table: $SELLERS_TABLE"
echo "   API Gateway URL: $API_URL"
echo ""
echo "🔗 Available Endpoints:"
echo "   Health Check: GET $API_URL/health"
echo "   Search: POST $API_URL/search"
echo "   Top Rated: POST $API_URL/recommendations/top-rated"
echo "   Proximity: POST $API_URL/search/proximity"
echo "   Bulk Capacity: POST $API_URL/search/bulk-capacity"
echo "   Popular Products: GET $API_URL/insights/popular-products"
echo ""
echo "📊 Next Steps:"
echo "   1. Test all endpoints with your preferred API client"
echo "   2. Monitor CloudWatch logs for any issues"
echo "   3. Update your frontend application with the new API URL"
echo "   4. Consider setting up monitoring and alerting"