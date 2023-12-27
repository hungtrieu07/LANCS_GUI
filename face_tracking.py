import datetime
from io import BytesIO
import cv2
import requests
import numpy as np
from PIL import Image


def convert_frame(frame):
    # cv2.imwrite("input_frame.jpg", frame)
    current_time = int(datetime.datetime.now().timestamp())

    map_time = list(map(int, str(current_time)))
    remainder = frame.shape[0] % 10
    quotient = frame.shape[0] // 10

    output = quotient * map_time
    output.extend(map_time[:remainder])

    add_array = np.array(output)
    add_array = add_array.reshape(1, -1, 1)

    empty_arr = np.zeros_like(frame[:1])

    empty_arr[:, : add_array.shape[1]] = add_array

    # Create a new image with the last row as add_array
    modified_image = np.concatenate((frame, empty_arr), axis=0)
    # byte_array = modified_image.tobytes(order="C")

    send_image = Image.fromarray(modified_image)
    image2bytes = BytesIO()
    send_image.save(image2bytes, format="PNG")
    image2bytes.seek(0)
    return image2bytes.read()

def draw_keypoints(frame, keypoints):
    for point in keypoints[0]['keypoints'][0]:
        x, y, _ = point
        cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 0), -1)

# Replace with your server IP
server_IP = '192.168.1.101'

human_keypoint_URL = f"http://{server_IP}:8090/predictions/HumanPose"
action_recognition_URL = f"http://{server_IP}:8090/predictions/ActionRecognition"

# You can integrate this into your existing code
# For example, read a video file or capture from a webcam
cap = cv2.VideoCapture('rtsp://admin:abcd1234@222.252.97.113:8007/h264_stream')  # Replace with your video file path or camera index

# Get video frame dimensions
width = int(cap.get(3))
height = int(cap.get(4))

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
output_file = cv2.VideoWriter('output_video.mp4', fourcc, 20.0, (width, height))


while cap.isOpened():
    ret, frame = cap.read()
    image_data = convert_frame(frame)

    if not ret:
        break
    
    # Send image data for human pose estimation
    human_keypoint_response = requests.post(human_keypoint_URL, data=image_data)

    # Check if the request was successful
    if human_keypoint_response.status_code == 200:
        human_keypoint_result = human_keypoint_response.json()

        # Assuming human_keypoint_result is in the format you provided earlier
        keypoints = human_keypoint_result

        # Draw keypoints on the current frame
        draw_keypoints(frame, keypoints)
        
        output_file.write(frame)

# Release the video capture object and close all windows
cap.release()
output_file.release()
cv2.destroyAllWindows()