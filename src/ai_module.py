import os
import time
from io import BytesIO

import cv2
import numpy as np
import requests
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from numpy.linalg import norm
from PIL import Image
from PyQt5 import QtCore, QtWidgets
from ui.ui_mainwindow import Ui_MainWindow
from pymilvus import Collection, connections, db

program_start_time = time.time()

max_cosine_distance = 0.4
nn_budget = None
metric = nn_matching.NearestNeighborDistanceMetric(
    "cosine", max_cosine_distance, nn_budget
)

# MILVUS DATABASE
conn = connections.connect(host='10.37.239.102', port=19530)
db.using_database("face_recognition")

### GET FACE EMBEDDING FROM DATABASE
collection = Collection("face_recognition")
result = collection.query(expr="face_id >= 0", output_fields=["face_id", "face_vector"])
# print(result[0]["face_id"])
# print(result[0]["face_vector"])

# emb_db = "deep_sort/emb_db"
# database = []
# list_emb = os.listdir(emb_db)

# for file in list_emb:
#     file_path = os.path.join(emb_db, file)
#     data = np.load(file_path)
#     id = file.split(".")[0]
#     database.append([id, data])

class AI(QtCore.QObject):
    def __init__(self, parent: QtWidgets.QMainWindow):
        super().__init__(parent)
        self.ui: Ui_MainWindow = parent.ui

        # initialize tracker
        self.tracker = Tracker(metric)

    def convert_frame(self, frame):
        send_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        image2bytes = BytesIO()
        send_image.save(image2bytes, format="PNG")
        image2bytes.seek(0)
        return image2bytes.read()

    def get_cosine_similarity(self, emb1, emb2):
        return np.degrees(np.arccos(np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))))

    def compare_emb(self, api_output):
        vectors_to_search = api_output
        print(vectors_to_search)
        
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }

        collection.load()
        collection.search(vectors_to_search, "face_vector", search_params, limit=1, output_fields=["face_id"])
        
        # MIN = 999
        # thresh = 88
        # ID = None
        # for id in data:
        #     for emb2 in id[1]:
        #         dist = self.get_cosine_similarity(emb1, emb2)
        #         # print(dist)
        #         if dist < MIN:
        #             MIN = dist
        #             ID = id[0]
        # # print(MIN)
        # if MIN <= thresh:
        #     return ID
        # else:
        #     return "None"

    def get_area_detect(self, frame, points):
        mask = np.zeros(frame.shape[:2], np.uint8)
        cv2.drawContours(mask, [points], -1, (255, 255, 255), -1, cv2.LINE_AA)
        return cv2.bitwise_and(frame, frame, mask=mask)

    def do_object_detection(self, frame: np.ndarray):
        image_data = self.convert_frame(frame)
        server_IP = str(self.ui.comboBoxServerIP.currentText())

        face_detection_URL = f"http://{server_IP}:8090/predictions/FaceDetection"
        face_recognition_URL = f"http://{server_IP}:8090/predictions/FaceRecognition"
        face_expression_URL = f"http://{server_IP}:8090/predictions/FaceExpression"
        human_keypoint_URL = f"http://{server_IP}:8090/predictions/HumanPose"
        action_recognition_URL = (
            f"http://{server_IP}:8090/predictions/ActionRecognition"
        )

        face_detection_response = requests.post(face_detection_URL, data=image_data)
        
        human_keypoint_response = requests.post(human_keypoint_URL, data=image_data)
        # if human_keypoint_response.status_code == 200:
        human_keypoint = human_keypoint_response.json()[0]["keypoints"]
        human_bboxes = human_keypoint_response.json()[0]["bbox"]
        # print(human_keypoint_response.json())
        
        for keypoint, human_box in zip(human_keypoint, human_bboxes):
            print(np.array(keypoint).shape)
            print(human_box)
        
        # temp = np.array(human_keypoint_result)
        # print(temp.shape)

        # action_recognition_response = requests.post(action_recognition_URL, data=image_data)
        # # if action_recognition_response.status_code == 200:
        # action_recognition_result = action_recognition_response.json()
        # print(action_recognition_result)
        
        if face_detection_response.status_code == 200:
            face_detection_result = face_detection_response.json()
            # print(face_detection_result)
            boxes = face_detection_result[0]["bbox"]

        dets = []
        fers = []
        for box in boxes:
            box = list(map(int, box))
            x = box[0]
            y = box[1]
            w = box[2] - box[0]
            h = box[3] - box[1]

            face = frame[box[1] : box[3], box[0] : box[2]]
            cv2.imwrite("face.jpg", face)
            
            face_data = self.convert_frame(face)
            
            face_recognition_response = requests.post(
                face_recognition_URL, data=face_data
            )
            face_expression_response = requests.post(
                face_expression_URL, data=face_data
            )

            if (
                face_recognition_response.status_code == 200
                and face_expression_response.status_code == 200
            ):
                face_recognition_result = face_recognition_response.json()
                emb = face_recognition_result["output"]

                face_expression_result = face_expression_response.json()
                expression = face_expression_result["output"]

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
            pass
