# Deployment Checklist

## Pre-Deployment Requirements ✅

### 1. AWS Account Setup
- [ ] AWS CLI installed and configured
- [ ] AWS credentials with appropriate permissions
- [ ] Target AWS region selected

### 2. Python Environment
- [ ] Python 3.12 installed
- [ ] Chalice framework installed (`pip install chalice`)
- [ ] All dependencies available (`pip install -r requirements.txt`)

### 3. DynamoDB Tables
- [ ] Products table exists with correct schema
- [ ] Sellers table exists with correct schema
- [ ] Tables have required indexes (LivestockTypeIndex)
- [ ] Tables contain sample data for testing

## Configuration Updates Required 🔧

### 1. Update `.chalice/config.json`
```json
{
    "environment_variables": {
        "PRODUCTS_TABLE_NAME": "YOUR_PRODUCTS_TABLE_NAME",
        "SELLERS_TABLE_NAME": "YOUR_SELLERS_TABLE_NAME",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0"
    }
}
```

### 2. Update `.chalice/policy-dev.json`
- Replace `YOUR_ACCOUNT_ID` with your AWS Account ID
- Replace `eu-west-1` with your AWS region
- Update DynamoDB table ARNs to match your table names

### 3. Optional: Update App Name
- Change `app_name` in `.chalice/config.json` if you want a different name
- This will affect the Lambda function name and other resource names

## Deployment Steps 🚀

### Option 1: Automated Script
```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Windows
deploy.bat
```

### Option 2: Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Deploy to AWS
chalice deploy --stage dev
```

## Post-Deployment Verification ✅

### 1. Test Health Endpoint
```bash
curl -X GET https://YOUR_API_URL/health
```
Expected response: `{"status": "healthy", "service": "livestock-matching-ai"}`

### 2. Test Search Endpoint
```bash
curl -X POST https://YOUR_API_URL/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find goats in Lagos"}'
```

### 3. Check AWS Resources
- [ ] Lambda function created and running
- [ ] API Gateway endpoint accessible
- [ ] CloudWatch logs showing activity
- [ ] IAM role created with correct permissions

## Troubleshooting 🔍

### Common Issues

1. **Deployment fails with permission errors**
   - Check AWS credentials and permissions
   - Ensure IAM user has Lambda, API Gateway, and IAM permissions

2. **DynamoDB access errors**
   - Verify table names in configuration
   - Check IAM policy has correct table ARNs
   - Ensure tables exist in the correct region

3. **Bedrock access errors**
   - Verify Bedrock is available in your region
   - Check model ID is correct
   - Ensure IAM policy includes Bedrock permissions

4. **API Gateway 5xx errors**
   - Check CloudWatch logs for Lambda errors
   - Verify environment variables are set correctly
   - Test Lambda function directly in AWS console

### Useful Commands

```bash
# View deployment status
chalice status

# View logs
chalice logs

# Redeploy after changes
chalice deploy --stage dev

# Delete deployment
chalice delete --stage dev
```

## Security Considerations 🔒

- [ ] API Gateway has appropriate throttling configured
- [ ] Lambda function has minimal required permissions
- [ ] DynamoDB tables have appropriate access controls
- [ ] CloudWatch logs retention period set appropriately
- [ ] Consider adding API authentication for production use

## Cost Optimization 💰

- [ ] Lambda function memory allocation optimized
- [ ] DynamoDB provisioned capacity appropriate for usage
- [ ] CloudWatch log retention period set to reasonable duration
- [ ] API Gateway caching configured if needed