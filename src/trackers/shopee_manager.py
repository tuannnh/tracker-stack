from typing import List, Dict, Any
from .shopee import ShopeeTracker
from ..clients.dynamodb import DynamoDBClient
import logging

logger = logging.getLogger()


class ShopeeProductsManager:
    def __init__(self):
        self.db_client = DynamoDBClient()

    def track_all_products(self) -> List[Dict[str, Any]]:
        """Track all active Shopee products from DynamoDB"""
        results = []
        
        try:
            # Get all active Shopee products
            products = self.db_client.get_shopee_products()
            logger.info(f"Found {len(products)} active Shopee products to track")

            for product in products:
                try:
                    # Create tracker for each product
                    tracker = ShopeeTracker(
                        product_id=product['shopee_product_id'],
                        config={
                            'shop_id': product['shop_id'],
                            'base_url': product.get('base_url', 'https://shopee.vn'),
                            'notification_threshold': product.get('notification_threshold', 0.05),
                            'product_name': product.get('product_name', ''),
                            'product_url': product.get('product_url', '')
                        }
                    )

                    # Track the price
                    result = tracker.track_price()
                    result['product_name'] = product.get('product_name', '')
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error tracking product {product.get('shopee_product_id')}: {str(e)}")
                    results.append({
                        'statusCode': 500,
                        'product_id': product.get('shopee_product_id'),
                        'product_name': product.get('product_name', ''),
                        'error': str(e)
                    })

        except Exception as e:
            logger.error(f"Error fetching products from DynamoDB: {str(e)}")
            return [{
                'statusCode': 500,
                'error': f"Failed to fetch products: {str(e)}"
            }]

        return results

    def add_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new Shopee product to track"""
        try:
            # Validate required fields
            required_fields = ['shopee_product_id', 'shop_id', 'product_name']
            for field in required_fields:
                if field not in product_data:
                    raise ValueError(f"Missing required field: {field}")

            # Set default values
            product_item = {
                'product_id': f"shopee_{product_data['shopee_product_id']}",
                'tracker_type': 'shopee',
                'shopee_product_id': product_data['shopee_product_id'],
                'shop_id': product_data['shop_id'],
                'product_name': product_data['product_name'],
                'product_url': product_data.get('product_url', ''),
                'base_url': product_data.get('base_url', 'https://shopee.vn'),
                'notification_threshold': product_data.get('notification_threshold', 0.05),
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self.db_client.store_product(product_item)
            
            return {
                'statusCode': 200,
                'message': 'Product added successfully',
                'product_id': product_item['product_id']
            }

        except Exception as e:
            logger.error(f"Error adding product: {str(e)}")
            return {
                'statusCode': 500,
                'error': str(e)
            }