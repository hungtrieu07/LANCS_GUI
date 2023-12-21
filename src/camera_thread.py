import contextlib
import datetime
import logging
import os
import sys
import time

import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

ci_build_and_not_headless = False

with contextlib.suppress(Exception):
    from cv2.version import ci_build, headless
    ci_and_not_headless = ci_build and not headless
if sys.platform.startswith("linux") and ci_and_not_headless:
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")
if sys.platform.startswith("linux") and ci_and_not_headless:
    os.environ.pop("QT_QPA_FONTDIR")

class Worker(QtCore.QThread):
    send_frame = QtCore.pyqtSignal(np.ndarray)
    send_update_status = QtCore.pyqtSignal(str, bool)
    send_data_to_consumer = QtCore.pyqtSignal(dict, np.ndarray, np.ndarray)
    error_occurred = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, parent, *args, data: dict, mutex, wait_condition, **kwargs):
        QtCore.QThread.__init__(self, *args, **kwargs)
        self.p = parent
        self.data = data
        self.name = data["CAM NAME"]
        self.ip = data["IP"]
        self.zone = data["ZONE"]
        self.coord = np.array(data["COORD"])
        self.index = data["INDEX"]
        
        self._interupted = False
        self.black_frame = np.zeros((480, 640, 3), np.uint8)
        self.violation_frame = None
        self.pause = False
        self.mutex = mutex
        self.wait_condition = wait_condition

    def reinit_params(self, data: dict):
        self.name = data["CAM NAME"]
        self.ip = data["IP"]
        self.zone = data["ZONE"]
        self.coord = np.array(data["COORD"])

    def interupted(self):
        self._interupted = True

    def run(self):
        self._interupted = False

        try:
            cap = cv2.VideoCapture(self.ip)
            if not cap.isOpened():
                cap.release()
                self.error_occurred.emit(f"Camera {self.name} không thể mở!")
                return
        except Exception as e:
            cap.release()
            self.error_occurred.emit(f"Có lỗi xảy ra: {str(e)}")
            self.finished.emit()
        finally:
            self.send_update_status.emit(self.name, cap.isOpened())
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.coord *= np.array([width, height])
            self.coord = self.coord.reshape((-1, 1, 2))

            while True:
                has, img = cap.read()
                if not has:
                    break

                if self._interupted: 
                    break
                
                self.violation_frame = img.copy()
                
                current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                text = f"{self.name} {self.zone} {current_time}"
                cv2.putText(img , text, (50, 50), fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=1, color=(255, 0, 0), thickness=2)
                
                pts = np.array(self.coord, dtype=np.int32)
                frame = cv2.polylines(img, [pts], True, (0, 255, 0), 2)
                
                mask = np.zeros_like(img)
                cv2.fillPoly(mask, [pts], (255, 255, 255))
                img = cv2.bitwise_and(img, mask)
                
                if not self.pause:
                    self.mutex.lock()
                    self.send_frame.emit(frame)  # Send the last frame if interrupted
                    self.wait_condition.wait(self.mutex, 80)
                    self.mutex.unlock()
                    last_frame = frame 
                self.send_data_to_consumer.emit(self.data, img, self.violation_frame)

                # self.spin(0.08)
                
            cap.release()
            self._interupted = True
            self.send_update_status.emit(self.name, False)
            self.send_frame.emit(last_frame)
            self.send_data_to_consumer.emit(self.data, self.black_frame, self.black_frame)
            
            if self._interupted:
                self.reconnect()
            
            self.finished.emit()
            
    def reconnect(self):
        while True:
            try:
                cap = cv2.VideoCapture(self.ip)
                
                if cap.isOpened():
                    self.coord = np.array(self.data["COORD"])
                    self.send_update_status.emit(self.name, True)
                    self._interupted = False
                    self.run()  # Restart the run loop
                    break
                    
            except Exception as e:
                QtWidgets.QMessageBox.critical(self.p, "ERROR", "Có lỗi xảy ra: " + str(e))
                self.send_update_status.emit(self.name, False)
                self.send_frame.emit(self.black_frame)
                self.send_data_to_consumer.emit(self.data, self.black_frame, self.black_frame)
                self.finished.emit()
            
    def handle_stop(self, state: bool):
        self.pause = state

class CameraWidget(QtWidgets.QWidget):
    send_camera_frame = QtCore.pyqtSignal(str, np.ndarray)
    send_camera_status = QtCore.pyqtSignal(str, bool)

    def __init__(self, parent, *args, data, worker: Worker, **kwargs):
        super(CameraWidget, self).__init__(*args, **kwargs)
        self.p = parent
        self.vlayout = QtWidgets.QVBoxLayout()
        self.obj_name = data["CAM NAME"]
        self.index = data["INDEX"]
        self.camera_status = False
        self.worker = worker

        self.worker.send_frame.connect(self.update_frame, type=QtCore.Qt.QueuedConnection)
        self.worker.send_update_status.connect(self.update_status)
        self.worker.error_occurred.connect(self.handle_error)

        self.CamLabel = QtWidgets.QLabel()
        self.CamLabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.CamLabel.setScaledContents(True)
        self.setObjectName(self.obj_name)

        self.CamNameLabel = QtWidgets.QLabel()
        self.CamNameLabel.setText(f"{self.obj_name}")

        self.vlayout.addWidget(self.CamNameLabel)
        self.vlayout.addWidget(self.CamLabel)
        self.vlayout.setStretch(0, 0)
        self.vlayout.setStretch(1, 10)
        self.vlayout.setSpacing(0)

        self.setMinimumSize(QtCore.QSize(480, 270))
        self.setLayout(self.vlayout)
    
    def start(self):
        self.worker.start()
    
    def isRunning(self) -> bool:
        return self.worker.isRunning()
    
    def taskStop(self) -> None:
        self.worker.interupted()
        self.worker.quit()
        # self.worker.deleteLater()
        
    def handle_stop(self, state: bool):
        self.worker.handle_stop(state)
        
    def convert_cv_qt(self, cv_img: np.ndarray) -> QtGui.QPixmap:
        """Convert from an numpy array to QPixmap"""
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        p = QtGui.QImage(cv_img.data, w, h, bytes_per_line, QtGui.QImage.Format_BGR888)
        p = p.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        return QtGui.QPixmap.fromImage(p)
    
    def handle_error(self, error_message):
        QtWidgets.QMessageBox.critical(self, "ERROR", error_message)

    @QtCore.pyqtSlot(str, bool)
    def update_status(self, cam_name: str, status: bool):
        self.send_camera_status.emit(cam_name, status)

    @QtCore.pyqtSlot(np.ndarray)
    def update_frame(self, frame: np.ndarray):
        pixmap = self.convert_cv_qt(frame)
        self.CamLabel.setPixmap(pixmap)
