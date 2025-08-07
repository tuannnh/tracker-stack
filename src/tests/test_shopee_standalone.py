import unittest
import json
import re
import requests
import time
import random
from unittest.mock import patch, MagicMock


class SimpleShopeeTracker:
    """Standalone Shopee tracker for testing without dependencies"""
    
    def __init__(self, product_id: str, shop_id: str, base_url: str = 'https://shopee.vn'):
        self.shopee_product_id = product_id
        self.shop_id = shop_id
        self.base_url = base_url

    def fetch_current_price(self):
        """Fetch product price using Shopee API v4"""
        try:
            api_url = f"{self.base_url}/api/v4/item/get"

            params = {
                'itemid': self.shopee_product_id,
                'shopid': self.shop_id
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
            }

            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))

            response = requests.get(api_url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('error') == 0:
                    item = data.get('data', {})

                    # Handle different price scenarios
                    if item.get('price_max') != item.get('price_min'):
                        # Price range exists, take minimum price
                        price = item.get('price_min', 0)
                    else:
                        price = item.get('price', 0)

                    # Shopee prices are in cents, convert to main currency
                    return float(price) / 100000
                else:
                    raise Exception(f"Shopee API error: {data.get('error_msg', 'Unknown error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            return "No Data"

    def get_full_product_data(self):
        """Get complete product data from Shopee API"""
        try:
            api_url = f"{self.base_url}/api/v4/item/get"

            params = {
                'itemid': self.shopee_product_id,
                'shopid': self.shop_id
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
            }

            # response = requests.get(api_url, params=params, headers=headers, timeout=10)
            url = f'https://shopee.vn/api/v4/item/get?itemid={self.shopee_product_id}&shopid={self.shop_id}'
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'error': 1,
                    'error_msg': f'HTTP {response.status_code}: {response.text[:100]}'
                }

        except Exception as e:
            return {
                'error': 1,
                'error_msg': str(e)
            }


class ShopeeURLParser:
    """Utility class to parse Shopee URLs and extract product/shop IDs"""
    
    @staticmethod
    def parse_shopee_url(url: str) -> dict:
        """
        Parse Shopee URL to extract shop_id and product_id
        URL format: https://shopee.vn/product-name-i.SHOPID.PRODUCTID
        """
        try:
            # Pattern to match Shopee URL with shop ID and product ID
            pattern = r'https://shopee\.vn/.*-i\.(\d+)\.(\d+)'
            match = re.search(pattern, url)
            
            if match:
                shop_id = match.group(1)
                product_id = match.group(2)
                return {
                    'shop_id': shop_id,
                    'product_id': product_id,
                    'success': True
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not extract shop_id and product_id from URL'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def build_api_url(shop_id: str, product_id: str, base_url: str = 'https://shopee.vn') -> str:
        """Build Shopee API URL"""
        return f"{base_url}/api/v4/item/get?itemid={product_id}&shopid={shop_id}"


def test_shopee_url_parsing():
    """Test URL parsing functionality"""
    print("=== Testing Shopee URL Parsing ===")
    
    test_url = "https://shopee.vn/-M%C3%A3-ELMALL1TR5-gi%E1%BA%A3m-8-%C4%91%C6%A1n-5TR-Apple-MacBook-Air-(2020)-M1-Chip-13.3-inch-8GB-256GB-SSD-i.88201679.5873954476"
    
    print(f"Input URL: {test_url}")
    
    parsed = ShopeeURLParser.parse_shopee_url(test_url)
    
    if parsed['success']:
        print(f"✓ Successfully parsed URL:")
        print(f"  Shop ID: {parsed['shop_id']}")
        print(f"  Product ID: {parsed['product_id']}")
        
        api_url = ShopeeURLParser.build_api_url(parsed['shop_id'], parsed['product_id'])
        print(f"  API URL: {api_url}")
        
        return parsed
    else:
        print(f"✗ Failed to parse URL: {parsed['error']}")
        return None


def test_shopee_api_full_response(shop_id: str, product_id: str):
    """Test complete API response from Shopee"""
    print(f"\n=== Testing Complete Shopee API Response ===")
    
    tracker = SimpleShopeeTracker(product_id, shop_id)
    
    print(f"Shop ID: {shop_id}")
    print(f"Product ID: {product_id}")
    print(f"API URL: https://shopee.vn/api/v4/item/get?itemid={product_id}&shopid={shop_id}")
    
    try:
        # Get full JSON response
        data = tracker.get_full_product_data()
        
        print(f"\n=== Complete JSON Response ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if data.get('error') == 0:
            item_data = data.get('data', {})
            
            print(f"\n=== Key Information Extracted ===")
            print(f"Product Name: {item_data.get('name', 'N/A')}")
            print(f"Raw Price: {item_data.get('price', 'N/A')}")
            print(f"Raw Price Min: {item_data.get('price_min', 'N/A')}")
            print(f"Raw Price Max: {item_data.get('price_max', 'N/A')}")
            
            # Calculate actual prices
            if 'price' in item_data and item_data['price']:
                actual_price = item_data['price'] / 100000
                print(f"Actual Price: {actual_price:,.2f} VND")
            
            if item_data.get('price_min') and item_data.get('price_max'):
                min_price = item_data['price_min'] / 100000
                max_price = item_data['price_max'] / 100000
                print(f"Price Range: {min_price:,.2f} - {max_price:,.2f} VND")
            
            print(f"Stock: {item_data.get('stock', 'N/A')}")
            print(f"Shop ID: {item_data.get('shopid', 'N/A')}")
            print(f"Item ID: {item_data.get('itemid', 'N/A')}")
            print(f"Currency: {item_data.get('currency', 'N/A')}")
            print(f"Sold Count: {item_data.get('sold', 'N/A')}")
            
            # Test price fetching method
            print(f"\n=== Testing Price Fetching Method ===")
            fetched_price = tracker.fetch_current_price()
            print(f"fetch_current_price() returned: {fetched_price}")
            
            return {
                'success': True,
                'data': data,
                'extracted_price': fetched_price
            }
        else:
            print(f"✗ API Error: {data.get('error_msg', 'Unknown error')}")
            return {
                'success': False,
                'error': data.get('error_msg', 'Unknown error')
            }
            
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


class TestShopeeAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_url = "https://shopee.vn/-M%C3%A3-ELMALL1TR5-gi%E1%BA%A3m-8-%C4%91%C6%A1n-5TR-Apple-MacBook-Air-(2020)-M1-Chip-13.3-inch-8GB-256GB-SSD-i.88201679.5873954476"
        
    def test_url_parsing(self):
        """Test URL parsing functionality"""
        parsed = ShopeeURLParser.parse_shopee_url(self.test_url)
        
        self.assertTrue(parsed['success'])
        self.assertEqual(parsed['shop_id'], '88201679')
        self.assertEqual(parsed['product_id'], '5873954476')
    
    def test_api_url_building(self):
        """Test API URL building"""
        api_url = ShopeeURLParser.build_api_url('88201679', '5873954476')
        expected_url = 'https://shopee.vn/api/v4/item/get?itemid=5873954476&shopid=88201679'
        
        self.assertEqual(api_url, expected_url)

    @patch('requests.get')
    def test_successful_api_response(self, mock_get):
        """Test handling of successful API response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'error': 0,
            'data': {
                'price': 5000000,  # 50.00 VND in Shopee format
                'price_min': 5000000,
                'price_max': 5000000,
                'name': 'Test Product',
                'stock': 100,
                'shopid': '88201679',
                'itemid': '5873954476'
            }
        }
        mock_get.return_value = mock_response

        tracker = SimpleShopeeTracker('5873954476', '88201679')
        # price = tracker.fetch_current_price()
        
        # self.assertEqual(price, 50.0)


def main():
    """Main test function"""
    print("🛍️  Shopee API Testing Tool (Standalone)")
    print("=" * 60)
    
    # Test URL
    test_url = "https://shopee.vn/-M%C3%A3-ELMALL1TR5-gi%E1%BA%A3m-8-%C4%91%C6%A1n-5TR-Apple-MacBook-Air-(2020)-M1-Chip-13.3-inch-8GB-256GB-SSD-i.88201679.5873954476"
    
    # Step 1: Test URL parsing
    parsed = test_shopee_url_parsing()
    
    if parsed and parsed['success']:
        # Step 2: Test complete API response
        result = test_shopee_api_full_response(parsed['shop_id'], parsed['product_id'])
        
        if result['success']:
            print(f"\n✓ All tests completed successfully!")
            print(f"✓ Final price: {result['extracted_price']}")
        else:
            print(f"\n✗ API test failed: {result['error']}")
    
    print("\n" + "=" * 60)
    print("Running Unit Tests...")
    print("=" * 60)


if __name__ == '__main__':
    # Run main test
    main()
    
    # Run unit tests
    unittest.main(verbosity=2, exit=False)