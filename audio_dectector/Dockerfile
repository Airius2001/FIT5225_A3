# This is the example copied dockerfile from Official documentation 
# reference from : https://docs.aws.amazon.com/lambda/latest/dg/python-image.html

FROM public.ecr.aws/lambda/python:3.9

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Install libsndifile in order the soundfile can R/W audio
RUN yum install -y libsndfile \
    libsndfile-devel \
 && yum clean all


# Copy function code
COPY lambda.py ${LAMBDA_TASK_ROOT}
# copy model
COPY BirdNET_GLOBAL_6K_V2.4_Labels.txt ${LAMBDA_TASK_ROOT}
COPY BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite ${LAMBDA_TASK_ROOT}


# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda.handler" ]