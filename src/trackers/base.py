from abc import ABC, abstractmethod
from datetime import datetime
import logging
import json
from typing import Dict, Any, Optional
from .clients.dynamodb_client import DynamoDBClient
from .clients.ntfy_client import NtfyClient

logger = logging.getLogger()


class BaseTracker(ABC):
    def __init__(self, product_id: str, config: Dict[str, Any]):
        self.product_id = product_id
        self.config = config
        self.db_client = DynamoDBClient()
        self.ntfy_client = NtfyClient()

    @abstractmethod
    def fetch_current_price(self) -> float:
        """Fetch current price from the source"""
        pass

    @abstractmethod
    def get_product_name(self) -> str:
        """Get human-readable product name"""
        pass

    def track_price(self) -> Dict[str, Any]:
        """Main tracking logic - common for all trackers"""
        try:
            # Fetch current price
            current_price = self.fetch_current_price()

            # Get latest historical price
            latest_price = self.get_latest_price()

            # Store new price data
            self.store_price_data(current_price)

            # Check for price changes and notify
            price_changed = False
            if latest_price and self.should_notify(current_price, latest_price):
                self.send_price_change_notification(latest_price, current_price)
                price_changed = True

            return {
                'statusCode': 200,
                'product_id': self.product_id,
                'current_price': current_price,
                'previous_price': latest_price,
                'price_changed': price_changed,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error tracking {self.product_id}: {str(e)}")
            return {
                'statusCode': 500,
                'product_id': self.product_id,
                'error': str(e)
            }

    def get_latest_price(self) -> Optional[float]:
        """Get latest price from DynamoDB"""
        return self.db_client.get_latest_price(self.product_id)

    def store_price_data(self, price: float):
        """Store price data in DynamoDB"""
        self.db_client.store_price(
            product_id=self.product_id,
            price=price,
            metadata=self.get_metadata()
        )

    def should_notify(self, current_price: float, previous_price: float) -> bool:
        """Determine if notification should be sent"""
        threshold = self.config.get('notification_threshold', 0.01)
        change_percent = abs((current_price - previous_price) / previous_price)
        return change_percent >= threshold

    def send_price_change_notification(self, old_price: float, new_price: float):
        """Send notification about price change"""
        product_name = self.get_product_name()
        change_percent = ((new_price - old_price) / old_price) * 100
        direction = "📈" if new_price > old_price else "📉"

        message = (
            f"{direction} {product_name} Price Alert!\n"
            f"Previous: ${old_price:.2f}\n"
            f"Current: ${new_price:.2f}\n"
            f"Change: {change_percent:+.2f}%"
        )

        self.ntfy_client.send_notification(message, self.product_id)

    def get_metadata(self) -> Dict[str, Any]:
        """Get additional metadata to store with price"""
        return {
            'tracker_type': self.__class__.__name__,
            'config': self.config
        }