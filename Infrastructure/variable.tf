variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "input_bucket_name" {
  description = "S3 bucket for uploaded videos"
  type        = string
  default     = "minute-maker-input"
}

variable "intermediate_bucket_name" {
  description = "S3 bucket for intermediate data (audio, transcripts)"
  type        = string
  default     = "minute-maker-intermediate"
}

variable "output_bucket_name" {
  description = "S3 bucket for final meeting minutes"
  type        = string
  default     = "minute-maker-output"
}

variable "model_bucket_name" {
  description = "S3 bucket for ML models (Whisper, BERT, ffmpeg)"
  type        = string
  default     = "minute-maker-models"
}

variable "video_upload_lambda_name" {
  description = "Name of the Lambda function that uploads videos to S3 and notifies SQS"
  type        = string
  default     = "video-upload-handler"
}

variable "video_transcriber_ecr_image_uri" {
  description = "ECR image URI for the video transcriber Lambda Docker deployment"
  type        = string
}

variable "summarizer_ecr_image_uri" {
  description = "ECR image URI for the summarizer Lambda Docker deployment"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag for Lambda deployments (like latest, v1, v2)"
  type        = string
  default     = "latest"
}
