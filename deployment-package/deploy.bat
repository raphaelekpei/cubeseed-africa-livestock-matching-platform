@echo off
REM AI Livestock Matching Service Deployment Script for Windows
REM This script helps deploy another instance of the service

echo 🚀 AI Livestock Matching Service Deployment
echo ===========================================

REM Check if chalice is installed
chalice --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Chalice is not installed. Please install it first:
    echo    pip install chalice
    pause
    exit /b 1
)

REM Check if AWS CLI is configured
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ AWS CLI is not configured or credentials are invalid
    echo    Please configure AWS CLI with: aws configure
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Get current AWS account info
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
for /f "tokens=*" %%i in ('aws configure get region') do set REGION=%%i

echo 📋 Current AWS Configuration:
echo    Account ID: %ACCOUNT_ID%
echo    Region: %REGION%
echo.

REM Prompt for configuration updates
echo 🔧 Configuration Updates Required:
echo    1. Update .chalice/policy-dev.json with your Account ID and Region
echo    2. Update .chalice/config.json with your DynamoDB table names
echo    3. Ensure your DynamoDB tables exist and have the correct structure
echo.

set /p "confirm=Have you updated the configuration files? (y/n): "
if /i not "%confirm%"=="y" (
    echo ❌ Please update the configuration files first, then run this script again
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Deploy the service
echo 🚀 Deploying the service...
chalice deploy --stage dev

if %errorlevel% equ 0 (
    echo.
    echo ✅ Deployment successful!
    echo.
    echo 📋 Next Steps:
    echo    1. Test the health endpoint: GET /health
    echo    2. Try the search endpoint: POST /search
    echo    3. Check CloudWatch logs for any issues
    echo    4. Update your application to use the new API Gateway URL
) else (
    echo.
    echo ❌ Deployment failed. Please check the error messages above.
    echo    Common issues:
    echo    - Incorrect AWS credentials
    echo    - Missing DynamoDB tables
    echo    - Incorrect IAM permissions
    echo    - Invalid configuration in .chalice/ files
)

pause