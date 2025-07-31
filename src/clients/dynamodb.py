import boto3
import os
from datetime import datetime
from typing import Optional, Dict, Any
from boto3.dynamodb.conditions import Key


class DynamoDBClient:
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=os.getenv('LOCALSTACK_ENDPOINT')
        )
        self.table = self.dynamodb.Table(os.getenv('DYNAMODB_TABLE'))

    def get_latest_price(self, product_id: str) -> Optional[float]:
        """Get the latest price for a product"""
        try:
            response = self.table.query(
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
            self.table.put_item(Item=item)
        except Exception as e:
            raise Exception(f"Error storing price: {str(e)}")