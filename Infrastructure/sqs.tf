# DLQ for the main entry queue
resource "aws_sqs_queue" "video_transcriber_notifier_dlq" {
  name = "video-transcriber-notifier-dlq"

  message_retention_seconds = 1209600 # 14 days
}

# Queue: uploader → whisper
resource "aws_sqs_queue" "video_transcriber_notifier" {
  name = "video-transcriber-notifier"

  visibility_timeout_seconds = 900
  message_retention_seconds  = 86400 # 1 day
  delay_seconds              = 0
  receive_wait_time_seconds  = 0

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.video_transcriber_notifier_dlq.arn
    maxReceiveCount     = 3
  })
}

# Queue: whisper → summarizer
resource "aws_sqs_queue" "summary_generator_notifier" {
  name = "summary-generator-notifier"

  visibility_timeout_seconds = 1000 # <-- Updated to 1000 seconds (safe for 900s Lambda timeout)
  message_retention_seconds  = 86400
  delay_seconds              = 0
  receive_wait_time_seconds  = 0
}
