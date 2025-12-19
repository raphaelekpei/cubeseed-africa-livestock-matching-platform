"""
Update ProductName values in livestock-matching-table from SKU to Breed values
"""
import boto3
from decimal import Decimal

# Configuration
AWS_REGION = 'us-east-1'
TABLE_NAME = 'livestock-matching-table'

# AWS setup
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

print(f"Updating ProductName values in table: {TABLE_NAME}")

try:
    # Scan all items in the table
    response = table.scan()
    items = response['Items']
    
    print(f"Found {len(items)} items to update")
    
    updated_count = 0
    
    for item in items:
        # Get the current values
        pk = item['PK']
        sk = item['SK']
        breed = item.get('Breed', 'Unknown')
        
        print(f"Updating {item.get('ProductId', 'Unknown')} -> ProductName: {breed}")
        
        # Update the item with ProductName = Breed
        try:
            table.update_item(
                Key={
                    'PK': pk,
                    'SK': sk
                },
                UpdateExpression='SET ProductName = :breed',
                ExpressionAttributeValues={
                    ':breed': breed
                }
            )
            updated_count += 1
            
        except Exception as e:
            print(f"Error updating item {pk}: {str(e)}")
    
    print(f"\n✅ Update complete!")
    print(f"Successfully updated {updated_count} items")
    
    # Verify a sample item
    print(f"\n🔍 Verifying update...")
    sample_response = table.get_item(
        Key={
            'PK': 'PRODUCT#SKU0009',
            'SK': 'PRODUCT#SKU0009'
        }
    )
    
    if 'Item' in sample_response:
        sample_item = sample_response['Item']
        print(f"Sample verification:")
        print(f"  ProductId: {sample_item.get('ProductId')}")
        print(f"  ProductName: {sample_item.get('ProductName')}")
        print(f"  Breed: {sample_item.get('Breed')}")
        print(f"  LivestockType: {sample_item.get('LivestockType')}")
    
except Exception as e:
    print(f"❌ Error during update: {str(e)}")