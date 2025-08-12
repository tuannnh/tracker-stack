import os
import json
import boto3
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

def handler(event, context):
    """
    Dispatcher Lambda handler that scans the product database and enqueues crawl jobs.
    
    This function is triggered by EventBridge on a schedule and:
    1. Scans the products table for all tracked items
    2. Enqueues a job for each product to check its price
    3. Enqueues a special job for the gold price
    """
    try:
        # Get environment variables
        products_table_name = os.environ['PRODUCTS_TABLE']
        queue_url = os.environ['CRAWL_QUEUE_URL']
        
        # Scan products table
        table = dynamodb.Table(products_table_name)
        response = table.scan()
        items = response.get('Items', [])
        
        # Track count of enqueued jobs
        enqueued_count = 0
        
        # Process each product
        logger.info(f"Processing {len(items)} products")
        for item in items:
            try:
                # Enqueue Shopee product job
                sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps({
                        'type': 'shopee',
                        'productId': item['productId'],
                        'url': item['url']
                    })
                )
                enqueued_count += 1
                logger.debug(f"Enqueued job for product {item['productId']}")
            except Exception as e:
                logger.error(f"Error enqueueing job for product {item.get('productId', 'unknown')}: {str(e)}")
        
        # Always add gold price tracking job
        try:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({
                    'type': 'gold',
                    'url': 'https://goldstore.com/daily-prices'
                })
            )
            enqueued_count += 1
            logger.info("Enqueued gold price tracking job")
        except Exception as e:
            logger.error(f"Error enqueueing gold price job: {str(e)}")
        
        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items = response.get('Items', [])
            
            logger.info(f"Processing additional {len(items)} products")
            for item in items:
                try:
                    sqs.send_message(
                        QueueUrl=queue_url,
                        MessageBody=json.dumps({
                            'type': 'shopee',
                            'productId': item['productId'],
                            'url': item['url']
                        })
                    )
                    enqueued_count += 1
                except Exception as e:
                    logger.error(f"Error enqueueing job for product {item.get('productId', 'unknown')}: {str(e)}")
        
        logger.info(f"Successfully enqueued {enqueued_count} jobs")
        return {
            'statusCode': 200,
            'enqueued': enqueued_count
        }
    
    except Exception as e:
        logger.error(f"Error in dispatcher: {str(e)}")
        raise