# AWS Credentials Setup

This project requires AWS credentials to deploy and run. **Never commit actual credentials to version control.**

## Option 1: AWS CLI Configuration (Recommended)

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key  
- Default region (us-east-1)
- Default output format (json)

## Option 2: Environment Variables

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"
```

## Option 3: IAM Roles (For EC2/Lambda)

If running on AWS infrastructure, use IAM roles instead of access keys.

## Required Permissions

Your AWS credentials need the following permissions:
- DynamoDB: CreateTable, DeleteTable, PutItem, GetItem, Scan, Query
- Lambda: CreateFunction, UpdateFunction, DeleteFunction
- API Gateway: CreateRestApi, CreateDeployment
- IAM: CreateRole, AttachRolePolicy
- CloudFormation: CreateStack, UpdateStack, DeleteStack

## Security Best Practices

1. Use least-privilege access
2. Rotate credentials regularly
3. Never commit credentials to version control
4. Use IAM roles when possible
5. Enable MFA on your AWS account

## Account Configuration

Update the following files with your AWS Account ID:
- `deployment-package/.chalice/policy-dev.json`
- `ai-matching-service/.chalice/policy-dev.json`

Replace `YOUR_ACCOUNT_ID` with your actual AWS Account ID (12-digit number).