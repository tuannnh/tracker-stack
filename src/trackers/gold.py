import requests
from bs4 import BeautifulSoup
from ..base_tracker import BaseTracker


class GoldTracker(BaseTracker):
    def __init__(self, config: dict):
        super().__init__('gold_doji', config)
        self.base_url = config.get('url', 'https://doji.vn')

    def fetch_current_price(self) -> float:
        """Crawl gold price from Doji website"""
        try:
            # Method 1: Try API first
            api_url = f"{self.base_url}/api/gold-price"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data.get('sell_price', 0))
        except:
            pass

        # Method 2: Fallback to web scraping
        try:
            response = requests.get(f"{self.base_url}/gia-vang", timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find gold price element (adjust selector based on actual website)
            price_element = soup.select_one('.gold-price .sell-price')
            if price_element:
                price_text = price_element.text.strip().replace(',', '').replace('.', '')
                return float(price_text) / 1000  # Convert to proper format

        except Exception as e:
            raise Exception(f"Failed to fetch gold price: {str(e)}")

        raise Exception("Could not fetch gold price from any source")

    def get_product_name(self) -> str:
        return "DOJI Gold Price (VND)"