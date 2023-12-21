import datetime
import json
import math
import os
import time
from io import BytesIO

import cv2
import numpy as np
import requests
from PIL import Image
from PyQt5 import QtCore, QtWidgets

from core.byte_tracker import BYTETracker
from core.lane_line_detector import calculate_distance
from core.track_abnormal import TrackAbnormal
from ui.ui_mainwindow import Ui_MainWindow

program_start_time = time.time()

MAX_FRAME = 3
MAX_VALUE_PER_LIST = 3

DISTANCE_CONST_COEFF = 0.3
VELOCITY_COEFF = 3.6

class AI(QtCore.QObject):
    def __init__(self, parent: QtWidgets.QMainWindow):
        super().__init__(parent)
        self.ui: Ui_MainWindow = parent.ui
        
        self.vehicle_database = parent.db["vehicles"]
        self.violation_database = parent.db["violation_vehicles"]

        self.track_abnormal = TrackAbnormal(max_dist=40)

        self.tracker = BYTETracker()
        self.test_size = (640, 640)
        self.direction_ids = {}
        self.start_point = {}
        self.check_point = {}
        self.MIN = 40
        self.current_direction_ids = {}
        
        self.delta = 0

        self.last_saved_time = time.time()

        self.left = {
            "bus": [],
            "car": [],
            "person": [],
            "trailer": [],
            "truck": [],
            "bike": [],
        }
        self.right = {
            "bus": [],
            "car": [],
            "person": [],
            "trailer": [],
            "truck": [],
            "bike": [],
        }
        self.CLASS_NAME = ["bus", "car", "trailer", "truck"]
        self.CLASS_NAME2 = ["bus", "car", "lane", "person", "trailer", "truck", "bike"]
        self.filter_class = [0, 1, 4, 5]
        self.camera_database = {}
        self.vehicle_each_lane = {}

    @QtCore.pyqtSlot(list)
    def recv_setting_data(self, setting_list: list):
        print(setting_list)

    def create_capture_folder():
        if not os.path.exists("./logs"):
            os.mkdir("./logs")

        folders = [
            "abnormal",
            "stopped",
            "overspeed",
            "opposite_direction",
            "person",
            "bike",
        ]

        for folder in folders:
            if not os.path.exists(f"./logs/{folder}"):
                os.mkdir(f"./logs/{folder}")

    create_capture_folder()

    def reset_variable(self, cam_num):
        for id in range(cam_num):
            self.vehicle_each_lane[id] = {
                "left_car": [],
                "left_bus": [],
                "left_trailer": [],
                "left_truck": [],
                "right_car": [],
                "right_bus": [],
                "right_trailer": [],
                "right_truck": [],
            }

    def reset_database(self, cam_num):
        for id in range(cam_num):
            self.camera_database[id] = {
                "properties": {
                    "bus": [],
                    "car": [],
                    "trailer": [],
                    "truck": [],
                }
            }

    def write_to_database(self, output_json):
        if os.path.exists("./logs") == False:
            os.mkdir("./logs")
        self.vehicle_database.insert_one(output_json)
        self.reset_database(len(output_json["CAM"]))
        self.reset_variable(len(output_json["CAM"]))
    
    def calculate_velocity(self, f, w, d):
        return float((w * d) / f)

    def convert_frame(self, frame):
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

    def calculate_lane(self, arg0, arg1):
        # Phương trình đường thẳng AB với A=p1_2 , B=p2_2
        x1, y1 = arg0
        x2, y2 = arg1
        a_AB = ((y1 - y2)) / (x1 - x2)
        b_AB = (y2 * x1 - y1 * x2) / (x1 - x2)
        y_M = max(y1, y2) * 0.6
        x_M = (y_M - b_AB) / a_AB
        return [int(x_M), int(y_M)]

    def calculate_2_point(self, pts):
        arr_point = pts

        point_1 = [
            int((arr_point[0][0] + arr_point[1][0]) / 2),
            int((arr_point[0][1] + arr_point[1][1]) / 2),
        ]
        point_2 = [
            int((arr_point[2][0] + arr_point[3][0]) / 2),
            int((arr_point[2][1] + arr_point[3][1]) / 2),
        ]

        return [point_1, point_2]

    def get_area_detect(self, frame, points):
        mask = np.zeros(frame.shape[:2], np.uint8)
        cv2.drawContours(mask, [points], -1, (255, 255, 255), -1, cv2.LINE_AA)
        return cv2.bitwise_and(frame, frame, mask=mask)

    # @profile
    def non_familiar_object(self, frame, violation_frame, label_id, location, id_cam, pts, bbox, delta=30):
        self.location = location
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        img_croped = self.get_area_detect(blur, np.array(pts, np.int32))
        
        non_familiar_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        for box in bbox:
            box = list(map(int, box))
            img_vehicle = np.zeros(
                [box[3] - box[1] + delta, box[2] - box[0] + delta],
                dtype=np.uint8,
                order="C",
            )
            img_croped[box[1] : box[3] + delta, box[0] : box[2] + delta] = img_vehicle

            center = self.calculate_2_point(pts)
            canny = cv2.Canny(img_croped, 100, 300)
            contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

            bboxes = []

            for index, c in enumerate(contours):
                if len(c) > 20 and len(c) < 100:
                    dist = calculate_distance(c[0][0], np.array(center))
                    x, y, w, h = cv2.boundingRect(c)
                    if dist > 60 and dist < 150:
                        cv2.drawContours(frame, c, index, (0, 255, 0), 3)
                        # ADD: add tọa độ bbox vào list trên
                        bboxes.append([x, y, w, h])

            state = self.track_abnormal.update(bboxes)

            # Nếu state là false, tức là object ở frame trước ko giống frame hiện tại
            # thì ghi frame
            if not state and 3 not in label_id:
                # Ghi frame
                filename = f"./logs/abnormal/{non_familiar_time}.jpg"
                cv2.imwrite(filename, violation_frame)

                data = {
                    "type": "Vật thể lạ",  # loại vi phạm
                    "location": self.location,  # địa điểm vi phạm
                    "path": filename,  # đường dẫn file ảnh vi phạm lưu trên local
                    "time": datetime.datetime.now().isoformat(
                        timespec="milliseconds"
                    ),  # thời gian vi phạm
                }
                result = json.dumps(data)
                result = json.loads(result)
                self.violation_database.insert_one(result)

    # @profile
    def detect_person_and_bike(self, violation_frame, coordinates, location, bboxes, label_id, online_ids, id_cam):
        self.location = location
        update_point = {}
        label_map = {
            0: "bus",
            1: "car",
            2: "lane",
            3: "person",
            4: "trailer",
            5: "truck",
            6: "bike"
        }
        
        for label, tid, box in zip(label_id, online_ids, bboxes):
            label_name = label_map[int(label)]

            if label_name == "bike":
                filename = f"./logs/bike/bike_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.jpg"
                cv2.imwrite(filename, violation_frame)

                data = {
                    "type": "Xe máy",  # loại vi phạm
                    "location": self.location,  # địa điểm vi phạm
                    "path": filename,  # đường dẫn file ảnh vi phạm lưu trên local
                    "time": datetime.datetime.now().isoformat(
                        timespec="milliseconds"
                    ),  # thời gian vi phạm
                }
                result = json.dumps(data)
                result = json.loads(result)
                self.violation_database.insert_one(result)
                
            elif label_name == "person":
                filename = f"./logs/person/person_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.jpg"
                cv2.imwrite(filename, violation_frame)

                data = {
                    "type": "Người đi bộ",  # loại vi phạm
                    "location": self.location,  # địa điểm vi phạm
                    "path": filename,  # đường dẫn file ảnh vi phạm lưu trên local
                    "time": datetime.datetime.now().isoformat(
                        timespec="milliseconds"
                    ),  # thời gian vi phạm
                }
                result = json.dumps(data)
                result = json.loads(result)
                self.violation_database.insert_one(result)
            else:
                if label_name not in self.camera_database[id_cam]["properties"]:
                    # Initialize the array if it doesn't exist
                    self.camera_database[id_cam]["properties"][label_name] = []
                if (
                    isinstance(
                        self.camera_database[id_cam]["properties"][label_name],
                        list,
                    )
                    and tid
                    not in self.camera_database[id_cam]["properties"][label_name]
                ):
                    
                    self.camera_database[id_cam]["properties"][label_name].append(
                        tid
                    )  # Append to the array if it does exist

            mid_point = (
                int((box[0] + box[2]) / 2),
                int((box[1] + box[3]) / 2),
            )
            if str(tid) not in self.start_point.keys():
                self.start_point[str(tid)] = [
                    mid_point,
                    time.perf_counter(),
                ]
            update_point[str(tid)] = [mid_point, time.perf_counter()]

            arr_point = coordinates
            arr_point2 = coordinates

            _, _, p3_1, p4_1 = arr_point
            p1_2, p2_2, p3_2, p4_2 = arr_point2

            K = self.calculate_lane(p1_2, p2_2)
            N = self.calculate_lane(p3_2, p4_2)
            area_Goal = np.array([K, N, p3_1, p4_1], np.int32)

            point_1 = [
                int((arr_point[0][0] + arr_point[1][0]) / 2),
                int((arr_point[0][1] + arr_point[1][1]) / 2),
            ]
            point_2 = [
                int((arr_point[2][0] + arr_point[3][0]) / 2),
                int((arr_point[2][1] + arr_point[3][1]) / 2),
            ]

            if mid_point[0] < max(point_1[0], point_2[0]):
                lane_prefix = "left"
                if str(tid) not in self.left[self.CLASS_NAME2[int(label)]]:
                    self.left[self.CLASS_NAME2[int(label)]].append(str(tid))
            else:
                lane_prefix = "right"
                if str(tid) not in self.right[self.CLASS_NAME2[int(label)]]:
                    self.right[self.CLASS_NAME2[int(label)]].append(str(tid))
                    
            if label_name != "person":
                vehicle_key = f"{lane_prefix}_{label_name}"
                
                if (
                    isinstance(
                        self.vehicle_each_lane[id_cam][vehicle_key],
                        list,
                    )
                    and tid not in self.vehicle_each_lane[id_cam][vehicle_key]
                ):
                    self.vehicle_each_lane[id_cam][vehicle_key].append(
                        tid
                    )  # Append to the array if it does exist

            vehicle_key_sort = sorted(self.vehicle_each_lane.keys())

            self.vehicle_each_lane = {
                i: self.vehicle_each_lane[i] for i in vehicle_key_sort
            }

            mid_point_t = self.start_point[str(tid)][0]
            t = self.start_point[str(tid)][1]
            mid_point_t_1 = update_point[str(tid)][0]

            t_1 = update_point[str(tid)][1] - t

            distance_pixel = math.hypot(
                abs(mid_point_t[0] - mid_point_t_1[0]),
                abs(mid_point_t[1] - mid_point_t_1[1]),
            )
            
            if distance_pixel < self.MIN and t_1 > 5 and label_name != "person":
                filename = f"./logs/stopped/{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.jpg"
                cv2.imwrite(filename, violation_frame)
                # cv2.imwrite("E:/VDS-GUI/test/stop.jpg", frame)
                data = {
                    "type": "Dừng đỗ xe",  # loại vi phạm
                    "location": self.location,  # địa điểm vi phạm
                    "path": filename,  # đường dẫn file ảnh vi phạm lưu trên local
                    "time": datetime.datetime.now().isoformat(
                        timespec="milliseconds"
                    ),  # thời gian vi phạm
                }
                result = json.dumps(data)
                result = json.loads(result)
                self.violation_database.insert_one(result)
            else:
                pass

            results_goal = cv2.pointPolygonTest(area_Goal, mid_point, False)

            if results_goal >= 0:
                mid_point_prev = self.start_point[str(tid)][0]
                start_time = self.start_point[str(tid)][1]
                distance_pixel = math.hypot(
                    abs(mid_point[0] - mid_point_prev[0]),
                    abs(mid_point[1] - mid_point_prev[1]),
                )
                end_time = update_point[str(tid)][1] - start_time
                
                focal_length_mm = 50.0
                sensor_size_mm = 24.0

                velocity = ((sensor_size_mm * distance_pixel) / (focal_length_mm * end_time)) * VELOCITY_COEFF

                if velocity >= 120:
                    velocity_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                    filename = f"./logs/overspeed/{velocity_time}.jpg"
                    cv2.imwrite(filename, violation_frame)
                    
                    data = {
                        "type": "Quá tốc độ",  # loại vi phạm
                        "speed": int(velocity),
                        "location": self.location,  # địa điểm vi phạm
                        "path": filename,  # đường dẫn file ảnh vi phạm lưu trên local
                        "time": datetime.datetime.now().isoformat(
                            timespec="milliseconds"
                        ),  # thời gian vi phạm
                    }
                    result = json.dumps(data)
                    result = json.loads(result)
                    self.violation_database.insert_one(result)

    # DIRECTION
    # @profile
    def opposite_direction(self, violation_frame, box_int, online_ids, label_id):
        if box_int is not None:
            for onl_id, box in zip(online_ids, box_int):
                if onl_id not in self.current_direction_ids:
                    self.current_direction_ids[onl_id] = []
                if len(self.current_direction_ids[onl_id]) < MAX_VALUE_PER_LIST:
                    mid_point = (int(box[1]) + int(box[3])) // 2
                    self.current_direction_ids[onl_id].append(mid_point)

        if len(self.direction_ids) < MAX_FRAME:
            for onl_id, mid_points in self.current_direction_ids.items():
                if onl_id not in self.direction_ids:
                    self.direction_ids[onl_id] = []
                self.direction_ids[onl_id] += mid_points
                if len(self.direction_ids[onl_id]) > MAX_VALUE_PER_LIST:
                    self.direction_ids[onl_id] = [
                        self.direction_ids[onl_id][-MAX_VALUE_PER_LIST:]
                    ]
        else:
            self.direction_ids = self.current_direction_ids

            for onl_id, mid_points in self.direction_ids.items():
                if len(mid_points) == MAX_VALUE_PER_LIST:
                    if mid_points == sorted(mid_points):
                        continue
                    if '3' not in label_id:
                        opposite_direction_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                        filename = f"./logs/opposite_direction/{opposite_direction_time}.jpg"
                        cv2.imwrite(filename, violation_frame)
                        
                        data = {
                        "type": "Ngược chiều",  # loại vi phạm
                        "location": self.location,  # địa điểm vi phạm
                        "path": filename,  # đường dẫn file ảnh vi phạm lưu trên local
                        "time": datetime.datetime.now().isoformat(
                            timespec="milliseconds"
                            ),  # thời gian vi phạm
                        }
                        result = json.dumps(data)
                        result = json.loads(result)
                        self.violation_database.insert_one(result)
                    self.direction_ids[onl_id] = []

    # @profile
    def do_object_detection(self, frame: np.ndarray, violation_frame: np.ndarray, location: str, id_cam: str, coordinates: list):
        
        image_data = self.convert_frame(frame)
        server_IP = str(self.ui.comboBoxServerIP.currentText())

        vehicle_URL = f"http://{server_IP}:8080/predictions/VehicleDetection"
        vehicle_response = requests.post(vehicle_URL, data=image_data)
        
        if vehicle_response.status_code == 200:
            vehicle_data = vehicle_response.json()

            output = vehicle_data[0]["output"]
            label_id = vehicle_data[0]["label"]
            bbox = vehicle_data[0]["bbox"]
            request_number = vehicle_data[0]["request_number"]
            print(request_number)
            
            online_tlwhs = []
            online_ids = []
            online_scores = []
            box_int = []
            
            result = np.array(output)

            if result is not None:
                online_targets = self.tracker.update(result, [frame.shape[0], frame.shape[1]], self.test_size, self.filter_class)

                for t, box in zip(online_targets, bbox):
                    tlwh = t.tlwh
                    tid = t.track_id
                    online_tlwhs.append(tlwh)
                    online_ids.append(tid)
                    
                    online_scores.append(t.score)
                    _box = list(map(int, box))
                    box_int.append(_box)

                self.detect_person_and_bike(violation_frame, coordinates, location, bbox, label_id, online_ids, id_cam)
                self.non_familiar_object(frame, violation_frame, label_id, location, id_cam, coordinates, bbox, delta=40)
                self.opposite_direction(violation_frame, box_int, online_ids, label_id)
                
                # print(self.camera_database)
                