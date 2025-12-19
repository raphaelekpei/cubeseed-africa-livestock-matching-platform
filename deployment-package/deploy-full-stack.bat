@echo off
REM Full Stack Deployment Script for AI Livestock Matching Service
REM This script deploys infrastructure, loads data, and deploys the Chalice application

echo 🚀 AI Livestock Matching Service - Full Stack Deployment
echo ========================================================

REM Set AWS credentials (configure via AWS CLI or environment variables)
REM set AWS_ACCESS_KEY_ID=your-access-key-id
REM set AWS_SECRET_ACCESS_KEY=your-secret-access-key
set AWS_DEFAULT_REGION=us-east-1

REM Configuration
set PROJECT_NAME=ai-livestock-matching
set ENVIRONMENT=dev
set REGION=us-east-1

echo 📋 Deployment Configuration:
echo    Project: %PROJECT_NAME%
echo    Environment: %ENVIRONMENT%
echo    Region: %REGION%
echo.

REM Check prerequisites
echo 🔍 Checking prerequisites...

terraform --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Terraform is not installed. Please install it first.
    pause
    exit /b 1
)

chalice --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Chalice is not installed. Installing...
    pip install chalice
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Step 1: Deploy Infrastructure
echo 🏗️  Step 1: Deploying Infrastructure with Terraform...
cd infrastructure\terraform

REM Create terraform.tfvars
(
echo aws_region  = "%REGION%"
echo environment = "%ENVIRONMENT%"
echo project     = "%PROJECT_NAME%"
echo.
echo bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
echo.
echo common_tags = {
echo   Project     = "%PROJECT_NAME%"
echo   Environment = "%ENVIRONMENT%"
echo   ManagedBy   = "terraform"
echo   Owner       = "deployment-script"
echo   Service     = "livestock-matching-ai"
echo }
) > terraform.tfvars

REM Initialize and apply Terraform
terraform init
terraform plan
terraform apply -auto-approve

REM Get table names from Terraform output
for /f "tokens=*" %%i in ('terraform output -raw livestock_products_table_name') do set PRODUCTS_TABLE=%%i
for /f "tokens=*" %%i in ('terraform output -raw livestock_sellers_table_name') do set SELLERS_TABLE=%%i

echo ✅ Infrastructure deployed successfully!
echo    Products Table: %PRODUCTS_TABLE%
echo    Sellers Table: %SELLERS_TABLE%
echo.

cd ..\..

REM Step 2: Load Sample Data
echo 📊 Step 2: Loading Sample Data...

REM Set environment variables for data loader
set PRODUCTS_TABLE_NAME=%PRODUCTS_TABLE%
set SELLERS_TABLE_NAME=%SELLERS_TABLE%
set AWS_REGION=%REGION%

REM Install data loader dependencies
cd data\data_loader
pip install -r requirements.txt

REM Run data loader
python livestock_data_loader.py

echo ✅ Sample data loaded successfully!
echo.

cd ..\..

REM Step 3: Update Chalice Configuration
echo ⚙️  Step 3: Updating Chalice Configuration...

REM Get AWS Account ID for IAM policy
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i

REM Update .chalice/config.json with actual table names
(
echo {
echo     "version": "2.0",
echo     "app_name": "livestock-matching-ai",
echo     "stages": {
echo         "dev": {
echo             "api_gateway_stage": "api",
echo             "autogen_policy": false,
echo             "iam_policy_file": "policy-dev.json",
echo             "environment_variables": {
echo                 "PRODUCTS_TABLE_NAME": "%PRODUCTS_TABLE%",
echo                 "SELLERS_TABLE_NAME": "%SELLERS_TABLE%",
echo                 "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0"
echo             }
echo         }
echo     }
echo }
) > .chalice\config.json

REM Update .chalice/policy-dev.json with actual table ARNs
(
echo {
echo     "Version": "2012-10-17",
echo     "Statement": [
echo         {
echo             "Effect": "Allow",
echo             "Action": [
echo                 "logs:CreateLogGroup",
echo                 "logs:CreateLogStream",
echo                 "logs:PutLogEvents"
echo             ],
echo             "Resource": "arn:aws:logs:*:*:*"
echo         },
echo         {
echo             "Effect": "Allow",
echo             "Action": [
echo                 "dynamodb:GetItem",
echo                 "dynamodb:PutItem",
echo                 "dynamodb:UpdateItem",
echo                 "dynamodb:DeleteItem",
echo                 "dynamodb:Query",
echo                 "dynamodb:Scan"
echo             ],
echo             "Resource": [
echo                 "arn:aws:dynamodb:%REGION%:%ACCOUNT_ID%:table/%PRODUCTS_TABLE%",
echo                 "arn:aws:dynamodb:%REGION%:%ACCOUNT_ID%:table/%PRODUCTS_TABLE%/index/*",
echo                 "arn:aws:dynamodb:%REGION%:%ACCOUNT_ID%:table/%SELLERS_TABLE%",
echo                 "arn:aws:dynamodb:%REGION%:%ACCOUNT_ID%:table/%SELLERS_TABLE%/index/*"
echo             ]
echo         },
echo         {
echo             "Effect": "Allow",
echo             "Action": [
echo                 "bedrock:InvokeModel",
echo                 "bedrock:InvokeModelWithResponseStream"
echo             ],
echo             "Resource": [
echo                 "arn:aws:bedrock:%REGION%::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
echo             ]
echo         }
echo     ]
echo }
) > .chalice\policy-dev.json

echo ✅ Chalice configuration updated!
echo.

REM Step 4: Deploy Chalice Application
echo 🚀 Step 4: Deploying Chalice Application...

REM Install Chalice dependencies
pip install -r requirements.txt

REM Deploy Chalice application
chalice deploy --stage dev

REM Get API Gateway URL
for /f "tokens=*" %%i in ('chalice url --stage dev') do set API_URL=%%i

echo ✅ Chalice application deployed successfully!
echo.

REM Step 5: Test Deployment
echo 🧪 Step 5: Testing Deployment...

echo Testing health endpoint...
curl -s "%API_URL%/health"

echo.
echo Testing search endpoint...
curl -s -X POST "%API_URL%/search" -H "Content-Type: application/json" -d "{\"query\": \"Find goats in Lagos\"}"

echo.
echo 🎉 Full Stack Deployment Complete!
echo ==================================
echo.
echo 📋 Deployment Summary:
echo    Products Table: %PRODUCTS_TABLE%
echo    Sellers Table: %SELLERS_TABLE%
echo    API Gateway URL: %API_URL%
echo.
echo 🔗 Available Endpoints:
echo    Health Check: GET %API_URL%/health
echo    Search: POST %API_URL%/search
echo    Top Rated: POST %API_URL%/recommendations/top-rated
echo    Proximity: POST %API_URL%/search/proximity
echo    Bulk Capacity: POST %API_URL%/search/bulk-capacity
echo    Popular Products: GET %API_URL%/insights/popular-products
echo.
echo 📊 Next Steps:
echo    1. Test all endpoints with your preferred API client
echo    2. Monitor CloudWatch logs for any issues
echo    3. Update your frontend application with the new API URL
echo    4. Consider setting up monitoring and alerting

pause