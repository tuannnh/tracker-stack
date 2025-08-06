import requests
import time
import random
from ..base_tracker import BaseTracker


class ShopeeTracker(BaseTracker):
    def __init__(self, product_id: str, config: dict):
        super().__init__(f'shopee_{product_id}', config)
        self.shopee_product_id = product_id
        self.shop_id = config.get('shop_id')
        self.base_url = config.get('base_url', 'https://shopee.vn')
        self.product_name = config.get('product_name', f'Shopee Product {product_id}')

    def fetch_current_price(self) -> float:
        """Fetch product price using Shopee API v4"""
        try:
            # Shopee API v4 endpoint
            api_url = f"{self.base_url}/api/v4/item/get"

            params = {
                'itemid': self.shopee_product_id,
                'shopid': self.shop_id
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': f'{self.base_url}/',
                'X-Requested-With': 'XMLHttpRequest'
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
            # Fallback to web scraping if API fails
            # return self._scrape_price_from_page()
            return "No Data"

    def _scrape_price_from_page(self) -> float:
        """Fallback method: scrape price from product page"""
        url = f"{self.base_url}/product/{self.shop_id}/{self.shopee_product_id}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            # Extract price from page (implementation depends on Shopee's current structure)
            import re
            price_pattern = r'"price":(\d+)'
            matches = re.findall(price_pattern, response.text)

            if matches:
                return float(matches[0]) / 100000

        raise Exception("Could not fetch Shopee price from any source")

    def get_product_name(self) -> str:
        return self.product_name

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata.update({
            'shop_id': self.shop_id,
            'shopee_product_id': self.shopee_product_id,
            'product_name': self.product_name
        })
        return metadata