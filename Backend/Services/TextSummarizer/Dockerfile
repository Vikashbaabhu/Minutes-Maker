# Using official AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR /var/task

# Install only necessary Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only main Lambda handler
COPY main.py .

# Define the Lambda handler
CMD ["main.lambda_handler"]
