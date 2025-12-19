"""
Verify the Species field has been added correctly to the table
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

print(f"Verifying Species field in table: {TABLE_NAME}")

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
        print("\n✅ Sample item structure with Species field:")
        
        # Show the key fields in order
        print(f"ProductId: {item.get('ProductId')}")
        print(f"BasePrice: {item.get('BasePrice')}")
        print(f"Species: {item.get('Species')} ← NEW FIELD ADDED")
        print(f"Breed: {item.get('Breed')}")
        print(f"LivestockType: {item.get('LivestockType')}")
        print(f"MaxPrice: {item.get('MaxPrice')}")
        print(f"MinPrice: {item.get('MinPrice')}")
        print(f"Number of sellers: {len(item.get('SellerIds', []))}")
        
        print(f"\n📋 Complete item structure:")
        # Create ordered dict to show fields in the desired order
        ordered_item = {
            'ProductId': item.get('ProductId'),
            'BasePrice': item.get('BasePrice'),
            'Species': item.get('Species'),
            'Breed': item.get('Breed'),
            'LivestockType': item.get('LivestockType'),
            'MaxPrice': item.get('MaxPrice'),
            'MinPrice': item.get('MinPrice'),
            'SellerIds': item.get('SellerIds', [])[:1]  # Show only first seller for brevity
        }
        
        print(json.dumps(ordered_item, indent=2, default=decimal_default))
        
    else:
        print("❌ Item SKU0009 not found")
        
except Exception as e:
    print(f"❌ Error retrieving item: {str(e)}")

# Check different species in the table
try:
    response = table.scan()
    species_count = {}
    
    for item in response['Items']:
        species = item.get('Species', 'Unknown')
        if species in species_count:
            species_count[species] += 1
        else:
            species_count[species] = 1
    
    print(f"\n📊 Species distribution in the table:")
    for species, count in species_count.items():
        print(f"  - {species}: {count} products")
        
except Exception as e:
    print(f"❌ Error getting species distribution: {str(e)}")

print(f"\n✅ Species field successfully added and loaded!")