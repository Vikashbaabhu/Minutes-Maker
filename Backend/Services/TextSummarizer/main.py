import os
import json
import boto3
import logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3 = boto3.client("s3")

# Environment variables
MODEL_BUCKET = os.environ["MODEL_BUCKET"]
MODEL_PREFIX = os.environ["MODEL_PREFIX"]
INTERMEDIATE_BUCKET = os.environ["INTERMEDIATE_BUCKET"]
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
TMP_DIR = "/tmp"
MODEL_DIR = os.path.join(TMP_DIR, "summarizer-model")
TRANSCRIPT_PATH = os.path.join(TMP_DIR, "transcript.txt")

def model_already_downloaded(model_dir):
    expected_files = [
        "config.json",
        "generation_config.json",
        "model.safetensors",
        "special_tokens_map.json",
        "spiece.model",
        "tokenizer_config.json",
        "tokenizer.json"
    ]
    for file in expected_files:
        if not os.path.exists(os.path.join(model_dir, file)):
            return False
    return True

def download_model_folder(bucket, prefix, destination_dir):
    logger.info(f"Downloading all model files from s3://{bucket}/{prefix} to {destination_dir}")
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith('/'):
                continue
            relative_path = os.path.relpath(key, prefix)
            local_path = os.path.join(destination_dir, relative_path)
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(bucket, key, local_path)

def upload_file(source, bucket, key):
    logger.info(f"Uploading {source} -> s3://{bucket}/{key}")
    s3.upload_file(source, bucket, key)

def generate_minutes(transcript_text):
    logger.info("Loading tokenizer and model from local directory...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR)

    # Improved prompt for better control
    prompt = (
        "You are a professional meeting assistant.\n"
        "Summarize the following meeting transcript into a structured set of bullet points.\n"
        "Focus on important updates, action items, blockers, and priorities.\n\n"
        f"Meeting Transcript:\n{transcript_text}"
    )

    # Tokenize properly
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512   # Very important — control input size
    )

    logger.info("Generating summary using FLAN-T5...")
    outputs = model.generate(
        **inputs,
        max_new_tokens=300,    
        early_stopping=True,
        num_beams=4,           # Slightly higher for better generation
        no_repeat_ngram_size=3 # Prevent repeating words
    )

    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return summary


def lambda_handler(event, context):
    try:
        logger.info(f"Lambda triggered with event: {json.dumps(event)}")

        # Step 1: Parse transcript key
        body = json.loads(event["Records"][0]["body"])
        transcript_key = body["transcript_key"]
        logger.info(f"Processing transcript: {transcript_key}")

        # Step 2: Download transcript
        Path(TRANSCRIPT_PATH).parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(INTERMEDIATE_BUCKET, transcript_key, TRANSCRIPT_PATH)

        # Step 3: Ensure model files are present
        if not model_already_downloaded(MODEL_DIR):
            logger.info("Model files not found in /tmp. Downloading...")
            download_model_folder(MODEL_BUCKET, MODEL_PREFIX, MODEL_DIR)
        else:
            logger.info("Model files already exist in /tmp. Skipping download.")

        # Step 4: Read transcript
        with open(TRANSCRIPT_PATH, "r") as f:
            transcript_text = f.read()

        # Step 5: Summarize
        summary = generate_minutes(transcript_text)

        # Step 6: Save and upload
        output_key = transcript_key.replace(".txt", "_minutes.txt")
        output_local_path = os.path.join(TMP_DIR, os.path.basename(output_key))
        with open(output_local_path, "w") as f:
            f.write(summary)
        upload_file(output_local_path, OUTPUT_BUCKET, output_key)

        logger.info(f"Summarization complete. Uploaded to {OUTPUT_BUCKET}/{output_key}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Summarization complete",
                "output_key": output_key
            })
        }

    except Exception as e:
        logger.error("Error during Lambda execution", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
