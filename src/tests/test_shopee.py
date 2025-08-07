import unittest
import json
import re
import requests
import time
import random
from unittest.mock import patch, MagicMock
import sys
import os

def parse_shopee_url(url):
    """
    Parse shopee.vn url to get itemid and shopid

    for example:
    url = https://shopee.vn/Apple-MacBook-Air-(2020)-M1-Chip-13.3-inch-8GB-256GB-SSD-i.88201679.5873954476
    itemid = 5873954476
    shopid = 88201679
    """
    # is valid url?
    if not re.match(r'^https://shopee.vn/.*[0-9]+\.[0-9]+$', url):
        print('Invalid url')
        return None, None

    url_split = url.split('.')
    itemid = url_split[-1]
    shopid = url_split[-2]

    return itemid, shopid

def fetch_data_with_enhanced_headers(itemid: str, shopid: str) -> dict:
    """
    Fetch data from shopee.vn api with enhanced headers to bypass 403
    """
    url = f'https://shopee.vn/api/v4/item/get'
    
    # Enhanced headers to mimic real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': f'https://shopee.vn/product/{shopid}/{itemid}',
        'Origin': 'https://shopee.vn',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'X-Requested-With': 'XMLHttpRequest',
        'X-API-SOURCE': 'pc',
        'X-Shopee-Language': 'vi',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    params = {
        'itemid': itemid,
        'shopid': shopid
    }
    
    # Add random delay
    time.sleep(random.uniform(2, 5))
    
    try:
        print(f'Fetching data from {url}')
        print(f'Params: {params}')
        print(f'Headers: {json.dumps(headers, indent=2)}')
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        print(f'Response status code: {response.status_code}')
        print(f'Response headers: {dict(response.headers)}')
        
        if response.status_code == 200:
            response_json = response.json()
            print(f'Response JSON: {json.dumps(response_json, indent=2, ensure_ascii=False)}')
            
            if response_json.get('error') == 0:
                data = response_json.get('data')
                if data:
                    return {
                        'success': True,
                        'data': data,
                        'full_response': response_json
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No data in response',
                        'full_response': response_json
                    }
            else:
                return {
                    'success': False,
                    'error': f"API error: {response_json.get('error')} - {response_json.get('error_msg', 'Unknown')}",
                    'full_response': response_json
                }
        else:
            print(f'Response text: {response.text}')
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text}',
                'status_code': response.status_code
            }
            
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Request failed: {str(e)}'
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'JSON decode error: {str(e)}'
        }

def test_multiple_approaches(itemid: str, shopid: str):
    """Test multiple approaches to bypass 403"""
    
    print("=== Testing Multiple API Approaches ===")
    
    approaches = [
        {
            'name': 'Standard API Call',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
            }
        },
        {
            'name': 'Mobile User Agent',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            }
        },
        {
            'name': 'Enhanced Browser Headers',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                'Referer': f'https://shopee.vn/product/{shopid}/{itemid}',
                'Origin': 'https://shopee.vn',
                'X-Requested-With': 'XMLHttpRequest'
            }
        }
    ]
    
    for i, approach in enumerate(approaches, 1):
        print(f"\n--- Approach {i}: {approach['name']} ---")
        
        url = f'https://shopee.vn/api/v4/item/get'
        params = {'itemid': itemid, 'shopid': shopid}
        
        try:
            time.sleep(random.uniform(1, 3))  # Random delay between requests
            
            response = requests.get(url, params=params, headers=approach['headers'], timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✓ Success! Got JSON response")
                    print(f"Error code: {data.get('error', 'N/A')}")
                    if data.get('error') == 0:
                        item_data = data.get('data', {})
                        print(f"Product name: {item_data.get('name', 'N/A')[:50]}...")
                        print(f"Price: {item_data.get('price', 'N/A')}")
                        return data
                    else:
                        print(f"API error: {data.get('error_msg', 'Unknown')}")
                except json.JSONDecodeError:
                    print(f"✗ Got 200 but invalid JSON: {response.text[:100]}...")
            elif response.status_code == 403:
                try:
                    error_data = response.json()
                    print(f"✗ 403 Forbidden - Error: {error_data.get('error', 'N/A')}")
                    print(f"Tracking ID: {error_data.get('tracking_id', 'N/A')}")
                except:
                    print(f"✗ 403 Forbidden - Raw: {response.text[:100]}...")
            else:
                print(f"✗ HTTP {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"✗ Exception: {str(e)}")
    
    return None

def analyze_shopee_protection():
    """Analyze Shopee's protection mechanisms"""
    print("\n=== Analyzing Shopee Protection ===")
    
    # Test basic connectivity
    print("1. Testing basic connectivity to shopee.vn...")
    try:
        response = requests.get('https://shopee.vn', timeout=10)
        print(f"   Main site status: {response.status_code}")
    except Exception as e:
        print(f"   Main site error: {str(e)}")
    
    # Test API endpoint without params
    print("2. Testing API endpoint without params...")
    try:
        response = requests.get('https://shopee.vn/api/v4/item/get', timeout=10)
        print(f"   API endpoint status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   API endpoint error: {str(e)}")

def suggest_alternatives():
    """Suggest alternative approaches"""
    print("\n=== Alternative Approaches ===")
    print("Since the API is protected, here are alternatives:")
    print("1. Use a proxy service or rotating proxies")
    print("2. Implement session management with cookies")
    print("3. Use Selenium to simulate real browser behavior")
    print("4. Try different API endpoints (v2, v3, etc.)")
    print("5. Web scraping from the product page HTML")
    print("6. Use official Shopee APIs if available for your region")

if __name__ == '__main__':
    url = 'https://shopee.vn/Thi%E1%BA%BFt-b%E1%BB%8B-l%C6%B0u-tr%E1%BB%AF-DAS-TerraMaster-D5-310-5-bay-h%C3%A0ng-ch%C3%ADnh-h%C3%A3ng-i.807476339.40004315413'

    try:
        print(f'Processing: {url}')
        itemid, shopid = parse_shopee_url(url)
        
        if itemid and shopid:
            print(f'Parsed - ItemID: {itemid}, ShopID: {shopid}')
            
            # Test enhanced approach
            result = fetch_data_with_enhanced_headers(itemid, shopid)
            
            if result['success']:
                print("\n✓ SUCCESS!")
                print(json.dumps(result['data'], indent=4, ensure_ascii=False))
            else:
                print(f"\n✗ Enhanced approach failed: {result['error']}")
                
                # Try multiple approaches
                print("\nTrying alternative approaches...")
                data = test_multiple_approaches(itemid, shopid)
                
                if not data:
                    # Analyze protection and suggest alternatives
                    analyze_shopee_protection()
                    suggest_alternatives()
        else:
            print("Failed to parse URL")
            
    except Exception as e:
        print(f"Error: {e}")