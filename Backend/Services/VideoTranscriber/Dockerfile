# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Install Python dependencies into Lambda environment
COPY requirements.txt .
RUN pip3 install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt --target .

# Copy your handler code
COPY main.py .

# Set environment variables
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}"

# Lambda entry point
CMD ["main.lambda_handler"]
