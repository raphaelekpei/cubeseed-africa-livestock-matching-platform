"""
Verify the loaded data in livestock-matching-table
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

print(f"Verifying data in table: {TABLE_NAME}")

# Get a sample item
try:
    response = table.get_item(
        Key={
            'PK': 'PRODUCT#SKU0009',
            'SK': 'PRODUCT#SKU0009'
        }
    )
    
    if 'Item' in response:
        item = response['Item']
        print("\n✅ Sample item found (SKU0009):")
        print(json.dumps(item, indent=2, default=decimal_default))
        
        print(f"\n📊 Item structure verification:")
        print(f"ProductId: {item.get('ProductId')}")
        print(f"LivestockType: {item.get('LivestockType')}")
        print(f"BasePrice: {item.get('BasePrice')}")
        print(f"MinPrice: {item.get('MinPrice')}")
        print(f"MaxPrice: {item.get('MaxPrice')}")
        print(f"Number of sellers: {len(item.get('SellerIds', []))}")
        
        if item.get('SellerIds'):
            print(f"\n👥 First seller details:")
            first_seller = item['SellerIds'][0]
            print(f"  SellerId: {first_seller.get('SellerId')}")
            print(f"  Name: {first_seller.get('Name')}")
            print(f"  City: {first_seller.get('City')}")
            print(f"  Rating: {first_seller.get('Rating')}")
            print(f"  Phone: {first_seller.get('Phone')}")
    else:
        print("❌ Item SKU0009 not found")
        
except Exception as e:
    print(f"❌ Error retrieving item: {str(e)}")

# Get table item count
try:
    response = table.scan(Select='COUNT')
    print(f"\n📈 Total items in table: {response['Count']}")
except Exception as e:
    print(f"❌ Error getting item count: {str(e)}")

# List a few items
try:
    response = table.scan(Limit=3)
    print(f"\n📋 Sample items in table:")
    for item in response['Items']:
        print(f"  - {item.get('ProductId')} ({item.get('LivestockType')}) - {len(item.get('SellerIds', []))} sellers")
except Exception as e:
    print(f"❌ Error listing items: {str(e)}")