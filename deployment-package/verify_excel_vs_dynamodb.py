"""
Verify that DynamoDB table data matches the Excel dataset
"""
import boto3
import openpyxl
import os
from decimal import Decimal
from collections import defaultdict

# Configuration
AWS_REGION = 'us-east-1'
TABLE_NAME = 'livestock-matching-table'
SELLERS_EXCEL_FILE = '../data/datasets/sellers_dataset.xlsx'

# AWS setup
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

print("🔍 Verifying Excel data vs DynamoDB table data...")

# Load Excel data
excel_path = os.path.join(os.path.dirname(__file__), SELLERS_EXCEL_FILE)
wb = openpyxl.load_workbook(excel_path)
sheet = wb['Sheet1']

# Extract Excel data
excel_data = []
headers = [cell.value for cell in sheet[1] if cell.value]
for row in sheet.iter_rows(min_row=2, values_only=True):
    row_dict = {headers[i]: value for i, value in enumerate(row) if i < len(headers)}
    if row_dict.get('SellerID'):
        excel_data.append(row_dict)

print(f"📊 Excel file contains {len(excel_data)} rows")

# Group Excel data by ProductID
excel_products = defaultdict(lambda: {'sellers': set(), 'prices': [], 'species': None, 'breed': None})
for entry in excel_data:
    product_id = entry['ProductID']
    excel_products[product_id]['sellers'].add(entry['SellerID'])
    excel_products[product_id]['prices'].append(entry['UnitPrice'])
    excel_products[product_id]['species'] = entry['Species']
    excel_products[product_id]['breed'] = entry['Breed']

print(f"📦 Excel contains {len(excel_products)} unique products")

# Get DynamoDB data
dynamodb_items = []
try:
    response = table.scan()
    dynamodb_items = response['Items']
    
    # Handle pagination if needed
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        dynamodb_items.extend(response['Items'])
        
except Exception as e:
    print(f"❌ Error reading DynamoDB: {str(e)}")
    exit(1)

print(f"🗄️  DynamoDB contains {len(dynamodb_items)} items")

# Verification checks
print("\n🔍 Verification Results:")

# Check 1: Product count match
if len(excel_products) == len(dynamodb_items):
    print("✅ Product count matches")
else:
    print(f"❌ Product count mismatch: Excel={len(excel_products)}, DynamoDB={len(dynamodb_items)}")

# Check 2: Verify specific products exist
sample_checks = ['SKU0009', 'SKU0035', 'SKU0001']
for product_id in sample_checks:
    if product_id in excel_products:
        # Find in DynamoDB
        dynamodb_item = None
        for item in dynamodb_items:
            if item.get('ProductId') == product_id:
                dynamodb_item = item
                break
        
        if dynamodb_item:
            excel_product = excel_products[product_id]
            
            # Check breed and species
            if (str(dynamodb_item.get('Breed')) == str(excel_product['breed']) and 
                f"{excel_product['species']} {excel_product['breed']}" == str(dynamodb_item.get('LivestockType'))):
                print(f"✅ {product_id}: Breed and species match")
            else:
                print(f"❌ {product_id}: Breed/species mismatch")
                print(f"   Excel: {excel_product['species']} {excel_product['breed']}")
                print(f"   DynamoDB: {dynamodb_item.get('LivestockType')}")
            
            # Check seller count
            excel_seller_count = len(excel_product['sellers'])
            dynamodb_seller_count = len(dynamodb_item.get('SellerIds', []))
            if excel_seller_count == dynamodb_seller_count:
                print(f"✅ {product_id}: Seller count matches ({excel_seller_count})")
            else:
                print(f"❌ {product_id}: Seller count mismatch - Excel: {excel_seller_count}, DynamoDB: {dynamodb_seller_count}")
            
            # Check price range
            excel_min_price = min(excel_product['prices'])
            excel_max_price = max(excel_product['prices'])
            dynamodb_min_price = float(dynamodb_item.get('MinPrice', 0))
            dynamodb_max_price = float(dynamodb_item.get('MaxPrice', 0))
            
            if (abs(excel_min_price - dynamodb_min_price) < 0.01 and 
                abs(excel_max_price - dynamodb_max_price) < 0.01):
                print(f"✅ {product_id}: Price range matches")
            else:
                print(f"❌ {product_id}: Price range mismatch")
                print(f"   Excel: {excel_min_price} - {excel_max_price}")
                print(f"   DynamoDB: {dynamodb_min_price} - {dynamodb_max_price}")
        else:
            print(f"❌ {product_id}: Not found in DynamoDB")
    else:
        print(f"❌ {product_id}: Not found in Excel")

# Check 3: Verify seller data structure
print(f"\n👥 Seller Data Verification:")
sample_item = dynamodb_items[0]
if 'SellerIds' in sample_item and len(sample_item['SellerIds']) > 0:
    sample_seller = sample_item['SellerIds'][0]
    required_fields = ['SellerId', 'Name', 'Phone', 'City', 'State', 'Latitude', 'Longitude', 
                      'Rating', 'QuantityTonsAvailable', 'PhotoURL', 'StockScore', 'PriceScore', 'DeliveryScore']
    
    missing_fields = [field for field in required_fields if field not in sample_seller]
    if not missing_fields:
        print("✅ All required seller fields present")
    else:
        print(f"❌ Missing seller fields: {missing_fields}")
        
    # Check if seller data comes from Excel
    sample_product_id = sample_item['ProductId']
    excel_sellers_for_product = [entry['SellerID'] for entry in excel_data if entry['ProductID'] == sample_product_id]
    dynamodb_sellers_for_product = [seller['SellerId'] for seller in sample_item['SellerIds']]
    
    if set(excel_sellers_for_product) == set(dynamodb_sellers_for_product):
        print(f"✅ Seller IDs match for {sample_product_id}")
    else:
        print(f"❌ Seller ID mismatch for {sample_product_id}")
        print(f"   Excel: {excel_sellers_for_product}")
        print(f"   DynamoDB: {dynamodb_sellers_for_product}")

print(f"\n📋 Summary:")
print(f"Excel file path: {excel_path}")
print(f"DynamoDB table: {TABLE_NAME}")
print(f"Data source verification: {'✅ CONFIRMED' if len(excel_products) == len(dynamodb_items) else '❌ ISSUES FOUND'}")