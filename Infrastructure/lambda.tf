# --- Pull the latest ECR image digest for video transcriber ---
data "aws_ecr_image" "video_transcriber_image" {
  repository_name = "minute-maker-video-transcriber"
  image_tag       = var.image_tag
}

# --- Pull the latest ECR image digest for summarizer ---
data "aws_ecr_image" "summarizer_image" {
  repository_name = "minute-maker-summarizer"
  image_tag       = var.image_tag
}

# --- IAM Role for Transcriber Lambda ---
resource "aws_iam_role" "lambda_transcriber_role" {
  name = "lambda-transcriber-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

# --- IAM Role for Summarizer Lambda ---
resource "aws_iam_role" "summarizer_lambda_exec_role" {
  name = "summarizer-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

# --- Lambda definition for video transcriber using Docker image ---
resource "aws_lambda_function" "video_transcriber" {
  function_name = "video-transcriber"
  role          = aws_iam_role.lambda_transcriber_role.arn

  package_type  = "Image"
  image_uri     = "${var.video_transcriber_ecr_image_uri}@${data.aws_ecr_image.video_transcriber_image.image_digest}"
  timeout       = 900
  memory_size   = 3000
  architectures = ["x86_64"]

  ephemeral_storage {
    size = 1024
  }

  environment {
    variables = {
      MODEL_BUCKET             = var.model_bucket_name
      MODEL_PREFIX             = "video-transcriber-models/"
      VIDEO_BUCKET             = var.input_bucket_name
      INTERMEDIATE_BUCKET      = var.intermediate_bucket_name
      SQS_SUMMARIZER_QUEUE_URL = aws_sqs_queue.summary_generator_notifier.id
    }
  }

  depends_on = [data.aws_ecr_image.video_transcriber_image]
}

# --- Lambda definition for summarizer using Docker image ---
resource "aws_lambda_function" "summarizer_lambda" {
  function_name = "summarizer-lambda"
  role          = aws_iam_role.summarizer_lambda_exec_role.arn

  package_type  = "Image"
  image_uri     = "${var.summarizer_ecr_image_uri}@${data.aws_ecr_image.summarizer_image.image_digest}"
  timeout       = 900
  memory_size   = 3008
  architectures = ["x86_64"]

  ephemeral_storage {
    size = 10240
  }

  environment {
    variables = {
      MODEL_BUCKET        = var.model_bucket_name
      MODEL_PREFIX        = "summarizer-models/"
      INTERMEDIATE_BUCKET = var.intermediate_bucket_name
      OUTPUT_BUCKET       = var.output_bucket_name
      DEPLOY_TIMESTAMP    = timestamp()
    }
  }

  depends_on = [data.aws_ecr_image.summarizer_image]
}

# --- IAM Policy for Transcriber Lambda ---
resource "aws_iam_role_policy" "lambda_transcriber_policy" {
  name = "lambda-transcriber-policy"
  role = aws_iam_role.lambda_transcriber_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      { Effect = "Allow", Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"], Resource = "arn:aws:logs:*:*:*" },
      { Effect = "Allow", Action = ["s3:ListBucket", "s3:GetObject", "s3:PutObject"], Resource = ["arn:aws:s3:::${var.model_bucket_name}", "arn:aws:s3:::${var.model_bucket_name}/*", "arn:aws:s3:::${var.input_bucket_name}/*", "arn:aws:s3:::${var.intermediate_bucket_name}/*"] },
      { Effect = "Allow", Action = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"], Resource = [aws_sqs_queue.summary_generator_notifier.arn, aws_sqs_queue.video_transcriber_notifier.arn] }
    ]
  })
}

# --- IAM Policy for Summarizer Lambda ---
resource "aws_iam_role_policy" "summarizer_lambda_policy" {
  name = "summarizer-lambda-policy"
  role = aws_iam_role.summarizer_lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      { Effect = "Allow", Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"], Resource = "arn:aws:logs:*:*:*" },
      { Effect = "Allow", Action = ["s3:ListBucket"], Resource = "arn:aws:s3:::${var.model_bucket_name}" },
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject"], Resource = ["arn:aws:s3:::${var.model_bucket_name}/*", "arn:aws:s3:::${var.intermediate_bucket_name}/*", "arn:aws:s3:::${var.output_bucket_name}/*"] },
      { Effect = "Allow", Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"], Resource = aws_sqs_queue.summary_generator_notifier.arn }
    ]
  })
}

# --- SQS Triggers ---
resource "aws_lambda_event_source_mapping" "sqs_transcriber_trigger" {
  event_source_arn = aws_sqs_queue.video_transcriber_notifier.arn
  function_name    = aws_lambda_function.video_transcriber.arn
  batch_size       = 1
  enabled          = true
}

resource "aws_lambda_event_source_mapping" "sqs_summarizer_trigger" {
  event_source_arn = aws_sqs_queue.summary_generator_notifier.arn
  function_name    = aws_lambda_function.summarizer_lambda.arn
  batch_size       = 1
  enabled          = true
}

# --- IAM Role for video-upload-handler ---
resource "aws_iam_role" "video_upload_lambda_exec_role" {
  name = "video-upload-handler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

# --- IAM Policy and Function for video-upload-handler ---
resource "aws_iam_role_policy_attachment" "upload_lambda_logging" {
  role       = aws_iam_role.video_upload_lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "upload_lambda_policy" {
  name = "video-upload-handler-policy"
  role = aws_iam_role.video_upload_lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      { Effect = "Allow", Action = ["s3:PutObject", "s3:ListBucket", "s3:GetObject"], Resource = ["arn:aws:s3:::${var.input_bucket_name}", "arn:aws:s3:::${var.input_bucket_name}/*"] },
      { Effect = "Allow", Action = ["sqs:SendMessage"], Resource = aws_sqs_queue.video_transcriber_notifier.arn }
    ]
  })
}

resource "aws_lambda_function" "video_upload_handler" {
  function_name    = var.video_upload_lambda_name
  filename         = "${path.module}/lambda/upload_handler.zip"
  handler          = "main.lambda_handler"
  runtime          = "python3.11"
  role             = aws_iam_role.video_upload_lambda_exec_role.arn
  timeout          = 30
  memory_size      = 256
  source_code_hash = filebase64sha256("${path.module}/lambda/upload_handler.zip")

  environment {
    variables = {
      BUCKET_NAME     = var.input_bucket_name
      S3_FOLDER       = "input/"
      SQS_QUEUE_URL   = aws_sqs_queue.video_transcriber_notifier.id
    }
  }

  depends_on = [aws_iam_role_policy.upload_lambda_policy]
}
