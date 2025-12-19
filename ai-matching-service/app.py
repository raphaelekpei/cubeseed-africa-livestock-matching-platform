"""
AI-Powered Livestock Buyer-Seller Matching Service
Built with AWS Chalice and Amazon Bedrock
"""
from chalice import Chalice, Response
import json
import logging
import boto3
import os
import math
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
        'aws_region': os.getenv('AWS_DEFAULT_REGION', 'eu-west-1'),
        'products_table_name': os.getenv('PRODUCTS_TABLE_NAME', 'livestock-marketplace-dev-livestock-products'),
        'sellers_table_name': os.getenv('SELLERS_TABLE_NAME', 'livestock-marketplace-dev-livestock-sellers'),
    }

# Matching Service
class LivestockMatchingService:
    def __init__(self):
        self.config = get_config()
        self.dynamodb = boto3.resource('dynamodb', region_name=self.config['aws_region'])
        self.products_table = self.dynamodb.Table(self.config['products_table_name'])
        self.sellers_table = self.dynamodb.Table(self.config['sellers_table_name'])
    
    def find_matching_sellers(self, params: Dict[str, Any], ignore_location_filter: bool = False) -> List[Dict[str, Any]]:
        try:
            # For location notice logic, we need to get all sellers first, then filter by location later
            if ignore_location_filter:
                # Get all sellers without location filtering
                sellers = self._get_all_sellers()
            else:
                sellers = self._get_filtered_sellers(params)
            app.log.info(f"Found {len(sellers)} sellers")
            
            products = self._get_matching_products(params)
            app.log.info(f"Found {len(products)} products")
            
            results = self._combine_and_rank_results(sellers, products, params)
            app.log.info(f"Combined results: {len(results)} matches")
            
            return results[:10]
        except Exception as e:
            app.log.error(f"Error finding matching sellers: {str(e)}")
            return []
    
    def get_top_rated_sellers(self, livestock_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            response = self.products_table.query(
                IndexName='LivestockTypeIndex',
                KeyConditionExpression=Key('LivestockType').eq(livestock_type)
            )
            
            seller_ids = set()
            for product in response['Items']:
                seller_ids.update(product.get('SellerIds', []))
            
            sellers = []
            for seller_id in list(seller_ids)[:20]:
                try:
                    seller_response = self.sellers_table.get_item(Key={'SellerId': seller_id})
                    if 'Item' in seller_response:
                        seller = seller_response['Item']
                        seller['Rating'] = float(seller.get('Rating', 0))
                        sellers.append(seller)
                except Exception:
                    continue
            
            sellers.sort(key=lambda x: x['Rating'], reverse=True)
            return sellers[:limit]
        except Exception as e:
            app.log.error(f"Error getting top rated sellers: {str(e)}")
            return []
    
    def find_sellers_by_proximity(self, location: str, radius_km: float, livestock_type: str = None) -> List[Dict[str, Any]]:
        try:
            ref_coords = self._get_location_coordinates(location)
            if not ref_coords:
                return []
            
            scan_params = {}
            if livestock_type:
                seller_ids = self._get_seller_ids_by_livestock_type(livestock_type)
                if seller_ids:
                    scan_params['FilterExpression'] = Attr('SellerId').is_in(seller_ids[:100])
            
            response = self.sellers_table.scan(**scan_params)
            
            nearby_sellers = []
            for seller in response['Items']:
                try:
                    seller_lat = float(seller.get('Latitude', 0))
                    seller_lon = float(seller.get('Longitude', 0))
                    
                    distance = self._calculate_distance(
                        ref_coords['lat'], ref_coords['lon'],
                        seller_lat, seller_lon
                    )
                    
                    if distance <= radius_km:
                        seller['distance_km'] = round(distance, 2)
                        nearby_sellers.append(seller)
                except Exception:
                    continue
            
            nearby_sellers.sort(key=lambda x: x['distance_km'])
            return nearby_sellers[:10]
        except Exception as e:
            app.log.error(f"Error finding sellers by proximity: {str(e)}")
            return []
    
    def find_bulk_suppliers(self, livestock_type: str, quantity_tons: float) -> List[Dict[str, Any]]:
        try:
            seller_ids = self._get_seller_ids_by_livestock_type(livestock_type)
            
            bulk_suppliers = []
            for seller_id in seller_ids[:20]:
                try:
                    seller_response = self.sellers_table.get_item(Key={'SellerId': seller_id})
                    if 'Item' in seller_response:
                        seller = seller_response['Item']
                        available_tons = float(seller.get('QuantityTonsAvailable', 0))
                        
                        if available_tons >= quantity_tons:
                            seller['available_tons'] = available_tons
                            seller['surplus_tons'] = available_tons - quantity_tons
                            bulk_suppliers.append(seller)
                except Exception:
                    continue
            
            bulk_suppliers.sort(key=lambda x: x['available_tons'], reverse=True)
            return bulk_suppliers[:10]
        except Exception as e:
            app.log.error(f"Error finding bulk suppliers: {str(e)}")
            return []
    
    def get_popular_products(self) -> List[Dict[str, Any]]:
        try:
            response = self.products_table.scan()
            products = response['Items']
            
            popularity_stats = {}
            for product in products:
                livestock_type = product.get('LivestockType', 'Unknown')
                seller_count = len(product.get('SellerIds', []))
                
                if livestock_type not in popularity_stats:
                    popularity_stats[livestock_type] = {
                        'livestock_type': livestock_type,
                        'total_products': 0,
                        'total_sellers': 0,
                        'avg_price': 0
                    }
                
                stats = popularity_stats[livestock_type]
                stats['total_products'] += 1
                stats['total_sellers'] += seller_count
                
                base_price = float(product.get('BasePrice', 0))
                stats['avg_price'] = (stats['avg_price'] * (stats['total_products'] - 1) + base_price) / stats['total_products']
            
            popular_products = list(popularity_stats.values())
            popular_products.sort(key=lambda x: x['total_sellers'], reverse=True)
            
            return popular_products[:10]
        except Exception as e:
            app.log.error(f"Error getting popular products: {str(e)}")
            return []
    
    def get_analysis_timestamp(self) -> str:
        return datetime.utcnow().isoformat() + 'Z'
    
    def _get_all_sellers(self) -> List[Dict[str, Any]]:
        """Get all sellers without any filtering"""
        try:
            response = self.sellers_table.scan()
            return response['Items']
        except Exception as e:
            app.log.error(f"Error in _get_all_sellers: {str(e)}")
            return []
    
    def _get_filtered_sellers(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        scan_params = {}
        filter_expressions = []
        
        location = params.get('location', {})
        if location.get('city'):
            filter_expressions.append(Attr('City').eq(location['city']))
        
        if filter_expressions:
            scan_params['FilterExpression'] = filter_expressions[0]
        
        try:
            response = self.sellers_table.scan(**scan_params)
            return response['Items']
        except Exception as e:
            app.log.error(f"Error in _get_filtered_sellers: {str(e)}")
            return []
    
    def _get_matching_products(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        products = []
        
        livestock_type = params.get('livestock_type')
        if livestock_type:
            try:
                # Handle generic types for price-based queries
                if livestock_type.startswith('GENERIC_'):
                    # For generic types, find all products of that category
                    all_products_response = self.products_table.scan()
                    category = livestock_type.replace('GENERIC_', '').title()
                    
                    for product in all_products_response['Items']:
                        product_type = product.get('LivestockType', '')
                        if category in product_type:
                            products.append(product)
                else:
                    # First try exact match
                    response = self.products_table.query(
                        IndexName='LivestockTypeIndex',
                        KeyConditionExpression=Key('LivestockType').eq(livestock_type)
                    )
                    products.extend(response['Items'])
                    
                    # If we got exact matches, don't expand further
                    # Only expand for truly generic searches (when no exact match found)
                    if not products:
                        # For generic terms, search for related types
                        all_products_response = self.products_table.scan()
                        for product in all_products_response['Items']:
                            product_type = product.get('LivestockType', '')
                            
                            # Add related types for generic searches
                            if livestock_type == 'Sheep Yankasa' and 'Sheep' in product_type:
                                products.append(product)
                            elif livestock_type == 'Cattle Sokoto Gudali' and 'Cattle' in product_type:
                                products.append(product)
                            elif livestock_type == 'Poultry Broiler' and 'Poultry' in product_type:
                                products.append(product)
                            elif livestock_type == 'Fish Tilapia' and 'Fish' in product_type:
                                products.append(product)
                    
                    # If still no exact match, try partial matches
                    if not products:
                        all_products_response = self.products_table.scan()
                        for product in all_products_response['Items']:
                            product_type = product.get('LivestockType', '').lower()
                            search_type = livestock_type.lower()
                            
                            # Check if any word in the search type matches the product type
                            search_words = search_type.split()
                            for word in search_words:
                                if word in product_type:
                                    products.append(product)
                                    break
                                
            except Exception as e:
                app.log.error(f"Error getting matching products: {str(e)}")
        else:
            # If no livestock type specified, don't return any products
            # This prevents location-only or price-only queries from returning results
            # Exception: if we have price terms but no livestock type, return empty
            price_range = params.get('price_range', {})
            if price_range.get('max') and not livestock_type:
                # Price-only queries without valid livestock type should return empty
                products = []
        
        # Apply price filtering with validation
        price_range = params.get('price_range', {})
        if price_range.get('invalid'):
            # If price is marked as invalid (too low), return no products
            products = []
        elif price_range.get('max'):
            max_price = price_range['max']
            # Filter products by price - use MinPrice for filtering
            filtered_products = []
            for p in products:
                min_price = float(p.get('MinPrice', 0))
                if min_price <= max_price:
                    filtered_products.append(p)
            products = filtered_products
        
        return products
    
    def _combine_and_rank_results(self, sellers: List[Dict], products: List[Dict], params: Dict) -> List[Dict]:
        seller_lookup = {seller['SellerId']: seller for seller in sellers}
        
        # Check if we have valid search criteria
        has_livestock_type = params.get('livestock_type') is not None
        has_location = params.get('location', {}).get('city') is not None
        has_price = params.get('price_range', {}).get('max') is not None
        has_quantity = params.get('quantity', {}).get('amount') is not None
        
        # If no valid search criteria, return empty results
        if not (has_livestock_type or has_location or has_price or has_quantity):
            return []
        
        # If we have products, filter sellers by product matches
        if products:
            product_seller_ids = set()
            for product in products:
                product_seller_ids.update(product.get('SellerIds', []))
            
            results = []
            for seller_id in product_seller_ids:
                if seller_id in seller_lookup:
                    seller = seller_lookup[seller_id].copy()
                    seller_products = [p for p in products if seller_id in p.get('SellerIds', [])]
                    seller['matching_products'] = seller_products
                    seller['relevance_score'] = self._calculate_relevance_score(seller)
                    results.append(seller)
        else:
            # If no products match but we have location criteria, return location-based results
            # BUT only if we don't have an invalid livestock query
            has_invalid_livestock_query = params.get('invalid_livestock_query', False)
            
            if has_location and not has_livestock_type and not has_invalid_livestock_query:
                # For location-only queries, return all sellers in that location with their products
                results = []
                for seller in sellers:
                    seller_copy = seller.copy()
                    # Get all products for this seller
                    seller_products = self._get_products_for_seller(seller['SellerId'])
                    seller_copy['matching_products'] = seller_products
                    seller_copy['relevance_score'] = self._calculate_relevance_score(seller_copy)
                    results.append(seller_copy)
            else:
                # For other cases without products (including invalid livestock queries), return empty results
                results = []
        
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results
    
    def _calculate_relevance_score(self, seller: Dict) -> float:
        score = 0.0
        
        # Rating score (0-5 scale, weight: 35%)
        rating = float(seller.get('Rating', 0))
        score += (rating / 5.0) * 0.35
        
        # Stock score (weight: 25%)
        stock_score = float(seller.get('StockScore', 0))
        score += (stock_score / 100.0) * 0.25
        
        # Price score (weight: 20%)
        price_score = float(seller.get('PriceScore', 0))
        score += (price_score / 100.0) * 0.20
        
        # Delivery score (weight: 15%)
        delivery_score = float(seller.get('DeliveryScore', 0))
        score += (delivery_score / 100.0) * 0.15
        
        # Bonus for having matching products (weight: 5%)
        product_count = len(seller.get('matching_products', []))
        if product_count > 0:
            score += min(product_count / 5.0, 1.0) * 0.05
        
        return round(score, 3)
    
    def _get_seller_ids_by_livestock_type(self, livestock_type: str) -> List[str]:
        try:
            response = self.products_table.query(
                IndexName='LivestockTypeIndex',
                KeyConditionExpression=Key('LivestockType').eq(livestock_type)
            )
            
            seller_ids = set()
            for product in response['Items']:
                seller_ids.update(product.get('SellerIds', []))
            
            return list(seller_ids)
        except Exception:
            return []
    
    def _get_location_coordinates(self, location: str) -> Optional[Dict[str, float]]:
        coordinates = {
            'kaduna': {'lat': 10.5105, 'lon': 7.4165},
            'zaria': {'lat': 11.0855, 'lon': 7.7199},
            'lagos': {'lat': 6.5244, 'lon': 3.3792},
            'abuja': {'lat': 9.0765, 'lon': 7.3986},
            'kano': {'lat': 12.0022, 'lon': 8.5920},
            'ibadan': {'lat': 7.3775, 'lon': 3.9470},
            'port harcourt': {'lat': 4.8156, 'lon': 7.0498},
            'benin city': {'lat': 6.3350, 'lon': 5.6037},
            'maiduguri': {'lat': 11.8311, 'lon': 13.1510},
            'jos': {'lat': 9.8965, 'lon': 8.8583},
            'ilorin': {'lat': 8.5000, 'lon': 4.5500},
            'owerri': {'lat': 5.4844, 'lon': 7.0351},
            'calabar': {'lat': 4.9517, 'lon': 8.3220},
            'sokoto': {'lat': 13.0059, 'lon': 5.2476},
            'enugu': {'lat': 6.5244, 'lon': 7.5086}
        }
        return coordinates.get(location.lower())
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _get_products_for_seller(self, seller_id: str) -> List[Dict]:
        """Get all products for a specific seller"""
        try:
            # Scan all products to find ones that include this seller
            response = self.products_table.scan()
            products = response['Items']
            
            seller_products = []
            for product in products:
                seller_ids = product.get('SellerIds', [])
                if seller_id in seller_ids:
                    seller_products.append(product)
            
            return seller_products
        except Exception as e:
            app.log.error(f"Error getting products for seller {seller_id}: {str(e)}")
            return []

# Enhanced parameter extraction with better validation
def extract_simple_parameters(query: str) -> Dict[str, Any]:
    query_lower = query.lower()
    params = {
        'livestock_type': None,
        'location': {},
        'price_range': {},
        'quantity': {},
        'quality_requirements': {}
    }
    
    # Valid livestock types from database - more specific patterns first
    livestock_patterns = [
        # Exact breed matches first (highest priority)
        ('Goat Sokoto Red', r'\b(goat sokoto red|goats? sokoto red)\b'),
        ('Cattle Sokoto Gudali', r'\b(cattle sokoto gudali)\b'),
        ('Cattle Muturu', r'\b(cattle muturu)\b'),
        ('Cattle White Fulani', r'\b(cattle white fulani)\b'),
        ('Poultry Broiler', r'\b(poultry broiler|broiller)\b'),
        ('Poultry Noiler', r'\b(poultry noiler|noilers?|noiler chickens?|noiller)\b'),
        ('Poultry Layer', r'\b(poultry layer|layers?|layyer)\b'),
        ('Sheep Yankasa', r'\b(sheep yankasa|yankassa)\b'),
        ('Sheep Balami', r'\b(sheep balami|balami sheep|balami|balamy)\b'),
        ('Sheep Uda', r'\b(sheep uda|uda sheep)\b'),
        ('Fish Tilapia', r'\b(fish tilapia|tilapya|tilapiya)\b'),
        ('Fish Catfish', r'\b(fish catfish|catfish|cat fish|catfsh|catfis)\b'),
        ('Fish Heterotis', r'\b(fish heterotis|heterotis|hetrotis)\b'),
        
        # Specific type matches (medium priority) - but use generic for price queries
        ('Poultry Broiler', r'\b(broilers?|chickens?|hens?|fowls?)\b'),
        ('Cattle Sokoto Gudali', r'\b(cattle)\b'),
        ('Fish Tilapia', r'\b(tilapia)\b'),
        
        # Generic matches for price-based queries (use generic types to find all variants)
        ('GENERIC_SHEEP', r'\b(sheep|rams?|ewes?|lambs?)\b'),
        ('GENERIC_GOAT', r'\b(goats?)\b'),
        ('GENERIC_CATTLE', r'\b(cows?|bulls?|beef|bovine)\b'),
        ('GENERIC_POULTRY', r'\b(poultry|birds?)\b'),
        ('GENERIC_FISH', r'\b(fish|fishes)\b')
    ]
    
    # Check for invalid livestock types first (common non-livestock animals)
    invalid_livestock = r'\b(pigs?|horses?|rabbits?|ducks?|turkeys?|guinea fowls?|guinea|donkeys?|camels?|dinosaurs?|dogs?|cats?|elephants?|lions?|unicorns?)\b'
    has_invalid_livestock = bool(re.search(invalid_livestock, query_lower))
    if has_invalid_livestock:
        # Mark as invalid livestock query - return early with no results
        params['livestock_type'] = None
        params['invalid_livestock_query'] = True
        # Don't extract any other parameters for invalid livestock queries
        return params
    else:
        # Check if this is a price-based query (has price terms)
        has_price_terms = bool(re.search(r'\b(under|below|less\s+than|maximum|cheap|affordable|budget|inexpensive)\b', query_lower))
        
        # Extract valid livestock types (check in order of specificity)
        for livestock_type, pattern in livestock_patterns:
            if re.search(pattern, query_lower):
                # For price-based queries, use generic types only for generic terms
                if has_price_terms:
                    # Only use generic types for truly generic searches
                    if livestock_type.startswith('GENERIC_'):
                        params['livestock_type'] = livestock_type
                        break
                    elif not livestock_type.startswith('GENERIC_'):
                        # For specific breeds with price terms, keep the specific type
                        params['livestock_type'] = livestock_type
                        break
                else:
                    # For non-price queries, use specific types
                    if not livestock_type.startswith('GENERIC_'):
                        params['livestock_type'] = livestock_type
                        break
        
        # If no specific match found and no price terms, try generic patterns
        if not params['livestock_type'] and not has_price_terms:
            for livestock_type, pattern in livestock_patterns:
                if livestock_type.startswith('GENERIC_') and re.search(pattern, query_lower):
                    # Convert generic type to specific default type
                    if livestock_type == 'GENERIC_GOAT':
                        params['livestock_type'] = 'Goat Sokoto Red'
                    elif livestock_type == 'GENERIC_SHEEP':
                        params['livestock_type'] = 'Sheep Yankasa'
                    elif livestock_type == 'GENERIC_CATTLE':
                        params['livestock_type'] = 'Cattle Sokoto Gudali'
                    elif livestock_type == 'GENERIC_POULTRY':
                        params['livestock_type'] = 'Poultry Broiler'
                    elif livestock_type == 'GENERIC_FISH':
                        params['livestock_type'] = 'Fish Tilapia'
                    break
    
    # Extract location with validation - context-aware livestock type filtering
    location_patterns = [
        r'\bin\s+([a-zA-Z]+)(?:\s+state)?(?:\s+under|\s+with|\s*$|\s)',  # "in Lagos state" or "in Lagos under" or "in Lagos"
        r'(?:from|at)\s+([a-zA-Z]+)(?:\s+state)?(?:\s+under|\s+with|\s*$|\s)',  # "from Lagos state" or "at Lagos"
        r'(?:near|around)\s+([a-zA-Z]+)(?:\s+state)?(?:\s+under|\s+with|\s*$|\s)'  # "near Lagos state"
    ]
    
    # Valid Nigerian locations (including Sokoto as a city)
    valid_locations = [
        'Kaduna', 'Lagos', 'Abuja', 'Fct', 'Kano', 'Ibadan', 
        'Port Harcourt', 'Benin City', 'Maiduguri', 'Jos', 
        'Ilorin', 'Owerri', 'Calabar', 'Sokoto', 'Enugu', 'Zaria',
        'Bauchi', 'Plateau', 'Benue', 'Taraba', 'Kebbi', 'Zamfara'
    ]
    
    for pattern in location_patterns:
        location_match = re.search(pattern, query_lower)
        if location_match:
            location = location_match.group(1).strip().title()
            
            # Check if location is valid first
            is_valid_location = any(
                valid_loc.lower() == location.lower()
                for valid_loc in valid_locations
            )
            
            if is_valid_location:
                # Context-aware filtering: check if this location word appears as part of a livestock breed name
                # For example, "Cattle Sokoto Gudali in Lagos" vs "Fish in Sokoto"
                is_part_of_livestock_name = False
                
                # Check if the location appears immediately after livestock type words
                livestock_context_patterns = [
                    rf'\b(?:cattle|goat|sheep)\s+{location.lower()}\s+(?:red|gudali|yankasa|balami|uda|white|fulani)\b',
                    rf'\b(?:poultry)\s+{location.lower()}\s+(?:broiler|noiler|layer)\b'
                ]
                
                for livestock_pattern in livestock_context_patterns:
                    if re.search(livestock_pattern, query_lower):
                        is_part_of_livestock_name = True
                        break
                
                # Only use as location if it's not part of a livestock breed name
                if not is_part_of_livestock_name:
                    params['location']['city'] = location
                    break
    
    # Extract price with validation
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
                
                # Validate reasonable price range (1,000 to 10,000,000 Naira)
                if 1000 <= price_value <= 10000000:
                    params['price_range']['max'] = price_value
                # If price is unreasonable, mark it as invalid
                elif price_value < 1000:
                    params['price_range']['invalid'] = True
            except ValueError:
                pass
            break
    
    # Extract quantity
    quantity_match = re.search(r'(\d+(?:\.\d+)?)\s*(tons?|kg|tonnes?)', query_lower)
    if quantity_match:
        amount = float(quantity_match.group(1))
        unit = quantity_match.group(2)
        
        # Validate reasonable quantity (0.1 to 1000 tons)
        if 0.1 <= amount <= 1000:
            params['quantity']['amount'] = amount
            params['quantity']['unit'] = unit
    
    # Quality requirements - enhanced patterns
    quality_patterns = [
        r'\b(top.?rated|highest.?rating|best|premium|high.?quality|excellent)\b',
        r'\b(quality|rated|rating)\b'
    ]
    
    for pattern in quality_patterns:
        if re.search(pattern, query_lower):
            params['quality_requirements']['top_rated'] = True
            break
    
    return params

def validate_query(query: str) -> None:
    if not query or not query.strip():
        raise ValidationError("Query cannot be empty")
    if len(query) > 500:
        raise ValidationError("Query too long (max 500 characters)")
    
    # Check for potentially harmful content
    harmful_patterns = [r'<script', r'javascript:', r'on\w+\s*=', r'eval\s*\(', r'exec\s*\(']
    for pattern in harmful_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValidationError("Query contains invalid content")

def validate_livestock_type(livestock_type: str) -> None:
    if not livestock_type or not livestock_type.strip():
        raise ValidationError("Livestock type cannot be empty")
    
    valid_types = [
        'Poultry Broiler', 'Poultry Noiler', 'Cattle Sokoto Gudali', 
        'Fish Tilapia', 'Fish Catfish', 'Fish Heterotis',
        'Goat Sokoto Red', 'Sheep Yankasa', 'Sheep Balami'
    ]
    
    # Allow partial matches for flexibility
    if not any(livestock_type.lower() in vt.lower() or vt.lower() in livestock_type.lower() for vt in valid_types):
        raise ValidationError(f"Invalid livestock type. Available types: {', '.join(valid_types)}")

def validate_location(location: str) -> None:
    if not location or not location.strip():
        raise ValidationError("Location cannot be empty")
    
    if len(location) > 100:
        raise ValidationError("Location name too long (max 100 characters)")

def validate_quantity(quantity: float) -> None:
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0")
    
    if quantity > 1000:
        raise ValidationError("Quantity too large (max 1000 tons)")

def validate_radius(radius: float) -> None:
    if radius <= 0:
        raise ValidationError("Radius must be greater than 0")
    
    if radius > 500:
        raise ValidationError("Radius too large (max 500 km)")

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
    Accepts queries like: "Find goats in Kaduna under 40,000 Naira"
    """
    try:
        request_data = app.current_request.json_body
        query = request_data.get('query', '').strip()
        
        if not query:
            raise ValidationError("Query is required")
        
        validate_query(query)
        
        # Process natural language query with simple extraction
        extracted_params = extract_simple_parameters(query)
        
        requested_livestock = extracted_params.get('livestock_type')
        requested_location = extracted_params.get('location', {}).get('city')
        requested_price = extracted_params.get('price_range', {}).get('max')
        
        # For location-specific queries, we need to check both location-specific and all results
        if requested_location and requested_livestock:
            # First, try to find results in the specific location
            location_specific_results = matching_service.find_matching_sellers(extracted_params)
            
            # If no results in specific location, get all results to show alternatives
            if not location_specific_results:
                # Remove location filter and search again
                params_without_location = extracted_params.copy()
                params_without_location['location'] = {}
                all_results = matching_service.find_matching_sellers(params_without_location, ignore_location_filter=True)
                
                # Filter results by location manually
                other_location_results = [
                    seller for seller in all_results 
                    if seller.get('City', '').lower() != requested_location.lower()
                ]
                
                # Set up location notice response
                if other_location_results:
                    show_location_notice = True
                    search_message = f"No {requested_livestock} sellers found in {requested_location}. Showing available sellers in other locations:"
                    final_results = other_location_results[:10]
                else:
                    show_location_notice = False
                    search_message = f"No {requested_livestock} sellers found"
                    final_results = []
            else:
                # Found results in requested location
                show_location_notice = False
                search_message = f"Found {len(location_specific_results)} seller{'s' if len(location_specific_results) != 1 else ''} for {requested_livestock} in {requested_location}"
                final_results = location_specific_results
        else:
            # For non-location-specific queries, use standard search
            raw_results = matching_service.find_matching_sellers(extracted_params)
            show_location_notice = False
            final_results = raw_results
            
            # Standard search summary for other cases
            search_message = f"Found {len(raw_results)} seller{'s' if len(raw_results) != 1 else ''}"
            if requested_livestock:
                search_message += f" for {requested_livestock}"
            if requested_location:
                search_message += f" in {requested_location}"
            if requested_price:
                search_message += f" under ₦{requested_price:,}"
        
        # Format results for buyer consumption - simple and clear
        buyer_results = []
        for seller in final_results:
            # Get seller rating with simple display
            rating_value = round(float(seller.get('Rating', 0)), 1)
            
            # Use farm name directly from database (now stored in correct format)
            farm_name = seller.get('Name', 'Unknown Farm')
            
            # Extract essential seller information - clean and simple
            seller_info = {
                'farm_name': farm_name,
                'location': seller.get('City', 'Unknown'),
                'rating': rating_value,
                'phone': seller.get('Phone', 'Contact via platform'),
                'livestock': []
            }
            
            # Add livestock products with clear pricing
            for product in seller.get('matching_products', []):
                min_price = int(product.get('MinPrice', 0))
                max_price = int(product.get('MaxPrice', 0))
                
                # Create simple price display
                if min_price == max_price:
                    price_display = f"₦{min_price:,}"
                else:
                    price_display = f"₦{min_price:,} - ₦{max_price:,}"
                
                livestock_info = {
                    'type': product.get('LivestockType', 'Unknown'),
                    'price': price_display
                }
                seller_info['livestock'].append(livestock_info)
            
            buyer_results.append(seller_info)
        
        # Create clean, buyer-focused response
        if show_location_notice:
            # When showing alternatives due to location unavailability
            response = {
                'message': f"No {requested_livestock} sellers found in {requested_location}. Showing {len(buyer_results)} sellers in nearby areas:",
                'sellers': buyer_results,
                'tip': "💡 Contact sellers about delivery to your area"
            }
        elif requested_location and requested_livestock and final_results:
            # When found results in requested location
            response = {
                'message': f"Found {len(buyer_results)} {requested_livestock} seller{'s' if len(buyer_results) != 1 else ''} in {requested_location}",
                'sellers': buyer_results,
                'tip': "💡 Compare prices and ratings to find the best deal"
            }
        elif final_results:
            # General search results
            livestock_text = f" {requested_livestock} seller{'s' if len(buyer_results) != 1 else ''}" if requested_livestock else f" seller{'s' if len(buyer_results) != 1 else ''}"
            location_text = f" in {requested_location}" if requested_location else ""
            price_text = f" under ₦{requested_price:,}" if requested_price else ""
            
            response = {
                'message': f"Found {len(buyer_results)}{livestock_text}{location_text}{price_text}",
                'sellers': buyer_results,
                'tip': "💡 Contact sellers directly to discuss your needs"
            }
        else:
            # No results found
            response = {
                'message': "No sellers found matching your search",
                'sellers': [],
                'suggestions': [
                    "Try a different livestock type",
                    "Search in nearby cities", 
                    "Increase your budget if you set a price limit"
                ]
            }
        
        return response
        
    except ValidationError as e:
        return Response(
            body={'error': str(e)},
            status_code=400,
            headers={'Content-Type': 'application/json'}
        )
    except ServiceError as e:
        app.log.error(f"Service error: {str(e)}")
        return Response(
            body={'error': 'Internal service error'},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        app.log.error(f"Unexpected error: {str(e)}")
        return Response(
            body={'error': 'Internal server error'},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

@app.route('/recommendations/top-rated', methods=['POST'])
def get_top_rated_sellers():
    """
    Get top-rated sellers for specific livestock type
    """
    try:
        request_data = app.current_request.json_body
        livestock_type = request_data.get('livestock_type', '').strip()
        limit = request_data.get('limit', 10)
        
        if not livestock_type:
            raise ValidationError("livestock_type is required")
        
        validate_livestock_type(livestock_type)
        
        results = matching_service.get_top_rated_sellers(livestock_type, limit)
        
        # Format for buyer consumption
        buyer_results = []
        for seller in results:
            # Use farm name directly from database
            farm_name = seller.get('Name', 'Unknown Farm')
                
            seller_info = {
                'farm_name': farm_name,
                'location': seller.get('City', 'Unknown'),
                'rating': round(float(seller.get('Rating', 0)), 1),
                'phone': seller.get('Phone', 'Contact via platform')
            }
            buyer_results.append(seller_info)
        
        return {
            'message': f"Top {len(buyer_results)} {livestock_type} sellers",
            'sellers': buyer_results
        }
        
    except ValidationError as e:
        return Response(
            body={'error': str(e)},
            status_code=400,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        app.log.error(f"Error getting top rated sellers: {str(e)}")
        return Response(
            body={'error': 'Internal server error'},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

@app.route('/search/proximity', methods=['POST'])
def proximity_search():
    """
    Location-based proximity search
    """
    try:
        request_data = app.current_request.json_body
        location = request_data.get('location', '').strip()
        radius_km = request_data.get('radius_km', 10)
        livestock_type = request_data.get('livestock_type', '')
        
        if not location:
            raise ValidationError("location is required")
        
        validate_location(location)
        validate_radius(radius_km)
        
        results = matching_service.find_sellers_by_proximity(
            location, radius_km, livestock_type
        )
        
        # Format for buyer consumption
        buyer_results = []
        for seller in results:
            # Use farm name directly from database
            farm_name = seller.get('Name', 'Unknown Farm')
                
            seller_info = {
                'farm_name': farm_name,
                'location': seller.get('City', 'Unknown'),
                'distance_km': seller.get('distance_km', 0),
                'rating': round(float(seller.get('Rating', 0)), 1),
                'phone': seller.get('Phone', 'Contact via platform')
            }
            buyer_results.append(seller_info)
        
        return {
            'message': f"Found {len(buyer_results)} sellers within {radius_km}km of {location}",
            'sellers': buyer_results
        }
        
    except ValidationError as e:
        return Response(
            body={'error': str(e)},
            status_code=400,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        app.log.error(f"Error in proximity search: {str(e)}")
        return Response(
            body={'error': 'Internal server error'},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

@app.route('/insights/popular-products', methods=['GET'])
def get_popular_products():
    """
    Get insights on popular livestock products
    """
    try:
        results = matching_service.get_popular_products()
        
        return {
            'message': f"Popular livestock types (by seller count)",
            'products': results
        }
        
    except Exception as e:
        app.log.error(f"Error getting popular products: {str(e)}")
        return Response(
            body={'error': 'Internal server error'},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )

@app.route('/search/bulk-capacity', methods=['POST'])
def bulk_capacity_search():
    """
    Search for sellers with bulk purchase capacity
    """
    try:
        request_data = app.current_request.json_body
        livestock_type = request_data.get('livestock_type', '').strip()
        quantity_tons = request_data.get('quantity_tons', 0)
        
        if not livestock_type or quantity_tons <= 0:
            raise ValidationError("livestock_type and quantity_tons (>0) are required")
        
        validate_livestock_type(livestock_type)
        validate_quantity(quantity_tons)
        
        results = matching_service.find_bulk_suppliers(livestock_type, quantity_tons)
        
        # Format for buyer consumption
        buyer_results = []
        for seller in results:
            # Use farm name directly from database
            farm_name = seller.get('Name', 'Unknown Farm')
                
            seller_info = {
                'farm_name': farm_name,
                'location': seller.get('City', 'Unknown'),
                'available_tons': seller.get('available_tons', 0),
                'rating': round(float(seller.get('Rating', 0)), 1),
                'phone': seller.get('Phone', 'Contact via platform')
            }
            buyer_results.append(seller_info)
        
        return {
            'message': f"Found {len(buyer_results)} suppliers with {quantity_tons}+ tons of {livestock_type}",
            'sellers': buyer_results
        }
        
    except ValidationError as e:
        return Response(
            body={'error': str(e)},
            status_code=400,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        app.log.error(f"Error in bulk capacity search: {str(e)}")
        return Response(
            body={'error': 'Internal server error'},
            status_code=500,
            headers={'Content-Type': 'application/json'}
        )