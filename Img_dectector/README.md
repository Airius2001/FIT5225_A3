<!-- deploy the lambda function though Elastic Container Registry -->
# Basic guide for deploying lambda function into AWS
# Reference from : https://docs.aws.amazon.com/lambda/latest/dg/python-image.html


<!-- Build the Docker image with the docker build command. The following example names the image docker-image and gives it the test tag. To make your image compatible with Lambda, you must use the --provenance=false option. -->
docker buildx build --platform linux/amd64 --provenance=false -t docker-image:test .


# repository-name I name it as images.
<!-- Create a repository in Amazon ECR using the create-repository command. -->
aws ecr create-repository --repository-name images --region us-east-1 --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

# Keep the return value for later use
<!-- the return value paste here (From terminal) -->
{
    "repository": {
        "repositoryArn": "arn:aws:ecr:us-east-1:679621786483:repository/images",
        "registryId": "679621786483",
        "repositoryName": "images",
        "repositoryUri": "679621786483.dkr.ecr.us-east-1.amazonaws.com/images",
        "createdAt": "2025-06-06T13:26:11.789000+10:00",
        "imageTagMutability": "MUTABLE",
        "imageScanningConfiguration": {
            "scanOnPush": true
        },
        "encryptionConfiguration": {
            "encryptionType": "AES256"
        }
    }
}

# replace the real repositoryUri from your aws account 
docker tag docker-image:test 679621786483.dkr.ecr.us-east-1.amazonaws.com/images:latest

<!-- AWS ECR Login -->
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 679621786483.dkr.ecr.us-east-1.amazonaws.com

<!-- push image -->
docker push 679621786483.dkr.ecr.us-east-1.amazonaws.com/images:latest



# These following code is for deploy/update/check for the lambda function
<!-- deploy function -->
aws lambda create-function `
  --function-name detectImageVideoFunction `
  --package-type Image `
  --code ImageUri=679621786483.dkr.ecr.us-east-1.amazonaws.com/images:latest `
  --role arn:aws:iam::679621786483:role/LabRole `
  --memory-size 2048 `
  --timeout 180 `
  --region us-east-1 `
  --architectures x86_64

<!-- update lambda -->
aws lambda update-function-code `
  --function-name detectImageVideoFunction `
  --image-uri 679621786483.dkr.ecr.us-east-1.amazonaws.com/images:latest `
  --publish

<!-- checking the updated lambda function is ready or not -->
aws lambda get-function-configuration `
  --function-name detectImageVideoFunction `
  --region us-east-1


# The process for uodate the lambda function 
# (once you changed the code from lambda function, you have to rebuild the docker image, then push image and last to update the lambda function)
<!-- docker build -->
docker buildx build --platform linux/amd64 --provenance=false -t 679621786483.dkr.ecr.us-east-1.amazonaws.com/images:latest .

<!-- docker push -->
docker push 679621786483.dkr.ecr.us-east-1.amazonaws.com/images:latest

<!-- update lambda -->
aws lambda update-function-code `
  --function-name detectImageVideoFunction `
  --image-uri 679621786483.dkr.ecr.us-east-1.amazonaws.com/images:latest `
  --publish