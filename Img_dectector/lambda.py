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
    """
    AWS Lambda function entry point to handle S3 file upload events.
    
    Args:    
    event (dict): AWS Lambda event object containing S3 trigger information    
    context (object): Lambda runtime context object
    
    Returns:    
    None: No explicit return value
    
    Notes:
    - Automatically handles images/videos uploaded to S3
    - Generates thumbnails for images
    - Detects bird species in files and logs to DynamoDB
    - Errors will be logged but will not interrupt processing
    """

    for record in event['Records']:
        try:
            # Analysis of Bucket and Key
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            filename = key.split('/')[-1]
            tmp_path = f"/tmp/{filename}"

            print(f"Trying to download s3://{bucket}/{key} → {tmp_path}")
            s3_client.download_file(bucket, key, tmp_path)
            print("✅ File downloaded")

            labels = []

            # Image processing branch
            if key.startswith('images/'):
                labels = image_prediction(tmp_path)
                b = create_thumbnail(tmp_path)
                if b is not None:
                    s3_client.put_object(
                        Bucket=bucket,
                        Key=f"thumbnails/{filename}",
                        Body=b,
                        ContentType='image/jpeg',
                        ContentDisposition='inline'
                    )
                    print(f"✅ Thumbnail uploaded to thumbnails/{filename}")
                else:
                    print("⚠️ Failed to create thumbnail.")

            # Video processing branch
            elif key.startswith('videos/'):
                labels = video_prediction(tmp_path)

            else:
                print(f"⚠️ Unsupported file type: {key}")
                continue

            # Label statistics & store in DynamoDB
            labels_total = Counter(labels)

            dynamodb.Table(TABLE).put_item(
                Item={
                    's3-url': f"https://{bucket}.s3.amazonaws.com/{key}",
                    'tags': labels_total
                }
            )
            print("✅ Tags saved to DynamoDB")

        except Exception as e:
            print(f"❌ Error processing file {key}: {e}")
            continue  # Does not affect the processing of other records



#  transfer the image to thumbnail image
def create_thumbnail(image_path, width = 200, height = 200):
    """
    Generate a thumbnail from the image file at the given path and return the binary data of the thumbnail.
    Parameters:
        image_path (str): The path to the original image 
        filewidth (int): The width of the thumbnail (set it as 200px)
        height (int): The height of the thumbnail (set it as 200px)
        Returns:bytes: The binary data of the thumbnail, returns None on failure
        Raises:No explicit exceptions are raised, but file operation-related exceptions may be implicitly raised.
    """
    # Get file extension
    _ ,ext = os.path.splitext(image_path)
    # Read the original image file
    img = cv.imread(image_path)
    if img is None:
        print("Can not load the image, please check the path")
        return None
    try:
        # Adjust the image size to the specified width and height.
        thumbnail = cv.resize(img, (width, height))
        ok, buffer = cv.imencode(ext, thumbnail)
        
        if not ok:
            print("Image encoding failed")
            return None
        
        # Return the binary data of the thumbnail.
        return buffer.tobytes()
    except Exception as e:
        print(f"An error occurred while generating the thumbnail.: {str(e)}")
        return None
    

# image prediction function
def image_prediction(image_path, confidence=0.5, model="./model.pt"):
    """
    Use the YOLO model to perform object detection on the input image and return a list of detected bird labels.

    Args:
    image_path (str): Path to the image file to be detected.
    confidence (float): Confidence threshold (0-1), default is 0.5.
    model (str): Path to the YOLO model file, default is "./model.pt".
    Returns:list: List of detected bird labels (e.g., ["crow", "pigeon"]); returns None on failure.

    Notes:
    - Uses the Ultralytics YOLO model for detection.
    - Relies on OpenCV to read the image.
    - Uses the supervision library to process detection results.
    """

    # Load the YOLO model
    # model: the loaded YOLO model object
    # class_dict: dictionary of categories supported by the model (e.g., {0: "crow", 1: "pigeon"})
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
    Use the YOLO model for frame-by-frame object detection on a video, returning all detected bird labels.
    
    Args:
    video_path (str): Input video file 
    pathresult_filename (str, optional): Result save file name, default None (does not save)
    save_dir (str): Result save directory, default "./video_prediction_results"
    confidence (float): Confidence threshold (0-1), default 0.5
    model (str): YOLO model file path, default "./model.pt"
    
    Returns:
    list: List of all bird labels detected in the video (e.g. ["crow", "pigeon", "crow"])
    
    Notes:
    - Use ByteTrack for object tracking to maintain ID consistency
    - Automatically release video resources to ensure there is no memory leak
    - In case of an error, it will return the detected labels and print the error message.
    """


    # Initialize the label list to store the detection results for the entire video.
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
            # Read the next frame
            # # ret: Whether the frame was successfully read
            # # frame: Current frame image (BGR format)
            ret, frame = cap.read()
            # End of the video
            if not ret:  
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

