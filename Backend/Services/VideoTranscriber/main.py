import os
import json
import boto3
import logging
import traceback
import stat
from pathlib import Path
from faster_whisper import WhisperModel

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# Environment Variables
MODEL_BUCKET = os.environ["MODEL_BUCKET"]
MODEL_PREFIX = os.environ.get("MODEL_PREFIX", "video-transcriber-models/")
INTERMEDIATE_BUCKET = os.environ["INTERMEDIATE_BUCKET"]
SQS_SUMMARIZER_QUEUE_URL = os.environ["SQS_SUMMARIZER_QUEUE_URL"]
TMP_DIR = "/tmp"

# ----------------- Utility Functions --------------------

def download_from_s3(bucket, key, local_path):
    """Download a file from S3 to local path"""
    logger.info(f"Downloading s3://{bucket}/{key} → {local_path}")
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(bucket, key, local_path)
    logger.info(f"Downloaded {key} to {local_path}")

def upload_to_s3(bucket, key, local_path):
    """Upload a local file to S3"""
    logger.info(f"Uploading {local_path} → s3://{bucket}/{key}")
    s3.upload_file(local_path, bucket, key)
    logger.info("Upload complete.")

def load_dependencies_to_tmp():
    """
    Downloads all dependencies (Whisper model + ffmpeg) from S3 to /tmp,
    makes ffmpeg executable, and updates PATH.
    """
    local_root = os.path.join(TMP_DIR, "video-transcriber-models")

    logger.info("Downloading dependencies from S3...")
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=MODEL_BUCKET, Prefix=MODEL_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            relative_path = key.replace(MODEL_PREFIX, "")
            if not relative_path:
                continue
            local_file = os.path.join(local_root, relative_path)
            download_from_s3(MODEL_BUCKET, key, local_file)

            # Make ffmpeg executable
            if relative_path == "ffmpeg":
                logger.info("Making ffmpeg executable")
                os.chmod(local_file, os.stat(local_file).st_mode | stat.S_IEXEC)

    os.environ["PATH"] = f"{local_root}:{os.environ['PATH']}"
    logger.info("Updated PATH for ffmpeg: %s", local_root)

    return local_root

def transcribe_audio(model, audio_path):
    """Runs Faster-Whisper transcription"""
    logger.info("Running transcription with Whisper...")
    segments, _ = model.transcribe(audio_path)
    transcript = "\n".join([segment.text for segment in segments])
    logger.info("Transcription complete.")
    return transcript

# ----------------- Lambda Handler --------------------

def lambda_handler(event, context):
    logger.info("Lambda triggered with event: %s", json.dumps(event))

    try:
        for record in event["Records"]:
            body = json.loads(record["body"])
            video_bucket = body["bucket"]
            video_key = body["key"]

            video_filename = os.path.basename(video_key)
            base_name = video_filename.rsplit(".", 1)[0]

            video_path = os.path.join(TMP_DIR, video_filename)
            transcript_path = os.path.join(TMP_DIR, f"{base_name}.txt")
            transcript_key = f"{base_name}.txt"

            # Step 1: Download video from S3
            download_from_s3(video_bucket, video_key, video_path)

            # Step 2: Download Whisper + ffmpeg from S3
            model_path = load_dependencies_to_tmp()

            # Step 3: Load Whisper model
            model = WhisperModel(model_path, compute_type="int8")

            # Step 4: Transcribe video
            transcript_text = transcribe_audio(model, video_path)

            # Step 5: Save transcript to /tmp
            with open(transcript_path, "w") as f:
                f.write(transcript_text)

            # Step 6: Upload transcript to intermediate S3 bucket
            upload_to_s3(INTERMEDIATE_BUCKET, transcript_key, transcript_path)

            # Step 7: Notify summarizer through SQS
            message = {
                "transcript_key": transcript_key,
                "intermediate_bucket": INTERMEDIATE_BUCKET
            }

            sqs.send_message(
                QueueUrl=SQS_SUMMARIZER_QUEUE_URL,
                MessageBody=json.dumps(message)
            )

            logger.info("Successfully sent transcript info to summarizer queue: %s", message)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Transcription and SQS notification complete."})
        }

    except Exception as e:
        logger.error("An error occurred during processing: %s", str(e))
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
