from ultralytics import YOLO
import supervision as sv
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import os
import requests


def handler(event, context):
    return 

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



if __name__ == '__main__':
    print("predicting...")
    # print(image_prediction("./test_images/crows_1.jpg"))
    print(video_prediction("./test_videos/crows.mp4",result_filename='crows_detected.mp4'))

