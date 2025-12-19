#!/bin/bash

# AI Livestock Matching Service Deployment Script
# This script helps deploy another instance of the service

echo "🚀 AI Livestock Matching Service Deployment"
echo "==========================================="

# Check if chalice is installed
if ! command -v chalice &> /dev/null; then
    echo "❌ Chalice is not installed. Please install it first:"
    echo "   pip install chalice"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured or credentials are invalid"
    echo "   Please configure AWS CLI with: aws configure"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Get current AWS account info
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)

echo "📋 Current AWS Configuration:"
echo "   Account ID: $ACCOUNT_ID"
echo "   Region: $REGION"
echo ""

# Prompt for configuration updates
echo "🔧 Configuration Updates Required:"
echo "   1. Update .chalice/policy-dev.json with your Account ID and Region"
echo "   2. Update .chalice/config.json with your DynamoDB table names"
echo "   3. Ensure your DynamoDB tables exist and have the correct structure"
echo ""

read -p "Have you updated the configuration files? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Please update the configuration files first, then run this script again"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Deploy the service
echo "🚀 Deploying the service..."
chalice deploy --stage dev

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Test the health endpoint: GET /health"
    echo "   2. Try the search endpoint: POST /search"
    echo "   3. Check CloudWatch logs for any issues"
    echo "   4. Update your application to use the new API Gateway URL"
else
    echo ""
    echo "❌ Deployment failed. Please check the error messages above."
    echo "   Common issues:"
    echo "   - Incorrect AWS credentials"
    echo "   - Missing DynamoDB tables"
    echo "   - Incorrect IAM permissions"
    echo "   - Invalid configuration in .chalice/ files"
fi