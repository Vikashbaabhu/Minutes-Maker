# Input Bucket - For uploading videos
resource "aws_s3_bucket" "input_bucket" {
  bucket = var.input_bucket_name

  tags = {
    Project     = "MinuteMaker"
    Type        = "Input"
    Environment = "Dev"
  }
}

# Intermediate Bucket - For audio/transcript files
resource "aws_s3_bucket" "intermediate_bucket" {
  bucket = var.intermediate_bucket_name

  tags = {
    Project     = "MinuteMaker"
    Type        = "Intermediate"
    Environment = "Dev"
  }
}

# Output Bucket - For final meeting minutes
resource "aws_s3_bucket" "output_bucket" {
  bucket = var.output_bucket_name

  tags = {
    Project     = "MinuteMaker"
    Type        = "Output"
    Environment = "Dev"
  }
}

# Model Bucket - For Whisper, BERT, etc.
resource "aws_s3_bucket" "model_bucket" {
  bucket = var.model_bucket_name

  tags = {
    Project     = "MinuteMaker"
    Type        = "Model"
    Environment = "Dev"
  }
}

# Video Transcriber Models folder placeholder
resource "aws_s3_object" "video_transcriber_prefix" {
  bucket  = aws_s3_bucket.model_bucket.bucket
  key     = "video-transcriber-models/.keep"
  content = "This is a placeholder to preserve folder structure"
}

# Summarizer Models folder placeholder
resource "aws_s3_object" "summarizer_prefix" {
  bucket  = aws_s3_bucket.model_bucket.bucket
  key     = "summarizer-models/.keep"
  content = "This is a placeholder to preserve folder structure"
}

