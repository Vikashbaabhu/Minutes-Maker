# Output: Input S3 Bucket name
output "s3_input_bucket_name" {
  description = "Name of the input S3 bucket"
  value       = aws_s3_bucket.input_bucket.bucket
}

# Output: video-upload-handler Lambda function name
output "video_upload_lambda_function_name" {
  description = "The name of the video uploader Lambda function"
  value       = aws_lambda_function.video_upload_handler.function_name
}

# Output: video-transcriber Lambda function name
output "video_transcriber_lambda_function_name" {
  description = "The name of the video transcriber Lambda function"
  value       = aws_lambda_function.video_transcriber.function_name
}

# --- Output: summarizer Lambda function name ---
output "summarizer_lambda_function_name" {
  description = "The name of the summarizer Lambda function"
  value       = aws_lambda_function.summarizer_lambda.function_name
}

# Output: Main queue from uploader → transcriber
output "video_transcriber_queue_url" {
  description = "URL of the SQS queue for the video transcriber"
  value       = aws_sqs_queue.video_transcriber_notifier.url
}

# Output: Dead Letter Queue for uploader → transcriber
output "video_transcriber_dlq_url" {
  description = "URL of the Dead Letter Queue for the video transcriber"
  value       = aws_sqs_queue.video_transcriber_notifier_dlq.url
}

# Output: Queue from transcriber → summarizer
output "summary_generator_queue_url" {
  description = "URL of the SQS queue for summary generation"
  value       = aws_sqs_queue.summary_generator_notifier.url
}

# Output: API Gateway endpoint
output "video_upload_api_endpoint" {
  description = "API Gateway endpoint for uploading videos"
  value       = "${aws_apigatewayv2_stage.video_upload_api_stage.invoke_url}/upload"
}

# Output: S3 prefix for video transcriber models
output "video_transcriber_model_prefix" {
  description = "S3 prefix for video transcriber models"
  value       = "s3://${aws_s3_bucket.model_bucket.bucket}/video-transcriber-models/"
}

# Output: S3 prefix for summarizer models
output "summarizer_model_prefix" {
  description = "S3 prefix for summarizer models"
  value       = "s3://${aws_s3_bucket.model_bucket.bucket}/summarizer-models/"
}
