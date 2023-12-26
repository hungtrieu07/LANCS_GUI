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
        
        self.reset_interval = 60
        self.last_reset_time = None
        self.merged_data = {}
    
    def run(self) -> None:
        self.last_reset_time = int(time.time())
        
        while self._is_running:
            try:                
                frame = self.frame.copy()
                violation = self.violation_image.copy()
                coord = np.array(self.data["COORD"])
                coord *= np.array([frame.shape[1], frame.shape[0]])
                coord = coord.reshape((-1, 1, 2))
                pts = np.array(coord, dtype=np.int32)
                lst = [tuple(coord[0]) for coord in pts]
                
                self.ai.do_object_detection(frame, violation, self.data["ZONE"], self.data["INDEX"], lst)
                del frame, violation

            except Exception:
                # traceback.print_exc()
                pass
            
            self.mutex.lock()
            self.wait_condition.wait(self.mutex, 50)
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