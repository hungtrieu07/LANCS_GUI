import json
import time
from datetime import datetime
import traceback

import numpy as np
import pymongo
from PyQt5 import QtCore, QtWidgets

from src.ai_module import AI
from ui.ui_mainwindow import Ui_MainWindow

merged_json = {}

class Consumer(QtCore.QThread):
    active_instance = []
    finished = QtCore.pyqtSignal()
    
    def __init__(self, parent: QtWidgets.QMainWindow, mutex, wait_condition):
        super().__init__(parent)
        self.p: QtWidgets.QMainWindow = parent
        self.ui: Ui_MainWindow = parent.ui
        self._is_running: bool = True
        self.ai = AI(self.p)
        self.data = None
        self.frame = None
        self.violation_image = None
        self.mutex = mutex
        self.wait_condition = wait_condition
        
        Consumer.active_instance.append(self)
        self.reset_interval = 60
        self.last_reset_time = None
        self.merged_data = {}
        
        self.db = parent.db
        self.vehicle_database = self.db["vehicles"]
        
    def time_difference_less_than_60_seconds(doc1, doc2):
        # Extract the 'create_time' field from both documents
        time1 = datetime.strptime(doc1['create_time'], '%Y-%m-%dT%H:%M:%S.%f')
        time2 = datetime.strptime(doc2['create_time'], '%Y-%m-%dT%H:%M:%S.%f')

        # Calculate the time difference in seconds
        time_difference = abs((time1 - time2).total_seconds())

        # Check if the time difference is less than 60 seconds
        return time_difference < 60
    
    def run(self) -> None:
        cam_threads = len(Consumer.active_instance)
        print(cam_threads)
        self.ai.reset_database(cam_threads)
        self.ai.reset_variable(cam_threads)
        self.last_reset_time = int(time.time())
        
        while self._is_running:
            try:
                cam_number = int(self.data["CAM_NUMBER"])
                
                frame = self.frame.copy()
                violation = self.violation_image.copy()
                coord = np.array(self.data["COORD"])
                coord *= np.array([frame.shape[1], frame.shape[0]])
                coord = coord.reshape((-1, 1, 2))
                pts = np.array(coord, dtype=np.int32)
                lst = [tuple(coord[0]) for coord in pts]
                
                last_document = self.vehicle_database.find_one({}, sort=[("create_time", pymongo.DESCENDING)])
                
                if last_document is not None:
                    time_from_database = int(datetime.fromisoformat(last_document["create_time"]).timestamp())
                else:
                    time_from_database = 0
                    last_document = {
                        "create_time": datetime.now().isoformat(timespec='milliseconds'),
                        "CAM": []
                    }
                    for cam_id in range(cam_number):
                        last_document["CAM"].append({
                            "CAM_ID": str(cam_id),
                            "CAR": 0,
                            "TRUCK": 0,
                            "BUS": 0,
                            "TRAILER": 0
                        })
                    self.ai.write_to_database(last_document)
                
                current_time = time.time()
                
                if current_time - self.last_reset_time > self.reset_interval and (int(datetime.now().timestamp()) - time_from_database) > self.reset_interval:
                    self.merge_data()
                    

                    for key, value in self.merged_data.items():
                        if key not in merged_json:
                            merged_json[key] = value['properties']
                        else:
                            merged_json[key].update(value['properties'])

                    counted_json = {}


                    for key, value in merged_json.items():
                        counted_json[key] = {
                            'bus': len(value['bus']),
                            'car': len(value['car']),
                            'trailer': len(value['trailer']),
                            'truck': len(value['truck'])
                        }

                    counted_json = json.dumps(counted_json, sort_keys=True)
                    counted_json = json.loads(counted_json)
                        
                    timestamp = datetime.now().isoformat(timespec='milliseconds')
                        
                    if len(counted_json.keys()) == cam_number:
                        counted_json["create_time"] = timestamp
                        
                        output_dict = {
                            "create_time": counted_json['create_time'],
                            "CAM": []
                        }
                            
                        for cam_id, cam_data in counted_json.items():
                            cam = {
                                "CAM_ID": cam_id,
                                "CAR": cam_data['car'],
                                "TRUCK": cam_data['truck'],
                                "BUS": cam_data['bus'],
                                "TRAILER": cam_data['trailer']
                            }
                            output_dict["CAM"].append(cam)
                            
                            time_from_dict = int(datetime.fromisoformat(output_dict["create_time"]).timestamp())
                        
                            if len(output_dict["CAM"]) == cam_number and time_from_dict - self.last_reset_time >= self.reset_interval:
                                try:
                                    result_dict = {
                                        'create_time': output_dict['create_time'],
                                        'CAM': []
                                    }
                                    print(output_dict)
                                    print(last_document)
                                    for current_cam, previous_cam in zip(output_dict['CAM'], last_document['CAM']):
                                        cam_id = current_cam['CAM_ID']
                                        cam_result = {'CAM_ID': cam_id}
                                        for vehicle_type in ['CAR', 'TRUCK', 'BUS', 'TRAILER']:
                                            current_count = current_cam[vehicle_type]
                                            previous_count = previous_cam[vehicle_type]
                                            change = abs(current_count - previous_count)
                                            cam_result[vehicle_type] = change
                                        result_dict['CAM'].append(cam_result)

                                    # print(result_dict)
                                    self.ai.write_to_database(result_dict)

                                except Exception:
                                    print(traceback.format_exc())
                                output_dict = {}
                                self.merged_data = {}
                                self.merged_json = {}
                                self.ai.reset_database(cam_number)
                                self.ai.reset_variable(cam_number)
                                self.last_reset_time = int(time.time())

                else:
                    # Initialize last_document with an empty document
                    last_document = {
                        "create_time": datetime.now().isoformat(timespec='milliseconds'),
                        "CAM": []
                    }
                    for cam_id in range(cam_number):
                        last_document["CAM"].append({
                            "CAM_ID": str(cam_id),
                            "CAR": 0,
                            "TRUCK": 0,
                            "BUS": 0,
                            "TRAILER": 0
                        })
                
                self.ai.do_object_detection(frame, violation, self.data["ZONE"], self.data["INDEX"], lst)

            except Exception as e:
                pass
            
            self.mutex.lock()
            self.wait_condition.wait(self.mutex, 80)
            self.mutex.unlock()
            
        self.finished.emit()

    def taskStop(self):
        self._is_running = False
        self.quit()

    # Slot to update data from producers
    @QtCore.pyqtSlot(dict, np.ndarray, np.ndarray)
    def update_data_to_buffer(self, data: dict, frame: np.ndarray, violation_image: np.ndarray):
        self.data = data
        self.frame = frame
        self.violation_image = violation_image

    def merge_data(self):
        cam_index = self.data["INDEX"]
        if cam_index not in self.merged_data:
            self.merged_data[cam_index] = {
                "properties": self.ai.camera_database.get(cam_index, {}).get("properties", {})
            }
        else:
            self.merged_data[cam_index]["properties"].update(self.ai.camera_database.get(cam_index, {}).get("properties", {}))

            # Find duplicate documents based on your criteria (time difference < 60 seconds)
            documents = list(self.vehicle_database.find())
            for i, doc1 in enumerate(documents):
                for doc2 in documents[i + 1:]:
                    if self.time_difference_less_than_60_seconds(doc1, doc2):
                        # Delete one of the duplicate documents
                        self.vehicle_database.delete_one({'_id': doc2['_id']})
            
            # Reset the last_reset_time to the current time
            self.last_reset_time = int(time.time())