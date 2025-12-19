# AI-Powered Livestock Matching Service

A serverless AWS application that matches livestock buyers with sellers using AI-powered natural language processing. Built with AWS Chalice, DynamoDB, and Terraform.

## Architecture

- **API**: AWS Chalice (Python serverless framework)
- **Database**: DynamoDB single table design
- **Infrastructure**: Terraform for AWS resource management
- **Data**: Excel-based livestock and seller information

## Features

- Natural language query processing for livestock searches
- Real-time seller matching based on location, price, and product type
- Relevance scoring algorithm for optimal seller recommendations
- RESTful API with health checks and product listings
- Scalable serverless architecture

## Data Structure

### Products
Each product in the DynamoDB table has the following structure:
```json
{
  "ProductName": "Broiler",
  "Species": "Poultry", 
  "BasePrice": 123390.5,
  "MinPrice": 112513.0,
  "MaxPrice": 134268.0,
  "SellerIds": [...]
}
```

### Sellers
Embedded seller information includes:
```json
{
  "SellerId": "SELL1006",
  "Name": "Farm 1006",
  "City": "Ibadan",
  "State": "Oyo",
  "Phone": "+2347739699689",
  "Rating": 4.1,
  "QuantityTonsAvailable": 9.0,
  "StockScore": 100.0,
  "PriceScore": 100.0,
  "DeliveryScore": 33.3
}
```

## Available Products

- **Poultry**: Broiler, Layer, Noiler
- **Fish**: Tilapia, Catfish, Heterotis  
- **Cattle**: Sokoto Gudali, White Fulani, Muturu
- **Sheep**: Yankasa, Balami, Uda
- **Goat**: Sokoto Red

## Quick Start

### Prerequisites
- Python 3.8+
- AWS CLI configured
- Terraform installed
- AWS account with appropriate permissions

### 1. Deploy Infrastructure
```bash
cd deployment-package/infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### 2. Load Sample Data
```bash
cd data/data_loader
python single_table_loader.py
```

### 3. Deploy Chalice Application
```bash
cd deployment-package
chalice deploy
```

## API Endpoints

### Search Livestock
```http
POST /search
Content-Type: application/json

{
  "query": "Find broiler sellers in Lagos under ₦130000"
}
```

### List Products
```http
GET /products
```

### Health Check
```http
GET /health
```

## Example Queries

- "Find broiler sellers in Lagos"
- "Show me tilapia farmers under ₦200000"
- "Get cattle sellers in Kaduna"
- "Find poultry suppliers with good ratings"

## Project Structure

```
├── ai-matching-service/          # Original Chalice app
├── data/
│   ├── datasets/                 # Excel data files
│   └── data_loader/             # Data loading scripts
├── deployment-package/           # Production deployment
│   ├── app.py                   # Main Chalice application
│   ├── data_loader.py           # Data loading utility
│   ├── infrastructure/          # Terraform configurations
│   └── .chalice/               # Chalice configuration
├── infrastructure/              # Additional infrastructure
└── tests/                      # Test files and results
```

## Configuration

### Environment Variables
- `LIVESTOCK_TABLE_NAME`: DynamoDB table name (default: livestock-matching-table)
- `AWS_DEFAULT_REGION`: AWS region (default: us-east-1)

### AWS Resources Created
- DynamoDB table: `livestock-matching-table`
- Lambda functions via Chalice
- API Gateway endpoints
- IAM roles and policies

## Data Statistics

- **Total Products**: 13 unique livestock products
- **Total Sellers**: 14 unique sellers across Nigeria
- **Total Seller Instances**: 19 (some sellers offer multiple products)
- **Coverage**: Major Nigerian cities including Lagos, Abuja, Kaduna, Port Harcourt

## Development

### Running Locally
```bash
cd deployment-package
chalice local
```

### Testing
```bash
# Verify data structure
cd data/data_loader
python verify_product_names.py

# Test API endpoints
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find broiler sellers in Lagos"}'
```

## Deployment Scripts

- `deploy.sh` / `deploy.bat`: Deploy Chalice app only
- `deploy-full-stack.sh` / `deploy-full-stack.bat`: Deploy infrastructure + app + data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the GitHub repository.