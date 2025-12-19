# Livestock Marketplace DynamoDB Infrastructure

This Terraform configuration creates the necessary DynamoDB tables for the livestock marketplace application.

## Tables Created

### LivestockProducts
- **Primary Key**: ProductId (String)
- **GSI**: SpeciesIndex (Species), LivestockTypeIndex (LivestockType)
- **Attributes**: ProductId, LivestockType, Species, Breed, BasePrice, MinPrice, MaxPrice, SellerIds

### LivestockSellers
- **Primary Key**: SellerId (String)
- **GSI**: CityIndex (City), StateIndex (State)
- **Attributes**: SellerId, Name, Phone, City, State, Latitude, Longitude, Rating, QuantityTonsAvailable, PhotoURL, StockScore, PriceScore, DeliveryScore

## Usage

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your specific values

3. Initialize and apply:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## Features

- Pay-per-request billing mode for cost optimization
- Point-in-time recovery enabled
- Server-side encryption enabled
- Global Secondary Indexes for efficient querying
- Environment-specific naming
- Comprehensive tagging strategy

## Outputs

- Table names and ARNs for both tables
- Use these outputs in your application configuration