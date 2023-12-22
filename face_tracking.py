# from TFLiteFaceDetector import UltraLightFaceDetecion
import datetime
from io import BytesIO
import os
import time
from PIL import Image

import cv2
import numpy as np
import requests
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker

# from face_fer import FER
# from mtcnn import MTCNN
# from infer_resnet import Arcface_Resnet
from numpy.linalg import norm
import traceback

# from predictor_v8 import Detect_v8
# from retinaface.pre_trained_models import get_model
# from tracker.byte_tracker import BYTETracker

Frame_rate = 1
# calculate cosine distance metric
max_cosine_distance = 0.4
nn_budget = None
metric = nn_matching.NearestNeighborDistanceMetric(
    "cosine", max_cosine_distance, nn_budget
)
# initialize tracker
tracker = Tracker(metric)


def get_area_detect(img, points):
    # points = points.reshape((-1, 1, 2))
    mask = np.zeros(img.shape[:2], np.uint8)
    cv2.drawContours(mask, [points], -1, (255, 255, 255), -1, cv2.LINE_AA)
    dts = cv2.bitwise_and(img, img, mask=mask)
    return dts


def get_distance_embeddings(emb1, emb2):
    diff = np.subtract(emb1, emb2)
    dist = np.sum(np.square(diff))
    return dist


def get_cosine_similarity(emb1, emb2):
    return np.degrees(np.arccos(np.dot(emb1, emb2) / (norm(emb1) * norm(emb2))))


def compare_emb(emb1, data):
    MIN = 999
    thresh = 88
    ID = None
    for id in data:
        for emb2 in id[1]:
            dist = get_cosine_similarity(emb1, emb2)
            # print(dist)
            if dist < MIN:
                MIN = dist
                ID = id[0]
    # print(MIN)
    if MIN <= thresh:
        return ID
    else:
        return "None"


def convert_frame(frame):
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


if __name__ == "__main__":
    video_path = "rtsp://admin:abcd1234@222.252.97.113:8008/h264_stream"

    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    size = (frame_width, frame_height)
    result = cv2.VideoWriter(
        "result.mp4", cv2.VideoWriter_fourcc(*"MP4V"), 20, size
    )

    emb_db = "deep_sort/emb_db"
    database = []
    list_emb = os.listdir(emb_db)

    for file in list_emb:
        file_path = os.path.join(emb_db, file)
        data = np.load(file_path)
        id = file.split(".")[0]
        database.append([id, data])
    try:
        while True:
            ret, frame = cap.read()
            if ret:
                pts = np.array(
                    [
                        [0, frame_height / 2 - 90],
                        [frame_width, frame_height / 2 - 90],
                        [frame_width, frame_height],
                        [0, frame_height],
                    ],
                    np.int32,
                )
                # crop frame
                img_croped = get_area_detect(frame, pts)
                step = time.time()
                post_image = convert_frame(frame)

                face_detector = requests.post(
                    "http://10.37.239.102:8090/predictions/FaceDetection",
                    data=post_image,
                )
                face_recognizer = requests.post(
                    "http://10.37.239.102:8090/predictions/FaceRecognition",
                    data=post_image,
                )
                face_expression = requests.post(
                    "http://10.37.239.102:8090/predictions/FaceExpression",
                    data=post_image,
                )

                print("FACE DETECTION:")
                face_detection_result = face_detector.json()
                outputs = face_detection_result[0]["output"]
                boxes = face_detection_result[0]["bbox"]
                scores = face_detection_result[0]["score"]
                print(outputs, boxes, scores)

                print("FACE RECOGNITION:")
                face_recognizer_result = (
                    face_recognizer.json()
                )  ### RETURN EMBEDDING VECTOR
                emb = face_recognizer_result["output"]
                print(emb)

                print("FACE EXPRESSION:")
                face_expression_result = face_expression.json()
                expression = face_expression_result["output"]
                print(expression)

                Frame_rate = int(1 / (time.time() - step))
                # print("FPS:",(1/(time.time()-step)))
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
                    user_name = compare_emb(emb, database)
                    print(user_name)
                    dets.append(
                        Detection([x, y, w, h], user_name, np.array(emb).flatten())
                    )

                tracker.predict()
                tracker.update(dets)
                
                # update tracks
                for track, ex in zip(tracker.tracks, fers):
                    if not track.is_confirmed() or track.time_since_update > 1:
                        continue
                    bbox = track.to_tlbr()
                    name = track.get_name()
                    id = track.track_id
                    # print(id)
                    color = [0, 0, 0]
                    cv2.rectangle(
                        frame,
                        (int(bbox[0]), int(bbox[1])),
                        (int(bbox[2]), int(bbox[3])),
                        color,
                        2,
                    )
                    cv2.rectangle(
                        frame,
                        (int(bbox[0]), int(bbox[1] - 30)),
                        (int(bbox[0]) + (len(name)) * 15, int(bbox[1])),
                        color,
                        -1,
                    )
                    cv2.putText(
                        frame,
                        str(name) + ":" + str(ex),
                        (int(bbox[0]), int(bbox[1] - 10)),
                        0,
                        0.75,
                        (255, 255, 255),
                        2,
                    )
                    
                result.write(frame)

    except Exception:
        print(traceback.print_exc())
        # pass,
        # cap.release()
        # result.release()
        
