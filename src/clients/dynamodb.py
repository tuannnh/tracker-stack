import boto3
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from boto3.dynamodb.conditions import Key


class DynamoDBClient:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=os.getenv('LOCALSTACK_ENDPOINT')
        )
        self.price_table = self.dynamodb.Table(os.getenv('DYNAMODB_TABLE'))
        self.products_table = self.dynamodb.Table(os.getenv('PRODUCTS_TABLE', 'products'))

    def get_latest_price(self, product_id: str) -> Optional[float]:
        """Get the latest price for a product"""
        try:
            response = self.price_table.query(
                KeyConditionExpression=Key('product_id').eq(product_id),
                ScanIndexForward=False,
                Limit=1
            )

            if response['Items']:
                return float(response['Items'][0]['price'])
            return None

        except Exception as e:
            raise Exception(f"Error fetching latest price: {str(e)}")

    def store_price(self, product_id: str, price: float, metadata: Dict[str, Any] = None):
        """Store price data"""
        item = {
            'product_id': product_id,
            'timestamp': datetime.now().isoformat(),
            'price': price
        }

        if metadata:
            item['metadata'] = metadata

        try:
            self.price_table.put_item(Item=item)
        except Exception as e:
            raise Exception(f"Error storing price: {str(e)}")

    def get_shopee_products(self) -> List[Dict[str, Any]]:
        """Get all active Shopee products to track"""
        try:
            response = self.products_table.scan(
                FilterExpression='#status = :status AND tracker_type = :tracker_type',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'active',
                    ':tracker_type': 'shopee'
                }
            )
            return response.get('Items', [])
        except Exception as e:
            raise Exception(f"Error fetching Shopee products: {str(e)}")

    def store_product(self, product_data: Dict[str, Any]):
        """Store product configuration"""
        try:
            self.products_table.put_item(Item=product_data)
        except Exception as e:
            raise Exception(f"Error storing product: {str(e)}")

    def update_product_status(self, product_id: str, status: str):
        """Update product status (active/inactive)"""
        try:
            self.products_table.update_item(
                Key={'product_id': product_id},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status}
            )
        except Exception as e:
            raise Exception(f"Error updating product status: {str(e)}")