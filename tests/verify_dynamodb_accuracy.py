#!/usr/bin/env python3

import boto3
import requests
import json
import os
from typing import Dict, List, Any
from collections import defaultdict

# AWS credentials should be set via environment variables or AWS CLI
# os.environ['AWS_ACCESS_KEY_ID'] = 'your-access-key-id'
# os.environ['AWS_SECRET_ACCESS_KEY'] = 'your-secret-access-key'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

API_URL = "https://mxu25s1yia.execute-api.eu-west-1.amazonaws.com/api"

class DynamoDBVerifier:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        self.products_table = self.dynamodb.Table('livestock-marketplace-dev-livestock-products')
        self.sellers_table = self.dynamodb.Table('livestock-marketplace-dev-livestock-sellers')
        
        # Cache for database data
        self.db_products = None
        self.db_sellers = None
        
    def load_database_data(self):
        """Load all data from DynamoDB tables"""
        print("📊 Loading DynamoDB data...")
        
        # Load products
        products_response = self.products_table.scan()
        self.db_products = products_response['Items']
        
        # Load sellers
        sellers_response = self.sellers_table.scan()
        self.db_sellers = sellers_response['Items']
        
        print(f"✅ Loaded {len(self.db_products)} products and {len(self.db_sellers)} sellers")
        
    def get_database_stats(self):
        """Get comprehensive database statistics"""
        if not self.db_products or not self.db_sellers:
            self.load_database_data()
            
        stats = {
            'total_products': len(self.db_products),
            'total_sellers': len(self.db_sellers),
            'livestock_types': {},
            'locations': {},
            'sellers_by_location': defaultdict(list),
            'products_by_type': defaultdict(list)
        }
        
        # Analyze products
        for product in self.db_products:
            livestock_type = product.get('LivestockType', 'Unknown')
            stats['livestock_types'][livestock_type] = stats['livestock_types'].get(livestock_type, 0) + 1
            stats['products_by_type'][livestock_type].append(product)
            
        # Analyze sellers
        for seller in self.db_sellers:
            location = seller.get('City', 'Unknown')
            stats['locations'][location] = stats['locations'].get(location, 0) + 1
            stats['sellers_by_location'][location].append(seller)
            
        return stats
    
    def verify_query_accuracy(self, query: str, api_response: Dict) -> Dict[str, Any]:
        """Verify API response accuracy against database"""
        if not self.db_products or not self.db_sellers:
            self.load_database_data()
            
        verification = {
            'query': query,
            'api_sellers_count': len(api_response.get('sellers', [])),
            'verification_passed': False,
            'issues': [],
            'details': {}
        }
        
        # Extract query parameters (simplified)
        query_lower = query.lower()
        
        # Check for livestock type
        livestock_type = None
        for product in self.db_products:
            product_type = product.get('LivestockType', '')
            if product_type.lower() in query_lower:
                livestock_type = product_type
                break
                
        # Check for location
        location = None
        for seller in self.db_sellers:
            seller_city = seller.get('City', '')
            if seller_city.lower() in query_lower:
                location = seller_city
                break
                
        verification['details']['extracted_livestock'] = livestock_type
        verification['details']['extracted_location'] = location
        
        # Calculate expected results from database
        expected_sellers = self._calculate_expected_sellers(livestock_type, location)
        verification['details']['expected_sellers_count'] = len(expected_sellers)
        verification['details']['expected_sellers'] = [s.get('Name', 'Unknown') for s in expected_sellers[:5]]
        
        # Compare with API response
        api_sellers = api_response.get('sellers', [])
        verification['details']['api_sellers'] = [s.get('farm_name', 'Unknown') for s in api_sellers[:5]]
        
        # Verify accuracy
        expected_count = len(expected_sellers)
        actual_count = len(api_sellers)
        
        # Allow some tolerance for complex queries
        tolerance = max(1, expected_count * 0.1)  # 10% tolerance
        
        if abs(expected_count - actual_count) <= tolerance:
            verification['verification_passed'] = True
        else:
            verification['issues'].append(f"Count mismatch: expected ~{expected_count}, got {actual_count}")
            
        # Verify seller names match
        if api_sellers and expected_sellers:
            api_names = set(s.get('farm_name', '') for s in api_sellers)
            expected_names = set(s.get('Name', '') for s in expected_sellers)
            
            # Check if there's reasonable overlap
            overlap = len(api_names.intersection(expected_names))
            overlap_ratio = overlap / min(len(api_names), len(expected_names)) if min(len(api_names), len(expected_names)) > 0 else 0
            
            verification['details']['name_overlap_ratio'] = overlap_ratio
            
            if overlap_ratio < 0.5:  # Less than 50% overlap
                verification['issues'].append(f"Low name overlap: {overlap_ratio:.1%}")
                
        return verification
    
    def _calculate_expected_sellers(self, livestock_type: str, location: str) -> List[Dict]:
        """Calculate expected sellers based on database data"""
        expected_sellers = []
        
        if livestock_type:
            # Find products of this type
            matching_products = [p for p in self.db_products if p.get('LivestockType') == livestock_type]
            
            # Get all seller IDs from matching products
            seller_ids = set()
            for product in matching_products:
                seller_ids.update(product.get('SellerIds', []))
                
            # Get seller details
            for seller in self.db_sellers:
                if seller.get('SellerId') in seller_ids:
                    if not location or seller.get('City') == location:
                        expected_sellers.append(seller)
        elif location:
            # Location-only query
            expected_sellers = [s for s in self.db_sellers if s.get('City') == location]
        else:
            # Generic query - return all sellers
            expected_sellers = self.db_sellers
            
        return expected_sellers
    
    def run_comprehensive_verification(self):
        """Run verification on key test queries"""
        print("\n🔍 COMPREHENSIVE DYNAMODB VERIFICATION")
        print("=" * 80)
        
        # Get database statistics first
        stats = self.get_database_stats()
        
        print(f"\n📊 Database Overview:")
        print(f"  Total Products: {stats['total_products']}")
        print(f"  Total Sellers: {stats['total_sellers']}")
        print(f"  Livestock Types: {len(stats['livestock_types'])}")
        print(f"  Locations: {len(stats['locations'])}")
        
        print(f"\n🐄 Livestock Types in Database:")
        for livestock_type, count in sorted(stats['livestock_types'].items()):
            print(f"  {livestock_type}: {count} products")
            
        print(f"\n🏙️  Locations in Database:")
        for location, count in sorted(stats['locations'].items()):
            print(f"  {location}: {count} sellers")
        
        # Test key queries
        test_queries = [
            "Find goats in Kaduna",
            "Show me cattle sellers", 
            "I need poultry suppliers",
            "Find fish sellers",
            "Show me sheep suppliers",
            "Find livestock in Lagos",
            "Show me sellers in Kaduna",
            "I need suppliers in Abuja",
            "Find Cattle Sokoto Gudali",
            "Show me Fish Tilapia",
            "I need Poultry Broiler",
            "Find Goat Sokoto Red",
            "Show me Sheep Yankasa"
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} Key Queries:")
        print("-" * 80)
        
        verification_results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"[{i:2d}/{len(test_queries)}] Testing: {query}")
            
            try:
                # Get API response
                response = requests.post(f"{API_URL}/search", json={"query": query})
                
                if response.status_code == 200:
                    api_data = response.json()
                    verification = self.verify_query_accuracy(query, api_data)
                    verification_results.append(verification)
                    
                    # Print results
                    status = "✅" if verification['verification_passed'] else "❌"
                    print(f"    {status} API: {verification['api_sellers_count']} sellers")
                    print(f"    📊 DB Expected: {verification['details']['expected_sellers_count']} sellers")
                    
                    if verification['issues']:
                        for issue in verification['issues']:
                            print(f"    ⚠️  {issue}")
                    
                    # Show sample results
                    if verification['details']['api_sellers']:
                        print(f"    🏪 API Sellers: {', '.join(verification['details']['api_sellers'])}")
                    if verification['details']['expected_sellers']:
                        print(f"    🏪 DB Sellers: {', '.join(verification['details']['expected_sellers'])}")
                        
                else:
                    print(f"    ❌ API Error: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                
            print()
        
        # Summary
        passed_verifications = sum(1 for v in verification_results if v['verification_passed'])
        total_verifications = len(verification_results)
        
        print("=" * 80)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Total Queries Tested: {total_verifications}")
        print(f"Verifications Passed: {passed_verifications}")
        print(f"Accuracy Rate: {passed_verifications/total_verifications*100:.1f}%")
        
        if passed_verifications == total_verifications:
            print("🌟 VERDICT: All API responses accurately reflect DynamoDB data!")
        elif passed_verifications >= total_verifications * 0.9:
            print("✅ VERDICT: API responses are highly accurate with minor discrepancies")
        else:
            print("⚠️  VERDICT: Significant discrepancies found - investigation needed")
            
        # Show failed verifications
        failed_verifications = [v for v in verification_results if not v['verification_passed']]
        if failed_verifications:
            print(f"\n❌ Failed Verifications ({len(failed_verifications)}):")
            for v in failed_verifications:
                print(f"  Query: {v['query']}")
                for issue in v['issues']:
                    print(f"    Issue: {issue}")
                    
        return verification_results

def main():
    verifier = DynamoDBVerifier()
    results = verifier.run_comprehensive_verification()
    
    # Save results
    with open('dynamodb_verification_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: dynamodb_verification_results.json")

if __name__ == "__main__":
    main()