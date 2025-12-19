# AI Livestock Matching Service - Deployment Package

This package contains all the necessary files to deploy another instance of the AI Livestock Matching Service.

## Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **Python 3.12** installed
3. **Chalice framework** installed: `pip install chalice`
4. **AWS Account** with permissions for:
   - Lambda functions
   - API Gateway
   - DynamoDB access
   - IAM role creation
   - CloudWatch Logs

## Deployment Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Edit `.chalice/config.json` and update the environment variables:
- `MARKETPLACE_TABLE_NAME`: Your DynamoDB marketplace table name
- `BEDROCK_MODEL_ID`: Your Bedrock model ID (default: anthropic.claude-3-sonnet-20240229-v1:0)

### 3. Update IAM Policy
Edit `.chalice/policy-dev.json` and update:
- AWS Account ID (replace `YOUR_ACCOUNT_ID` with your account ID)
- AWS Region (replace `eu-west-1` with your region)
- DynamoDB table ARNs to match your table names

### 4. Deploy
```bash
chalice deploy --stage dev
```

## Configuration Files

- **app.py**: Main application code (single table architecture)
- **requirements.txt**: Python dependencies
- **.chalice/config.json**: Chalice configuration
- **.chalice/policy-dev.json**: IAM permissions policy
- **data_loader.py**: Script to load sample data into DynamoDB
- **infrastructure/terraform/**: Terraform code to create DynamoDB table

## Environment Variables Required

| Variable | Description | Example |
|----------|-------------|---------|
| MARKETPLACE_TABLE_NAME | DynamoDB table for livestock marketplace | ai-livestock-matching-dev-marketplace |
| BEDROCK_MODEL_ID | Amazon Bedrock model identifier | anthropic.claude-3-sonnet-20240229-v1:0 |

## API Endpoints

After deployment, your API will have these endpoints:
- `GET /health` - Health check
- `POST /search` - Natural language livestock search
- `POST /recommendations/top-rated` - Get top-rated sellers
- `POST /search/proximity` - Location-based search
- `POST /search/bulk-capacity` - Bulk purchase capacity search
- `GET /insights/popular-products` - Popular products insights

## AWS Resources Created

- **Lambda Function**: `{app_name}-{stage}` (e.g., livestock-matching-ai-dev)
- **API Gateway**: REST API with custom stage name
- **IAM Role**: For Lambda execution with DynamoDB and Bedrock permissions
- **CloudWatch Log Group**: For application logs

## Customization

To deploy with different settings:

1. **Change App Name**: Update `app_name` in `.chalice/config.json`
2. **Change Stage**: Use `chalice deploy --stage production`
3. **Different Region**: Set `AWS_DEFAULT_REGION` environment variable
4. **Custom Domain**: Add domain configuration to `.chalice/config.json`

## Security Notes

- The IAM policy follows least-privilege principles
- Only necessary DynamoDB and Bedrock permissions are granted
- CloudWatch logging is enabled for monitoring
- API Gateway stage is configurable for different environments

## Data Structure

The service uses a single DynamoDB table with the following structure:

```json
{
  "ProductId": "SKU0009",
  "BasePrice": 123390.5,
  "Breed": "Broiler",
  "LivestockType": "Poultry Broiler",
  "MaxPrice": 134200,
  "MinPrice": 112513,
  "SellerIds": [
    {
      "SellerId": "SELL1024",
      "City": "Kaduna",
      "DeliveryScore": 66.7,
      "Latitude": 10.5105,
      "Longitude": 7.4165,
      "Name": "Farm 1024",
      "Phone": "+2349474852817",
      "PhotoURL": "https://s3.amazonaws.com/bucket/photo_SELL1024.jpg",
      "PriceScore": 0,
      "QuantityTonsAvailable": 14,
      "Rating": 3.8,
      "State": "Kaduna",
      "StockScore": 87.5
    }
  ]
}
```

## Infrastructure Deployment

### Option 1: Using Terraform (Recommended)

1. **Navigate to infrastructure directory:**
   ```bash
   cd infrastructure/terraform
   ```

2. **Copy and edit variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Deploy infrastructure:**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Get table name for Chalice:**
   ```bash
   terraform output chalice_config_update
   ```

### Option 2: Manual DynamoDB Setup

Create a DynamoDB table with:
- **Table Name**: `ai-livestock-matching-dev-marketplace`
- **Primary Key**: `ProductId` (String)
- **Global Secondary Indexes**:
  - `LivestockTypeIndex` with hash key `LivestockType`
  - `BreedIndex` with hash key `Breed`

## Loading Sample Data

After creating the DynamoDB table:

```bash
# Set environment variable
export MARKETPLACE_TABLE_NAME=your-table-name

# Load sample data
python data_loader.py
```

The data loader will:
- Create sample livestock products with embedded seller information
- Load data into your DynamoDB table
- Verify the data was loaded correctly
- Test the indexes