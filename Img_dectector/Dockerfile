# Use the official AWS Lambda Python 3.10 base image
FROM public.ecr.aws/lambda/python:3.10

# Set working directory
WORKDIR /var/task

# Install system packages required for building dependencies
RUN yum -y update && yum install -y gcc gcc-c++ make cmake unzip git

# Upgrade pip and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the application code and model
COPY lambda.py .
COPY model.pt .

# Set the Lambda handler
CMD ["lambda.handler"]
