from ultralytics import YOLO
import supervision as sv
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import os
import requests
import boto3

from collections import Counter


s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
TABLE = "media"

# s3 event handling logic
def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # download the image from S3
        tmp_path = f"/tmp/{key.split('/')[-1]}"
        s3_client.download_file(bucket, key, tmp_path)

        # Call the image_prediction function
        labels = []
        if key.startswith('images/'): # the folder name from AWS S3 bucket
            labels = image_prediction(tmp_path)
            # resize the image size to thumbnails
            b = create_thumbnail(tmp_path)
            s3_client.put_object(
                Bucket = bucket,
                Key = f"thumbnails/{key.split('/')[-1]}",
                Body = b,
                ContentType = 'mimetype',
                ContentDisposition = 'inline'
            )

        elif key.startswith('videos/'): # the folder name from AWS S3 bucket
            labels = video_prediction(tmp_path)
        else:
            print(f'Unsupported file type for key: {key}')
            return
        labels_total = Counter(labels)

        try:
            dynamodb.Table(TABLE).put_item(
                Item = {
                    's3-url': "https://{0}.s3.us-east-1.amazonaws.com/{1}".format(bucket,key),
                    'tags': labels_total
                }
            )
        except boto3.ClientError as err:
            print(f"Error saving to DynamoDB: {err}")
        except Exception as e:
            print(f"Unexpected error occured: {e}")


def create_thumbnail(image_path, width = 150, height = 150):
    _ ,ext = os.path.splittext(image_path)
    img = cv.imread(image_path)
    if img is None:
        print("Can not load the image, please check the path")
        return None
    thumbnail = cv.resize(img, (width, height))
    ok, buffer = cv.imencode(ext, thumbnail)
    if not ok:
        print("Error encoding the image.")
        return None
    
    return buffer.tobytes()
    

# image prediction function
def image_prediction(image_path, confidence=0.5, model="./model.pt"):
    """
    Function to display predictions of a pre-trained YOLO model on a given image.

    Parameters:
        image_path (str): Path to the image file. Can be a local path or a URL.
        result_path (str): If not None, this is the output filename.
        confidence (float): 0-1, only results over this value are saved.
        model (str): path to the model.
    """

    # Load YOLO model
    model = YOLO(model)
    class_dict = model.names

    # Load image from local path
    img = cv.imread(image_path)

    # Check if image was loaded successfully
    if img is None:
        print("Couldn't load the image! Please check the image path.")
        return

    # Run the model on the image
    result = model(img)[0]

    # Convert YOLO result to Detections format
    detections = sv.Detections.from_ultralytics(result)

    # Filter detections based on confidence threshold and check if any exist
    if detections.class_id is not None:
        detections = detections[(detections.confidence > confidence)]

        # Create labels for the detected objects
        labels = [f"{class_dict[cls_id]}" for cls_id in 
                  detections.class_id]
    return labels



# ## Video Detection
def video_prediction(video_path, result_filename=None, save_dir = "./video_prediction_results", confidence=0.5, model="./model.pt"):
    """
    Function to make predictions on video frames using a trained YOLO model and display the video with annotations.

    Parameters:
        video_path (str): Path to the video file.
        save_video (bool): If True, saves the video with annotations. Default is False.
        filename (str): The name of the output file where the video will be saved if save_video is True.
    """

    labels = []

    try:
        # Load video info and extract width, height, and frames per second (fps)
        video_info = sv.VideoInfo.from_video_path(video_path=video_path)
        # only need to know the fps, others not necessary so deleted
        fps = int(video_info.fps)

        model = YOLO(model)  # Load your custom-trained YOLO model
        tracker = sv.ByteTrack(frame_rate=fps)  # Initialize the tracker with the video's frame rate
        class_dict = model.names  # Get the class labels from the model
        
        # Capture the video from the given path
        cap = cv.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Error: couldn't open the video!")

        # Process the video frame by frame
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:  # End of the video
                break

            # Make predictions on the current frame using the YOLO model
            result = model(frame)[0]
            detections = sv.Detections.from_ultralytics(result)  # Convert model output to Detections format
            detections = tracker.update_with_detections(detections=detections)  # Track detected objects

            # Filter detections based on confidence
            if detections.tracker_id is not None:
                detections = detections[(detections.confidence > confidence)]  # Keep detections with confidence greater than a threashold

                labels_1 = [f"{class_dict[cls_id]}" for cls_id in
                            detections.class_id]
                labels.extend(labels_1)
        return labels

    except Exception as e:
        print(f"An error occurred: {e}")
        return labels

    finally:
        # Release resources
        cap.release()
        print("Video processing complete, Released resources.")


# test the function locally
if __name__ == '__main__':
    print("predicting...")
    print(image_prediction("./test_images/crows_1.jpg"))
    # print(video_prediction("./test_videos/crows.mp4",result_filename='crows_detected.mp4'))

