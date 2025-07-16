import json
import boto3
import os
import logging
from botocore.exceptions import ClientError

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# Environment variables
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")

def lambda_handler(event, context):
    try:
        logger.info("Lambda triggered with event metadata: %s", json.dumps(event.get("headers", {})))

        # Step 1: Parse the incoming JSON body
        body = event.get("body")
        if body is None:
            raise ValueError("Request body is missing.")

        # If the event is from API Gateway HTTP API, body might be a raw JSON string
        if isinstance(body, str):
            body = json.loads(body)

        bucket = body.get("bucket")
        key = body.get("key")

        if not bucket or not key:
            raise ValueError("Both 'bucket' and 'key' must be provided in the request body.")

        logger.info(f"Received bucket: {bucket}, key: {key}")

        # Step 2: Check if the file exists in S3
        try:
            s3.head_object(Bucket=bucket, Key=key)
            logger.info(f"File {key} exists in bucket {bucket}.")
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                logger.error(f"File {key} not found in bucket {bucket}.")
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": "File not found in S3 bucket."})
                }
            else:
                logger.error(f"Unexpected error checking S3: {str(e)}")
                raise

        # Step 3: Notify SQS
        message_body = json.dumps({"bucket": bucket, "key": key})
        response = sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message_body
        )
        logger.info(f"Message sent to SQS with MessageId: {response['MessageId']}")

        # Step 4: Return success
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "File exists. Notification sent to processing queue.",
                "bucket": bucket,
                "key": key
            })
        }

    except Exception as e:
        logger.error("Error occurred during Lambda execution", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
