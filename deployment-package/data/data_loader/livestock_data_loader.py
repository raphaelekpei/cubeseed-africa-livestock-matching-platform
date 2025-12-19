import boto3
import openpyxl
import random
import os
from decimal import Decimal
from collections import defaultdict

# Load environment variables if .env file exists
try:
    import load_env
except ImportError:
    pass

from config import AWS_REGION, PRODUCTS_TABLE_NAME, SELLERS_TABLE_NAME, SELLERS_EXCEL_FILE

# AWS setup
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
products_table = dynamodb.Table(PRODUCTS_TABLE_NAME)
sellers_table = dynamodb.Table(SELLERS_TABLE_NAME)

# Nigerian cities with coords (expand as needed)
cities = [
    {'City': 'Kaduna', 'State': 'Kaduna', 'Lat': 10.5105, 'Long': 7.4165},
    {'City': 'Zaria', 'State': 'Kaduna', 'Lat': 11.0855, 'Long': 7.7199},
    {'City': 'Lagos', 'State': 'Lagos', 'Lat': 6.5244, 'Long': 3.3792},
    {'City': 'Abuja', 'State': 'FCT', 'Lat': 9.0765, 'Long': 7.3986},
    # Add 10-20 more for variety
]

# Load Excel

wb = openpyxl.load_workbook(SELLERS_EXCEL_FILE)
sheet = wb['Sheet1']
data = []
headers = [cell.value for cell in sheet[1] if cell.value]
for row in sheet.iter_rows(min_row=2, values_only=True):
    row_dict = {headers[i]: value for i, value in enumerate(row) if i < len(headers)}
    if row_dict.get('SellerID'):  # Skip empty
        data.append(row_dict)

# Group for Products table
products_dict = defaultdict(lambda: {'SellerIds': [], 'UnitPrices': []})
seller_data = defaultdict(dict)  # For Sellers table

for entry in data:
    product_id = entry['ProductID']
    seller_id = entry['SellerID']
    livestock_type = f"{entry['Species']} {entry['Breed']}"
    
    # Products aggregation
    products_dict[product_id]['SellerIds'].append(seller_id)
    products_dict[product_id]['LivestockType'] = livestock_type  # Assume consistent per product
    products_dict[product_id]['Species'] = entry['Species']
    products_dict[product_id]['Breed'] = entry['Breed']
    products_dict[product_id]['UnitPrices'].append(entry['UnitPrice'])
    
    # Sellers aggregation (take first occurrence for shared fields)
    if not seller_data[seller_id]:
        city = random.choice(cities)
        seller_data[seller_id] = {
            'SellerId': seller_id,
            'Name': f"Farm {seller_id.replace('SELL', '')}",  # Convert SELL1024 to Farm 1024
            'Phone': f"+234{random.randint(1000000000, 9999999999)}",  # Placeholder
            'City': city['City'],
            'State': city['State'],
            'Latitude': Decimal(str(city['Lat'])),
            'Longitude': Decimal(str(city['Long'])),
            'Rating': Decimal(str(entry['Seller_Avg_Rating'] or 0)),
            'QuantityTonsAvailable': Decimal(str(entry['Quantity'] or 0)),  # Per product max; update if multi
            'PhotoURL': f"https://s3.amazonaws.com/bucket/photo_{seller_id}.jpg",  # Placeholder
            # Add scores if needed for matching
            'StockScore': Decimal(str(entry['StockScore'] or 0)),
            'PriceScore': Decimal(str(entry['PriceScore'] or 0)),
            'DeliveryScore': Decimal(str(entry['DeliveryScore'] or 0))
        }
    # Update quantity if higher
    seller_data[seller_id]['QuantityTonsAvailable'] = max(
        seller_data[seller_id]['QuantityTonsAvailable'], Decimal(str(entry['Quantity'] or 0))
    )

# Load Sellers table
for seller in seller_data.values():
    sellers_table.put_item(Item=seller)

# Load Products table
for product_id, info in products_dict.items():
    min_price = min(info['UnitPrices'])
    max_price = max(info['UnitPrices'])
    products_table.put_item(Item={
        'ProductId': product_id,
        'LivestockType': info['LivestockType'],
        'Species': info['Species'],
        'Breed': info['Breed'],
        'BasePrice': Decimal(str(sum(info['UnitPrices']) / len(info['UnitPrices']))),  # Average
        'MinPrice': Decimal(str(min_price)),
        'MaxPrice': Decimal(str(max_price)),
        'SellerIds': list(set(info['SellerIds']))  # Dedupe
    })

print("Data loaded successfully!")