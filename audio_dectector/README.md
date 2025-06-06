<!-- TO TEST THE LOCAL TEST AUDIO FUNCTION -->
have to switch the python version to 3.10, then create a vm with 3.10 version. 
Because the tensorflow is not compatible for 3.12 or 3.13

<!-- deploy the lambda function though Elastic Container Registry -->
# Basic guide for deploying lambda function into AWS
# Reference from : https://docs.aws.amazon.com/lambda/latest/dg/python-image.html


# I create a new repository and name it as audios
<!-- create reporsity -->
aws ecr create-repository --repository-name audios --region us-east-1 --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

<!--AWS ECR login -->
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 679621786483.dkr.ecr.us-east-1.amazonaws.com


# Keep the return value for later use
<!-- the return value paste here (From terminal) -->
{
    "repository": {
        "repositoryArn": "arn:aws:ecr:us-east-1:679621786483:repository/audios",
        "registryId": "679621786483",
        "repositoryName": "audios",
        "repositoryUri": "679621786483.dkr.ecr.us-east-1.amazonaws.com/audios",
        "createdAt": "2025-06-06T18:26:56.365000+10:00",
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
docker tag docker-image:test 679621786483.dkr.ecr.us-east-1.amazonaws.com/audios:latest


<!-- AWS ECR Login -->
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 679621786483.dkr.ecr.us-east-1.amazonaws.com

<!-- push image -->
docker push 679621786483.dkr.ecr.us-east-1.amazonaws.com/audios:latest



# These following code is for deploy/update/check for the lambda function
<!-- deploy function -->
aws lambda create-function `
  --function-name detectAudioFunction `
  --package-type Image `
  --code ImageUri=679621786483.dkr.ecr.us-east-1.amazonaws.com/audios:latest `
  --role arn:aws:iam::679621786483:role/LabRole `
  --memory-size 2048 `
  --timeout 180 `
  --region us-east-1 `
  --architectures x86_64

<!-- update lambda -->
aws lambda update-function-code `
  --function-name detectAudioFunction `
  --image-uri 679621786483.dkr.ecr.us-east-1.amazonaws.com/audios:latest `
  --publish

<!-- checking the updated lambda function is ready or not -->
aws lambda get-function-configuration `
  --function-name detectAudioFunction `
  --region us-east-1


# The process for uodate the lambda function 
# (once you changed the code from lambda function, you have to rebuild the docker image, then push image and last to update the lambda function)
<!-- docker build -->
docker buildx build --platform linux/amd64 --provenance=false -t 679621786483.dkr.ecr.us-east-1.amazonaws.com/audios:latest .

<!-- docker push -->
docker push 679621786483.dkr.ecr.us-east-1.amazonaws.com/audios:latest

<!-- update lambda -->
aws lambda update-function-code `
  --function-name detectAudioFunction `
  --image-uri 679621786483.dkr.ecr.us-east-1.amazonaws.com/audios:latest `
  --publish
