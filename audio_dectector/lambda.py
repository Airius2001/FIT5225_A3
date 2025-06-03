import os
import boto3
from collections import Counter


# COPY FROM https://joeweiss.github.io/birdnetlib/#using-birdnet-analyzer 
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
TABLE = "media"

# s3 event handling logic
def handler(event, context):
    s3_client = boto3.client('s3')

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # download the audio file from S3
        tmp_path = f"/tmp/{os.path.basename(key)}"
        s3_client.download_file(bucket, key, tmp_path)

        # Call the image_prediction function
        labels = []
        if key.startswith('audios/'): # the folder name from AWS S3 bucket
            labels = audio_dectector(tmp_path)
        labels_total = Counter(labels)
        table = dynamodb.Table(TABLE)

        response = table.put_item(
            Item = {
                    's3-url': "https://{0}.s3.us-east-1.amazonaws.com/{1}".format(bucket,key),
                    'tags': labels_total
                }
        )

        print(f"Processed {key} and saved results to {response}")

# audio dectector function
def audio_dectector(audio_path):
    # Load and initialize the BirdNET-Analyzer models.
    analyzer = Analyzer(
        classifier_model_path ="model/BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite",
        classifier_labels_path ="model/BirdNET_GLOBAL_6K_V2.4_Labels.txt",
    )

    recording = Recording(
        analyzer,
        audio_path,
        min_conf=0.5,
    )

    recording.analyze()
    labels = []
    for dectection in recording.dectections:
        labels.append(dectection["common_name"])

    return labels

# test the function locally
if __name__ == '__main__':
    print("predicting...")
    print(audio_dectector("./test_audios/soundscape.wav"))
