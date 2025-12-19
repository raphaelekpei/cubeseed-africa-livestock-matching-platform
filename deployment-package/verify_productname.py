"""
Verify the ProductName field has been updated correctly
"""
import boto3
import json
from decimal import Decimal

# Configuration
AWS_REGION = 'us-east-1'
TABLE_NAME = 'livestock-matching-table'

# AWS setup
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

print(f"Verifying ProductName field in table: {TABLE_NAME}")

# Get a sample item to show the structure
try:
    response = table.get_item(
        Key={
            'PK': 'PRODUCT#SKU0009',
            'SK': 'PRODUCT#SKU0009'
        }
    )
    
    if 'Item' in response:
        item = response['Item']
        print("\n✅ Sample item structure with ProductName field:")
        
        # Show the key fields in order
        print(f"ProductName: {item.get('ProductName')} ← CHANGED FROM ProductId")
        print(f"BasePrice: {item.get('BasePrice')}")
        print(f"Species: {item.get('Species')}")
        print(f"Breed: {item.get('Breed')}")
        print(f"LivestockType: {item.get('LivestockType')}")
        print(f"MaxPrice: {item.get('MaxPrice')}")
        print(f"MinPrice: {item.get('MinPrice')}")
        print(f"Number of sellers: {len(item.get('SellerIds', []))}")
        
        print(f"\n📋 Complete item structure:")
        # Create ordered dict to show fields in the desired order
        ordered_item = {
            'ProductName': item.get('ProductName'),
            'BasePrice': item.get('BasePrice'),
            'Species': item.get('Species'),
            'Breed': item.get('Breed'),
            'LivestockType': item.get('LivestockType'),
            'MaxPrice': item.get('MaxPrice'),
            'MinPrice': item.get('MinPrice'),
            'SellerIds': item.get('SellerIds', [])[:1]  # Show only first seller for brevity
        }
        
        print(json.dumps(ordered_item, indent=2, default=decimal_default))
        
        # Verify ProductId field does not exist
        if 'ProductId' in item:
            print("\n⚠️ WARNING: ProductId field still exists in the item!")
        else:
            print("\n✅ Confirmed: ProductId field has been removed, ProductName is now used")
        
    else:
        print("❌ Item SKU0009 not found")
        
except Exception as e:
    print(f"❌ Error retrieving item: {str(e)}")

# Check all items to ensure ProductName is used consistently
try:
    response = table.scan()
    items_with_productname = 0
    items_with_productid = 0
    
    for item in response['Items']:
        if 'ProductName' in item:
            items_with_productname += 1
        if 'ProductId' in item:
            items_with_productid += 1
    
    print(f"\n📊 Field usage across all items:")
    print(f"  - Items with ProductName: {items_with_productname}")
    print(f"  - Items with ProductId: {items_with_productid}")
    
    if items_with_productid == 0 and items_with_productname == response['Count']:
        print(f"\n✅ All {response['Count']} items successfully use ProductName field!")
    else:
        print(f"\n⚠️ Inconsistent field usage detected")
        
except Exception as e:
    print(f"❌ Error checking field usage: {str(e)}")