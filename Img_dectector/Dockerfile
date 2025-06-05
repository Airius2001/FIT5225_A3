FROM public.ecr.aws/lambda/python:3.10

WORKDIR /var/task

COPY lambda.py .
COPY model.pt .
COPY requirements.txt .

# Install dependencies efficiently
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["lambda.handler"]
