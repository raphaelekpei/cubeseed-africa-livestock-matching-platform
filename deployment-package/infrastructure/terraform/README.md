# AI Livestock Matching Service - Infrastructure

This Terraform configuration creates the necessary DynamoDB tables for the AI Livestock Matching Service.

## Table Created

### Marketplace Table: `{project}-{environment}-marketplace`
- **Primary Key**: ProductId (String)
- **GSI**: LivestockTypeIndex (LivestockType), BreedIndex (Breed)
- **Structure**: Each item contains product information with embedded seller details
- **Sample Data Format**:
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

## Quick Start

1. **Copy the example variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit `terraform.tfvars` with your specific values:**
   ```hcl
   aws_region  = "your-region"
   environment = "dev"
   project     = "your-project-name"
   
   common_tags = {
     Project     = "your-project-name"
     Environment = "dev"
     Owner       = "your-team"
   }
   ```

3. **Initialize and apply:**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Get table names for Chalice configuration:**
   ```bash
   terraform output chalice_config_update
   ```

## Integration with Chalice

After running Terraform, use the outputs to update your Chalice configuration:

1. **Get the table names:**
   ```bash
   terraform output -json chalice_config_update
   ```

2. **Update `.chalice/config.json`** with the table names from the output

3. **Update `.chalice/policy-dev.json`** with the table ARNs:
   ```bash
   terraform output -json iam_policy_arns
   ```

## Features

- **Pay-per-request billing** for cost optimization
- **Point-in-time recovery** enabled for data protection
- **Server-side encryption** enabled by default
- **Global Secondary Indexes** for efficient querying
- **Environment-specific naming** to avoid conflicts
- **Comprehensive tagging** strategy for resource management

## Table Naming Convention

The table is named using the pattern: `{project}-{environment}-marketplace`

Example:
- `ai-livestock-matching-dev-marketplace`

## Customization

### Change Project Name
Update the `project` variable in `terraform.tfvars`:
```hcl
project = "my-custom-livestock-app"
```

### Change Environment
Update the `environment` variable:
```hcl
environment = "production"
```

### Change Region
Update the `aws_region` variable:
```hcl
aws_region = "eu-west-1"
```

## Outputs

The Terraform configuration provides several useful outputs:

- **Table name and ARN** for the DynamoDB table
- **Chalice configuration** values ready to copy
- **IAM policy ARNs** for security configuration

## Cost Considerations

- Tables use **pay-per-request** billing mode
- **Point-in-time recovery** adds ~20% to storage costs
- **Global Secondary Indexes** consume additional read/write capacity
- Consider switching to **provisioned capacity** for predictable workloads

## Security

- **Server-side encryption** enabled by default
- **Point-in-time recovery** for data protection
- Use **least-privilege IAM policies** (provided in outputs)
- Consider enabling **DynamoDB Streams** for audit logging

## Troubleshooting

### Common Issues

1. **Table already exists**: Change the `project` or `environment` variable
2. **Insufficient permissions**: Ensure your AWS credentials have DynamoDB permissions
3. **Region mismatch**: Verify `aws_region` matches your AWS CLI configuration

### Useful Commands

```bash
# View current state
terraform show

# Destroy infrastructure
terraform destroy

# Format configuration files
terraform fmt

# Validate configuration
terraform validate
```