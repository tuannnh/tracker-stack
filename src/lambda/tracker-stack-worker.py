import os
import json
import re
import logging
import requests
from datetime import datetime, timezone
from decimal import Decimal
import boto3
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert Decimal to float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_price_from_shopee(url):
    """
    Extract price from Shopee API
    
    Args:
        url (str): The Shopee API URL to fetch price data from
        
    Returns:
        int: The price value
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        data = response.json()
        
        # Extract price from response
        if 'data' in data and 'price' in data['data']:
            return int(data['data']['price'])
        else:
            logger.error(f"Unexpected API response structure: {json.dumps(data)[:200]}...")
            raise ValueError("Price data not found in API response")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error when fetching Shopee price: {str(e)}")
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing Shopee API response: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_price_from_shopee: {str(e)}")
        raise

def get_price_from_gold_page(url):
    """
    Extract gold price from HTML page
    
    Args:
        url (str): The URL of the gold price page
        
    Returns:
        int: The gold price value
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        price_element = soup.select_one('.gold-price')
        
        if not price_element:
            logger.error("Gold price element not found on page")
            raise ValueError("Gold price element not found")
            
        price_text = price_element.get_text()
        # Remove all non-digit characters
        num = re.sub(r'[^\d]', '', price_text)
        
        if not num:
            logger.error(f"Could not extract numeric price from text: {price_text}")
            raise ValueError("Failed to extract numeric price")
            
        return int(num)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error when fetching gold price: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error in get_price_from_gold_page: {str(e)}")
        raise

def handler(event, context):
    """
    Worker Lambda handler that processes crawl jobs from SQS.
    
    For each job, the function:
    1. Fetches the current price
    2. Compares with previous price (if any)
    3. If price changed, updates database and sends notification
    """
    logger.info(f"Processing batch of {len(event.get('Records', []))} messages")
    
    # Get environment variables
    products_table_name = os.environ['PRODUCTS_TABLE']
    history_table_name = os.environ['HISTORY_TABLE']
    topic_arn = os.environ['PRICE_TOPIC_ARN']
    
    # Get DynamoDB tables
    products_table = dynamodb.Table(products_table_name)
    history_table = dynamodb.Table(history_table_name)
    
    processed_count = 0
    error_count = 0
    
    for record in event.get('Records', []):
        try:
            # Parse job from SQS message
            job = json.loads(record['body'])
            job_type = job.get('type')
            url = job.get('url')
            
            logger.info(f"Processing job type: {job_type}, URL: {url}")
            
            # Get price based on job type
            if job_type == 'shopee':
                price_val = get_price_from_shopee(url)
                product_id = job.get('productId')
            elif job_type == 'gold':
                price_val = get_price_from_gold_page(url)
                product_id = 'gold-price'
            else:
                logger.warning(f"Unknown job type: {job_type}")
                continue
            
            # Get current timestamp
            now_iso = datetime.now(timezone.utc).isoformat()
            
            # Get existing product data
            try:
                response = products_table.get_item(Key={'productId': product_id})
                product = response.get('Item')
            except ClientError as e:
                logger.error(f"Error retrieving product data: {str(e)}")
                raise
                
            # Get last price
            last_price = product.get('lastPrice') if product else None
            
            # Check if price changed or new product
            price_changed = last_price is None or int(last_price) != int(price_val)
            
            if price_changed:
                logger.info(f"Price changed for {product_id}: {last_price} -> {price_val}")
                
                # Update price history
                try:
                    history_table.put_item(Item={
                        'productId': product_id,
                        'timestamp': now_iso,
                        'price': Decimal(str(price_val)),
                        'currency': 'VND'
                    })
                except ClientError as e:
                    logger.error(f"Error updating price history: {str(e)}")
                    raise
                
                # Update product with new price
                try:
                    products_table.put_item(Item={
                        'productId': product_id,
                        'url': url,
                        'lastPrice': Decimal(str(price_val)),
                        'lastCheckedAt': now_iso
                    })
                except ClientError as e:
                    logger.error(f"Error updating product data: {str(e)}")
                    raise
                
                # Send notification
                try:
                    message = {
                        'productId': product_id,
                        'oldPrice': last_price,
                        'newPrice': price_val,
                        'timestamp': now_iso
                    }
                    
                    sns.publish(
                        TopicArn=topic_arn,
                        Message=json.dumps(message, cls=DecimalEncoder),
                        Subject=f"Price Change: {product_id}"
                    )
                    
                    logger.info(f"Notification sent for {product_id}")
                except ClientError as e:
                    logger.error(f"Error sending notification: {str(e)}")
                    raise
            else:
                logger.info(f"No price change for {product_id}")
                
                # Update last checked timestamp
                try:
                    products_table.update_item(
                        Key={'productId': product_id},
                        UpdateExpression="SET lastCheckedAt = :t",
                        ExpressionAttributeValues={':t': now_iso}
                    )
                except ClientError as e:
                    logger.error(f"Error updating last checked timestamp: {str(e)}")
                    
            processed_count += 1
                
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            error_count += 1
    
    logger.info(f"Completed batch processing: {processed_count} successful, {error_count} failed")
    
    return {
        'statusCode': 200,
        'processed': processed_count,
        'errors': error_count
    }