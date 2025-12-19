"""
AI-Powered Livestock Buyer-Seller Matching Service
Built with AWS Chalice - Single Table Design
"""
from chalice import Chalice, Response
import json
import logging
import boto3
import os
import re
from boto3.dynamodb.conditions import Key, Attr
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime

app = Chalice(app_name='livestock-matching-ai')
app.log.setLevel(logging.INFO)

# Custom exceptions
class ValidationError(Exception):
    pass

class ServiceError(Exception):
    pass

# Configuration
def get_config():
    return {
        'aws_region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        'livestock_table_name': os.getenv('LIVESTOCK_TABLE_NAME', 'livestock-matching-table'),
    }

# Matching Service
class LivestockMatchingService:
    def __init__(self):
        self.config = get_config()
        self.dynamodb = boto3.resource('dynamodb', region_name=self.config['aws_region'])
        self.table = self.dynamodb.Table(self.config['livestock_table_name'])
    
    def find_matching_sellers(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            # Get products based on search criteria
            products = self._get_matching_products(params)
            app.log.info(f"Found {len(products)} products")
            
            # Extract and filter sellers from products
            results = self._extract_and_filter_sellers(products, params)
            app.log.info(f"Combined results: {len(results)} matches")
            
            return results[:10]
        except Exception as e:
            app.log.error(f"Error finding matching sellers: {str(e)}")
            return []
    
    def _get_matching_products(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        products = []
        
        product_name = params.get('product_name')
        species = params.get('species')
        
        try:
            if product_name:
                # Get specific product by ProductName (primary key)
                response = self.table.get_item(
                    Key={'ProductName': product_name}
                )
                if 'Item' in response:
                    products.append(response['Item'])
            else:
                # Scan all products and filter by species if specified
                response = self.table.scan()
                all_products = response['Items']
                
                if species:
                    # Filter by species
                    products = [p for p in all_products if p.get('Species') == species]
                else:
                    products = all_products
            
            # Apply price filtering
            price_range = params.get('price_range', {})
            if price_range.get('max'):
                max_price = price_range['max']
                filtered_products = []
                for p in products:
                    min_price = float(p.get('MinPrice', 0))
                    if min_price <= max_price:
                        filtered_products.append(p)
                products = filtered_products
            
        except Exception as e:
            app.log.error(f"Error getting matching products: {str(e)}")
        
        return products
    
    def _extract_and_filter_sellers(self, products: List[Dict], params: Dict) -> List[Dict]:
        all_sellers = []
        location = params.get('location', {}).get('city')
        
        for product in products:
            sellers = product.get('SellerIds', [])
            for seller in sellers:
                # Add product information to seller
                seller_copy = seller.copy()
                seller_copy['ProductName'] = product.get('ProductName')
                seller_copy['Species'] = product.get('Species')
                seller_copy['BasePrice'] = float(product.get('BasePrice', 0))
                seller_copy['MinPrice'] = float(product.get('MinPrice', 0))
                seller_copy['MaxPrice'] = float(product.get('MaxPrice', 0))
                
                # Apply location filter if specified
                if location:
                    seller_city = seller.get('City', '').lower()
                    if location.lower() not in seller_city:
                        continue
                
                # Calculate relevance score
                seller_copy['relevance_score'] = self._calculate_relevance_score(seller_copy)
                all_sellers.append(seller_copy)
        
        # Sort by relevance score
        all_sellers.sort(key=lambda x: x['relevance_score'], reverse=True)
        return all_sellers
    
    def _calculate_relevance_score(self, seller: Dict) -> float:
        score = 0.0
        
        # Rating score (0-5 scale, weight: 40%)
        rating = float(seller.get('Rating', 0))
        score += (rating / 5.0) * 0.40
        
        # Stock score (weight: 30%)
        stock_score = float(seller.get('StockScore', 0))
        score += (stock_score / 100.0) * 0.30
        
        # Price score (weight: 20%)
        price_score = float(seller.get('PriceScore', 0))
        score += (price_score / 100.0) * 0.20
        
        # Delivery score (weight: 10%)
        delivery_score = float(seller.get('DeliveryScore', 0))
        score += (delivery_score / 100.0) * 0.10
        
        return round(score, 3)

# Parameter extraction
def extract_simple_parameters(query: str) -> Dict[str, Any]:
    query_lower = query.lower()
    params = {
        'product_name': None,
        'species': None,
        'location': {},
        'price_range': {}
    }
    
    # Extract product names (breeds)
    product_patterns = [
        ('Broiler', r'\b(broiler|broilers)\b'),
        ('Layer', r'\b(layer|layers)\b'),
        ('Noiler', r'\b(noiler|noilers)\b'),
        ('Tilapia', r'\b(tilapia)\b'),
        ('Catfish', r'\b(catfish|cat fish)\b'),
        ('Heterotis', r'\b(heterotis)\b'),
        ('Sokoto Gudali', r'\b(sokoto gudali|gudali)\b'),
        ('White Fulani', r'\b(white fulani|fulani)\b'),
        ('Muturu', r'\b(muturu)\b'),
        ('Sokoto Red', r'\b(sokoto red)\b'),
        ('Yankasa', r'\b(yankasa)\b'),
        ('Balami', r'\b(balami)\b'),
        ('Uda', r'\b(uda)\b')
    ]
    
    for product_name, pattern in product_patterns:
        if re.search(pattern, query_lower):
            params['product_name'] = product_name
            break
    
    # Extract species
    species_patterns = [
        ('Poultry', r'\b(poultry|chicken|fowl|bird)\b'),
        ('Fish', r'\b(fish)\b'),
        ('Cattle', r'\b(cattle|cow|bull|beef)\b'),
        ('Goat', r'\b(goat)\b'),
        ('Sheep', r'\b(sheep|ram|ewe)\b')
    ]
    
    for species, pattern in species_patterns:
        if re.search(pattern, query_lower):
            params['species'] = species
            break
    
    # Extract location
    location_patterns = [
        r'\bin\s+([a-zA-Z]+)(?:\s+state)?',
        r'(?:from|at)\s+([a-zA-Z]+)(?:\s+state)?'
    ]
    
    valid_locations = [
        'Kaduna', 'Lagos', 'Abuja', 'Kano', 'Ibadan', 
        'Port Harcourt', 'Benin City', 'Maiduguri', 'Jos', 
        'Ilorin', 'Owerri', 'Calabar', 'Sokoto', 'Enugu', 'Zaria'
    ]
    
    for pattern in location_patterns:
        location_match = re.search(pattern, query_lower)
        if location_match:
            location = location_match.group(1).strip().title()
            if any(valid_loc.lower() == location.lower() for valid_loc in valid_locations):
                params['location']['city'] = location
                break
    
    # Extract price
    price_patterns = [
        r'under\s+₦?(\d+(?:,\d+)*)',
        r'below\s+₦?(\d+(?:,\d+)*)',
        r'less\s+than\s+₦?(\d+(?:,\d+)*)',
        r'maximum\s+₦?(\d+(?:,\d+)*)'
    ]
    
    for pattern in price_patterns:
        price_match = re.search(pattern, query_lower)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            try:
                price_value = int(price_str)
                if 1000 <= price_value <= 10000000:
                    params['price_range']['max'] = price_value
            except ValueError:
                pass
            break
    
    return params

def validate_query(query: str) -> None:
    if not query or not query.strip():
        raise ValidationError("Query cannot be empty")
    if len(query) > 500:
        raise ValidationError("Query too long (max 500 characters)")

# Initialize services
matching_service = LivestockMatchingService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'livestock-matching-ai'}

@app.route('/search', methods=['POST'])
def search_livestock():
    """
    Natural language livestock search endpoint
    """
    try:
        request_data = app.current_request.json_body
        query = request_data.get('query', '').strip()
        
        if not query:
            raise ValidationError("Query is required")
        
        validate_query(query)
        
        # Process natural language query
        extracted_params = extract_simple_parameters(query)
        
        # Find matching sellers
        results = matching_service.find_matching_sellers(extracted_params)
        
        # Format results for response
        formatted_results = []
        for seller in results:
            seller_info = {
                'seller_id': seller.get('SellerId'),
                'name': seller.get('Name'),
                'location': f"{seller.get('City')}, {seller.get('State')}",
                'phone': seller.get('Phone'),
                'rating': float(seller.get('Rating', 0)),
                'product_name': seller.get('ProductName'),
                'species': seller.get('Species'),
                'price_range': f"₦{int(seller.get('MinPrice', 0)):,} - ₦{int(seller.get('MaxPrice', 0)):,}",
                'quantity_available': float(seller.get('QuantityTonsAvailable', 0)),
                'relevance_score': seller.get('relevance_score', 0)
            }
            formatted_results.append(seller_info)
        
        return {
            'message': f"Found {len(formatted_results)} matching sellers",
            'query': query,
            'results': formatted_results
        }
        
    except ValidationError as e:
        return Response(
            body={'error': str(e)},
            status_code=400,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        app.log.error(f"Unexpected error: {str(e)}")
        return Response(
            body={'error': 'Internal server error'},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

@app.route('/products', methods=['GET'])
def list_products():
    """
    List all available products
    """
    try:
        response = matching_service.table.scan()
        products = []
        
        for item in response['Items']:
            product_info = {
                'product_name': item.get('ProductName'),
                'species': item.get('Species'),
                'base_price': float(item.get('BasePrice', 0)),
                'price_range': f"₦{int(item.get('MinPrice', 0)):,} - ₦{int(item.get('MaxPrice', 0)):,}",
                'seller_count': len(item.get('SellerIds', []))
            }
            products.append(product_info)
        
        return {
            'message': f"Found {len(products)} products",
            'products': products
        }
        
    except Exception as e:
        app.log.error(f"Error listing products: {str(e)}")
        return Response(
            body={'error': 'Internal server error'},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )