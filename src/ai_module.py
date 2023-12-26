import concurrent.futures
import datetime
import json
import os
import time
from io import BytesIO
from numpy.linalg import norm

import cv2
import numpy as np
import requests
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from PIL import Image
from PyQt5 import QtCore, QtWidgets
from ui.ui_mainwindow import Ui_MainWindow

program_start_time = time.time()

max_cosine_distance = 0.4
nn_budget = None
metric = nn_matching.NearestNeighborDistanceMetric(
    "cosine", max_cosine_distance, nn_budget
)


emb_db = "deep_sort/emb_db"
database = []
list_emb = os.listdir(emb_db)

for file in list_emb:
    file_path = os.path.join(emb_db, file)
    data = np.load(file_path)
    id = file.split(".")[0]
    database.append([id, data])


class AI(QtCore.QObject):
    def __init__(self, parent: QtWidgets.QMainWindow):
        super().__init__(parent)
        self.ui: Ui_MainWindow = parent.ui
        
        self.frame_counter = 0
        self.frame_threshold = 1000

        # initialize tracker
        self.tracker = Tracker(metric)

    def convert_frame(self, frame):
        cv2.imwrite("input_frame.jpg", frame)
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

    def get_cosine_similarity(self, emb1, emb2):
        return np.degrees(np.arccos(np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))))

    def compare_emb(self, emb1, data):
        MIN = 999
        thresh = 88
        ID = None
        for id in data:
            for emb2 in id[1]:
                dist = self.get_cosine_similarity(emb1, emb2)
                # print(dist)
                if dist < MIN:
                    MIN = dist
                    ID = id[0]
        # print(MIN)
        if MIN <= thresh:
            return ID
        else:
            return "None"

    def get_area_detect(self, frame, points):
        mask = np.zeros(frame.shape[:2], np.uint8)
        cv2.drawContours(mask, [points], -1, (255, 255, 255), -1, cv2.LINE_AA)
        return cv2.bitwise_and(frame, frame, mask=mask)

    # @profile
    def do_object_detection(
        self,
        frame: np.ndarray,
        violation_frame: np.ndarray,
        location: str,
        id_cam: str,
        coordinates: list,
    ):
        image_data = self.convert_frame(frame)
        server_IP = str(self.ui.comboBoxServerIP.currentText())

        face_detection_URL = f"http://{server_IP}:8090/predictions/FaceDetection"
        face_recognition_URL = f"http://{server_IP}:8090/predictions/FaceRecognition"
        face_expression_URL = f"http://{server_IP}:8090/predictions/FaceExpression"
        human_keypoint_URL = f"http://{server_IP}:8090/predictions/HumanPose"
        action_recognition_URL = (
            f"http://{server_IP}:8090/predictions/ActionRecognition"
        )

        # Define a mapping between URL and type
        url_type_mapping = {
            face_detection_URL: "Face Detection",
            face_recognition_URL: "Face Recognition",
            face_expression_URL: "Face Expression",
            human_keypoint_URL: "Human Pose Keypoint",
            action_recognition_URL: "Action Recognition",
        }
        
        if self.frame_counter % self.frame_threshold == 0:

            # Use a ThreadPoolExecutor for parallel execution of requests
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit API requests concurrently
                futures = [
                    executor.submit(requests.post, url, data=image_data)
                    for url in [
                        face_detection_URL,
                        face_recognition_URL,
                        face_expression_URL
                    ]
                ]

            # Process the responses
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                url = response.request.url
                response_type = url_type_mapping.get(url, "Unknown Type")

                if response.status_code == 200:
                    response_data = response.json()

                    # Process the data based on the response type
                    if response_type == "Face Detection":
                        # Process face detection data
                        outputs = response_data[0]["output"]
                        boxes = response_data[0]["bbox"]
                        scores = response_data[0]["score"]
                        # print(outputs)
                    elif response_type == "Face Recognition":
                        # Process face recognition data
                        emb = response_data["output"]
                        # print(emb)
                    elif response_type == "Face Expression":
                        # Process face expression data
                        expression = response_data["output"]
                        # print(expression)

                    height, width = frame.shape[:2]
                    output = []
                    filter_class = [0]
                    dets = []
                    fers = []
                    for box in boxes:
                        box = list(map(int, box))
                        x = box[0]
                        y = box[1]
                        w = box[2] - box[0]
                        h = box[3] - box[1]

                        face = frame[box[1] : box[3], box[0] : box[2]]
                        fers.append(expression)
                        user_name = self.compare_emb(emb, database)
                        print(user_name)
                        dets.append(
                            Detection([x, y, w, h], user_name, np.array(emb).flatten())
                        )

                    self.tracker.predict()
                    self.tracker.update(dets)

                    # update tracks
                    for track, ex in zip(self.tracker.tracks, fers):
                        if not track.is_confirmed() or track.time_since_update > 1:
                            continue
                        bbox = track.to_tlbr()
                        name = track.get_name()
                        id = track.track_id
                        print(id)
                        # color = [0, 0, 0]
                        # cv2.rectangle(
                        #     frame,
                        #     (int(bbox[0]), int(bbox[1])),
                        #     (int(bbox[2]), int(bbox[3])),
                        #     color,
                        #     2,
                        # )
                        # cv2.rectangle(
                        #     frame,
                        #     (int(bbox[0]), int(bbox[1] - 30)),
                        #     (int(bbox[0]) + (len(name)) * 15, int(bbox[1])),
                        #     color,
                        #     -1,
                        # )
                        # cv2.putText(
                        #     frame,
                        #     str(name) + ":" + str(ex),
                        #     (int(bbox[0]), int(bbox[1] - 10)),
                        #     0,
                        #     0.75,
                        #     (255, 255, 255),
                        #     2,
                        # )
                else:
                    # Handle non-200 responses if needed
                    # print(f"{response_type} have error {response.status_code}")
                    pass
                
        else:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(requests.post, url, data=image_data)
                           for url in [human_keypoint_URL, action_recognition_URL]
                        ]
            
            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                url = response.request.url
                response_type = url_type_mapping.get(url, "Unknown Type")

                if response.status_code == 200:
                    response_data = response.json()

                    # Process the data based on the response type
                    if response_type == "Human Pose Keypoint":
                        keypoint = response_data['keypoint']
                        print(keypoint)
                    elif response_type == "Action Recognition":
                        action = response_data["output"]
                        print(action)
