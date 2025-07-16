# 🎥📝 Minutes Maker – Video Transcription and Summarization Pipeline

Welcome!
This project automatically transcribes meeting videos and summarizes them into professional meeting minutes — powered by AWS Serverless architecture.

---

## 🚀 Project Architecture

- **Frontend**:  
  User uploads a video file via API Gateway.
- **Upload Lambda** (`video-upload-handler`):

  - Receives the API call with the uploaded video name.
  - Verifies the video exists in the **Input S3 Bucket**.
  - Sends a notification to **Video Transcriber SQS Queue**.

- **Video Transcriber Lambda** (`video-transcriber`, Dockerized):

  - Triggered by the SQS event.
  - Downloads the video and Whisper model from S3.
  - Extracts and transcribes audio using **Faster-Whisper**.
  - Uploads the generated transcript to an **Intermediate S3 Bucket**.
  - Sends a notification to the **Summarizer SQS Queue**.

- **Summarizer Lambda** (`summarizer-lambda`, Dockerized):
  - Triggered by the Summarizer SQS queue.
  - Downloads the transcript from Intermediate Bucket.
  - Loads **FLAN-T5 model** from S3 into `/tmp/`.
  - Summarizes the transcript into bullet-point meeting minutes.
  - Uploads final minutes to the **Output S3 Bucket**.

✅ All steps are fully asynchronous using SQS for communication!

---

## 🛠 Tech Stack

- **AWS Services**:  
  S3, Lambda, API Gateway, SQS, CloudWatch, ECR, IAM, Terraform
- **Languages & Tools**:  
  Python, Docker, Huggingface Transformers, GitHub Actions (CI/CD), Terraform (IaC)

---

## 🧠 Deployment Workflow

> Fully automated CI/CD powered by GitHub Actions!

1. Code changes pushed to GitHub (inside `Backend/Services/VideoTranscriber/` or `Backend/Services/TextSummarizer/`).
2. GitHub Actions pipeline automatically:
   - Builds the Docker image for the updated Lambda.
   - Pushes the image to ECR.
   - Re-runs Terraform to:
     - Update Lambda functions with the **new Docker image digest**.
     - Deploy any infra changes (S3, SQS, roles).

✅ No manual intervention needed after pushing code!

---

## 📁 Project Structure

| Folder                               | Purpose                                                       |
| :----------------------------------- | :------------------------------------------------------------ |
| `Backend/Services/VideoUploader/`    | Code for Upload Lambda (Python script, zipped)                |
| `Backend/Services/VideoTranscriber/` | Dockerized Lambda to transcribe video using Whisper model     |
| `Backend/Services/TextSummarizer/`   | Dockerized Lambda to summarize transcript using FLAN-T5 model |
| `Infrastructure/`                    | Terraform code for AWS infrastructure setup                   |

---

## ⚙️ Quick Manual Commands

When needed manually (in case of emergency deploy):

```bash
# Build and Push Transcriber Docker Image
cd Backend/Services/VideoTranscriber
docker build -t minute-maker-video-transcriber:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-ecr-url>
docker tag minute-maker-video-transcriber:latest <your-ecr-url>/minute-maker-video-transcriber:latest
docker push <your-ecr-url>/minute-maker-video-transcriber:latest

# Build and Push Summarizer Docker Image
cd Backend/Services/TextSummarizer
docker build -t minute-maker-summarizer:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-ecr-url>
docker tag minute-maker-summarizer:latest <your-ecr-url>/minute-maker-summarizer:latest
docker push <your-ecr-url>/minute-maker-summarizer:latest

# Deploy Infrastructure
cd Infrastructure
terraform init
terraform plan
terraform apply
```
