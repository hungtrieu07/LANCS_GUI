import asyncio
import datetime
import json
import os
import queue
import time
import traceback
from io import BytesIO

import cv2
import httpx
import numpy as np
import requests
from deep_sort import nn_matching
from deep_sort.detection import Detection
from deep_sort.tracker import Tracker
from numpy.linalg import norm
from PIL import Image

frame_queue = queue.Queue()
expression_task_last_run = 0

Frame_rate = 1
# calculate cosine distance metric
max_cosine_distance = 0.4
nn_budget = None
metric = nn_matching.NearestNeighborDistanceMetric(
    "cosine", max_cosine_distance, nn_budget
)
# initialize tracker
tracker = Tracker(metric)

def connect_to_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        print("Connected to video stream")
        return cap

async def async_request(url, data):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        return response


async def run_expression_task():
    expression_response = await async_request(
        "http://10.37.239.102:8090/predictions/FaceExpression",
        data=post_image,
    )

    expression = json.loads(expression_response.text)
    expression = expression['output']
    print(expression)


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
    result = cv2.VideoWriter("result.mp4", cv2.VideoWriter_fourcc(*"MP4V"), 20, size)

    emb_db = "deep_sort/emb_db"
    database = []
    list_emb = os.listdir(emb_db)

    for file in list_emb:
        file_path = os.path.join(emb_db, file)
        data = np.load(file_path)
        id = file.split(".")[0]
        database.append([id, data])

    try:
        frame_count = 0
        expression_task_last_run = 0

        while True:
            ret, frame = cap.read()
            if ret:
                frame_count += 1

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
                post_image = convert_frame(frame)

                if frame_count <= 20 or frame_count % 1000 == 0:
                    loop = asyncio.get_event_loop()
                    results = loop.run_until_complete(
                        asyncio.gather(
                            async_request(
                                "http://10.37.239.102:8090/predictions/FaceDetection",
                                data=post_image,
                            ),
                            async_request(
                                "http://10.37.239.102:8090/predictions/FaceRecognition",
                                data=post_image,
                            ),
                        )
                    )

                    # Wait for all requests to finish
                    face_detector_result = results[0].json()
                    face_recognizer_result = results[1].json()

                    outputs = face_detector_result[0]["output"]
                    boxes = face_detector_result[0]["bbox"]
                    scores = face_detector_result[0]["score"]

                    ### RETURN EMBEDDING VECTOR
                    emb = face_recognizer_result["output"]

                if frame_count <= 20 or time.time() - expression_task_last_run >= 300:  # 5 minutes
                    # Run expression task
                    expression_task_last_run = time.time()
                    loop = asyncio.get_event_loop()
                    expression_result = loop.run_until_complete(
                        asyncio.gather(
                            async_request(
                                "http://10.37.239.102:8090/predictions/FaceExpression",
                                data=post_image,
                            )
                        )
                    )
                    
                    expression = expression_result[0].json()['output']

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
                del frame
            else:
                print("Reconnecting to video...")
                cap.release()
                cap = connect_to_video(video_path)

    except Exception:
        traceback.print_exc()
        pass
    finally:
        cap.release()
        result.release()
