import boto3
import openpyxl
import random
import os
from decimal import Decimal
from collections import defaultdict

# Configuration
AWS_REGION = 'us-east-1'
TABLE_NAME = 'livestock-matching-table'
SELLERS_EXCEL_FILE = '../datasets/sellers_dataset.xlsx'

# AWS setup
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

# Nigerian cities with coordinates
cities = [
    {'City': 'Kaduna', 'State': 'Kaduna', 'Lat': 10.5105, 'Long': 7.4165},
    {'City': 'Zaria', 'State': 'Kaduna', 'Lat': 11.0855, 'Long': 7.7199},
    {'City': 'Lagos', 'State': 'Lagos', 'Lat': 6.5244, 'Long': 3.3792},
    {'City': 'Abuja', 'State': 'FCT', 'Lat': 9.0765, 'Long': 7.3986},
    {'City': 'Kano', 'State': 'Kano', 'Lat': 12.0022, 'Long': 8.5920},
    {'City': 'Ibadan', 'State': 'Oyo', 'Lat': 7.3775, 'Long': 3.9470},
    {'City': 'Port Harcourt', 'State': 'Rivers', 'Lat': 4.8156, 'Long': 7.0498},
    {'City': 'Benin City', 'State': 'Edo', 'Lat': 6.3350, 'Long': 5.6037},
    {'City': 'Maiduguri', 'State': 'Borno', 'Lat': 11.8311, 'Long': 13.1510},
    {'City': 'Jos', 'State': 'Plateau', 'Lat': 9.8965, 'Long': 8.8583},
]

print(f"Loading data from {SELLERS_EXCEL_FILE}...")

# Load Excel file
excel_path = os.path.join(os.path.dirname(__file__), SELLERS_EXCEL_FILE)
wb = openpyxl.load_workbook(excel_path)
sheet = wb['Sheet1']

# Extract headers and data
data = []
headers = [cell.value for cell in sheet[1] if cell.value]
for row in sheet.iter_rows(min_row=2, values_only=True):
    row_dict = {headers[i]: value for i, value in enumerate(row) if i < len(headers)}
    if row_dict.get('SellerID'):  # Skip empty rows
        data.append(row_dict)

print(f"Loaded {len(data)} rows from Excel")

# Group data by ProductID and aggregate seller information
products_dict = defaultdict(lambda: {'SellerIds': [], 'UnitPrices': [], 'Sellers': {}})

for entry in data:
    product_id = entry['ProductID']
    seller_id = entry['SellerID']
    livestock_type = f"{entry['Species']} {entry['Breed']}"
    
    # Add to products dictionary
    products_dict[product_id]['LivestockType'] = livestock_type
    products_dict[product_id]['Species'] = entry['Species']
    products_dict[product_id]['Breed'] = entry['Breed']
    products_dict[product_id]['UnitPrices'].append(entry['UnitPrice'])
    
    # Store seller information (only once per seller per product)
    if seller_id not in products_dict[product_id]['Sellers']:
        city = random.choice(cities)
        products_dict[product_id]['Sellers'][seller_id] = {
            'SellerId': seller_id,
            'Name': f"Farm {seller_id.replace('SELL', '')}",
            'Phone': f"+234{random.randint(7000000000, 9999999999)}",
            'City': city['City'],
            'State': city['State'],
            'Latitude': Decimal(str(city['Lat'])),
            'Longitude': Decimal(str(city['Long'])),
            'Rating': Decimal(str(entry['Seller_Avg_Rating'] or 0)),
            'QuantityTonsAvailable': Decimal(str(entry['Quantity'] or 0)),
            'PhotoURL': f"https://s3.amazonaws.com/bucket/photo_{seller_id}.jpg",
            'StockScore': Decimal(str(entry['StockScore'] or 0)),
            'PriceScore': Decimal(str(entry['PriceScore'] or 0)),
            'DeliveryScore': Decimal(str(entry['DeliveryScore'] or 0))
        }

print(f"Processed {len(products_dict)} unique products")

# Clear existing data (optional - comment out if you want to keep existing data)
print("Clearing existing data...")
try:
    # Scan and delete all existing items
    response = table.scan()
    with table.batch_writer() as batch:
        for item in response['Items']:
            batch.delete_item(Key={'ProductName': item['ProductName']})
    print("Existing data cleared")
except Exception as e:
    print(f"Warning: Could not clear existing data: {str(e)}")

# Load data into DynamoDB table
items_loaded = 0
for product_id, info in products_dict.items():
    min_price = min(info['UnitPrices'])
    max_price = max(info['UnitPrices'])
    base_price = sum(info['UnitPrices']) / len(info['UnitPrices'])
    
    # Convert sellers dict to list
    sellers_list = list(info['Sellers'].values())
    
    # Create item with ProductName as the primary key (simplified structure)
    product_name = info['Breed']  # ProductName is now the primary key
    item = {
        'ProductName': product_name,  # ProductName is the primary key
        'Species': info['Species'],  # Add Species field as requested
        'BasePrice': Decimal(str(round(base_price, 2))),
        'MaxPrice': Decimal(str(max_price)),
        'MinPrice': Decimal(str(min_price)),
        'SellerIds': sellers_list
    }
    
    try:
        table.put_item(Item=item)
        items_loaded += 1
        if items_loaded % 10 == 0:
            print(f"Loaded {items_loaded} items...")
    except Exception as e:
        print(f"Error loading {product_id}: {str(e)}")

print(f"\n✅ Data loading complete!")
print(f"Total items loaded: {items_loaded}")
print(f"Table name: {TABLE_NAME}")
print(f"Region: {AWS_REGION}")

# Display sample item
if items_loaded > 0:
    print("\n📋 Sample item structure:")
    sample_product = list(products_dict.keys())[0]
    sample_info = products_dict[sample_product]
    print(f"ProductName (PK): {sample_info['Breed']}")
    print(f"Species: {sample_info['Species']}")
    print(f"Number of sellers: {len(sample_info['Sellers'])}")
    print(f"Price range: {min(sample_info['UnitPrices'])} - {max(sample_info['UnitPrices'])}")

# Verify the data structure
print("\n🔍 Verifying loaded data...")
try:
    # Get a sample item to verify structure
    sample_product_id = list(products_dict.keys())[0]
    sample_product_name = products_dict[sample_product_id]['Breed']
    response = table.get_item(
        Key={
            'ProductName': sample_product_name
        }
    )
    
    if 'Item' in response:
        item = response['Item']
        print(f"✅ Verification successful:")
        print(f"  ProductName (PK): {item.get('ProductName')}")
        print(f"  Species: {item.get('Species')}")
        print(f"  Number of sellers: {len(item.get('SellerIds', []))}")
        print(f"  Has PK field: {'PK' in item}")
        print(f"  Has SK field: {'SK' in item}")
        print(f"  Has GSI fields: {'GSI1PK' in item or 'GSI1SK' in item or 'GSI2PK' in item}")
    else:
        print("❌ Could not verify data structure")
        
except Exception as e:
    print(f"❌ Error during verification: {str(e)}")