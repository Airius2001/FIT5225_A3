from ultralytics import YOLO
import supervision as sv
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import os
import requests

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

    # Get image dimensions
    # h, w = img.shape[:2]

    # Calculate optimal thickness for boxes and text based on image resolution
    # thickness = sv.calculate_optimal_line_thickness(resolution_wh=(w, h))
    # text_scale = sv.calculate_optimal_text_scale(resolution_wh=(w, h))

    # Set up color palette for annotations
    # color_palette = sv.ColorPalette.from_matplotlib('magma', 10)

    # Create box and label annotators
    # box_annotator = sv.BoxAnnotator(thickness=thickness, color=color_palette)
    # label_annotator = sv.LabelAnnotator(color=color_palette, text_scale=text_scale, 
    #                                     text_thickness=thickness, 
    #                                     text_position=sv.Position.TOP_LEFT)

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

        # Annotate the image with boxes and labels
        # box_annotator.annotate(img, detections=detections)
        # label_annotator.annotate(img, detections=detections, labels=labels)
    return labels
    # if result_filename:
    #     os.makedirs(save_dir, exist_ok=True)  # Ensure the save directory exists
    #     save_path = os.path.join(save_dir, result_filename)
    #     try:
    #         status = cv.imwrite(save_path, img)
    #         print(f"Image save status = {status}.")
    #     except Exception as e:
    #         print(f"Error saving image: {e}")
    # else:
    #     print("Filename is none, result is not saved.")



if __name__ == '__main__':
    print("predicting...")
    print(image_prediction("./test_images/crows_1.jpg"))
