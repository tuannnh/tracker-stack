import json
import os
import logging
from typing import Dict, Any

# Import all tracker classes
from src.trackers.gold import GoldTracker
from src.trackers.shopee import ShopeeTracker

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Tracker registry
TRACKER_REGISTRY = {
    'gold': GoldTracker,
    'shopee': ShopeeTracker,
    # 'amazon': AmazonTracker,
    # 'ebay': EbayTracker,
}


def lambda_handler(event, context):
    """
    Generic handler that can track any product type
    Event should contain: tracker_type, product_id (optional), config
    """
    try:
        tracker_type = event.get('tracker_type')
        product_id = event.get('product_id')
        config = event.get('config', {})

        if tracker_type not in TRACKER_REGISTRY:
            raise ValueError(f"Unknown tracker type: {tracker_type}")

        # Initialize the appropriate tracker
        tracker_class = TRACKER_REGISTRY[tracker_type]

        if tracker_type in ['shopee', 'amazon', 'ebay'] and not product_id:
            raise ValueError(f"product_id is required for {tracker_type} tracker")

        # Create tracker instance
        if product_id:
            tracker = tracker_class(product_id, config)
        else:
            tracker = tracker_class(config)

        # Track the price
        result = tracker.track_price()

        logger.info(f"Tracking result: {json.dumps(result)}")
        return result

    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e)
        }


def handle_scheduled_event(event, context):
    """Handle EventBridge scheduled events"""
    # Get tracker configuration from environment or event
    trackers_config = json.loads(os.getenv('TRACKERS_CONFIG', '[]'))

    results = []
    for tracker_config in trackers_config:
        result = lambda_handler(tracker_config, context)
        results.append(result)

    return {
        'statusCode': 200,
        'results': results
    }