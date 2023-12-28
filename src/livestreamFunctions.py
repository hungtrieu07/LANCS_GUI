from __future__ import annotations

import abc

from PyQt5 import QtCore, QtWidgets

from src.camera_thread import CameraWidget, Worker
from src.consumer_thread import Consumer
from ui.ui_mainwindow import Ui_MainWindow


class GridStyle():
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, layout: QtWidgets.QGridLayout, num_col = 3):
        self.num_col = num_col
        self.layout = layout
        self.track_first_widget = None
        
    def setLayout(self, layout: QtWidgets.QGridLayout):
        self.layout = layout
    
    def setNumColumn(self, num_col: int):
        self.num_col = num_col
    
    @abc.abstractmethod
    def addWidget(self, widget: QtWidgets.QWidget, index: int):
        ...
    
    @abc.abstractmethod
    def filterWidget(self, ignore_obj_name: str, show: bool):
        ...
    
class NormalGrid(GridStyle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def addWidget(self, widget: QtWidgets.QWidget, index: int):
        self.layout.addWidget(widget, index//self.num_col, index%self.num_col)
    
    def filterWidget(self, cam_managers: dict, ignore_obj_name: str, show: bool):
        for obj_name, mng in cam_managers.items():            
            if obj_name == ignore_obj_name:
                continue
            if show:
                mng["cameraWidget"].show()
            else:
                mng["cameraWidget"].hide()

class CompactGrid(GridStyle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
class CompactGrid(GridStyle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def addWidget(self, camWidget: QtWidgets.QWidget, index: int):
        num_span = self.num_col - 1

        if index < 3:
            if index == 0:
                self.layout.addWidget(camWidget, 0, 0, num_span, num_span)
            elif index == 1:
                self.layout.addWidget(camWidget, 0, num_span, 1, 1)
            elif index == 2:
                self.layout.addWidget(camWidget, 1, num_span, 1, 1)      
        else:
            self.layout.addWidget(camWidget, (index - 3) // self.num_col + num_span, (index - 3) % self.num_col)

    def filterWidget(self, cam_managers: dict, ignore_obj_name: str, show: bool):
        for obj_name, mng in cam_managers.items():
            if self.track_first_widget is None:
                self.track_first_widget = self.layout.itemAt(0).widget()
            
            if obj_name == ignore_obj_name:
                continue
            if show:
                self.setWidgetSpan(self.track_first_widget, self.num_col - 1, self.num_col - 1)
                mng["cameraWidget"].show()
            else:
                self.setWidgetSpan(self.track_first_widget, 1, 1)
                mng["cameraWidget"].hide()

    def setWidgetSpan(self, widget, rowspan=1, colspan=1):
        index = self.layout.indexOf(widget)
        row, col = self.layout.getItemPosition(index)[:2]
        self.layout.addWidget(widget, row, col, rowspan, colspan)

class LiveStreamGrid(QtWidgets.QWidget):
    send_camera_update_status = QtCore.pyqtSignal(str, bool)
    
    def __init__(self, parent: QtWidgets.QMainWindow):
        super().__init__(parent)
        self.p: QtWidgets.QMainWindow = parent
        self.ui: Ui_MainWindow = parent.ui
                
        self.cam_managers = {}
        
        self.grid_style = NormalGrid(self.ui.LiveStreamGrid, 3)

        self.mutex = QtCore.QMutex()
        self.wait_condition = QtCore.QWaitCondition()
        
        self.mutex2 = QtCore.QMutex()
        self.wait_condition2 = QtCore.QWaitCondition()
        # self.consumer = Consumer(parent=self.p)
        

    def setGridStyle(self, grid_style: GridStyle):
        self.grid_style = grid_style

    def initialize_grid(self, camera_datas):
        for data in camera_datas:
            if data["CAM NAME"] in self.cam_managers:
                cameraWidget: CameraWidget = self.cam_managers[data["CAM NAME"]]["cameraWidget"]
                consumer: Consumer = self.cam_managers[data["CAM NAME"]]["consumer"]
                if cameraWidget.isRunning():
                    cameraWidget.taskStop()
                if consumer.isRunning():
                    consumer.taskStop()
                cameraWidget.worker.reinit_params(data)
            else:
                worker = Worker(self, data=data, mutex=self.mutex,  wait_condition=self.wait_condition)
                cameraWidget = CameraWidget(parent=self.p, data=data, worker=worker)
                consumer = Consumer(self.p, self.mutex2, self.wait_condition2)
                cameraWidget.send_camera_status.connect(self.recv_update_status_from_camera)
                cameraWidget.worker.send_data_to_consumer.connect(consumer.update_data_to_buffer, type=QtCore.Qt.QueuedConnection)
                # consumer.send_buffer_signal_state.connect(cameraWidget.worker.update_buffer_status)
                cameraWidget.installEventFilter(self)
                cameraWidget.setObjectName(cameraWidget.obj_name)

                idx = int(data["INDEX"])
                # self.ui.LiveStreamGrid.addWidget(cameraWidget, idx//3, idx%3)
                self.grid_style.addWidget(cameraWidget, index=idx)

                self.cam_managers[cameraWidget.obj_name] = {"cameraWidget": cameraWidget, "is_window_maximized": False, "consumer": consumer}

            cameraWidget.start()
            consumer.start()
        # if not self.consumer.isRunning():
        #     self.consumer.start()


    @QtCore.pyqtSlot(str, bool)
    def recv_update_status_from_camera(self, cam_name: str, status: bool):
        self.send_camera_update_status.emit(cam_name, status)

    def remove_camera(self, cam_name_lst: list[str]):
        """ receive a list of deleted camera name from setup table and remove those cameras"""  
        for cam_name in cam_name_lst:
            if cam_name not in self.cam_managers: continue
            cameraWidget: CameraWidget = self.cam_managers[cam_name]["cameraWidget"]
            cameraWidget.worker.send_frame.disconnect()
            cameraWidget.worker.send_data_to_consumer.disconnect()
            cameraWidget.worker.send_update_status.disconnect()
            cameraWidget.send_camera_status.disconnect()
            cameraWidget.taskStop()
            
            consumer: Consumer = self.cam_managers[cam_name]["consumer"]
            consumer.taskStop()
            consumer.deleteLater()

            self.ui.LiveStreamGrid.removeWidget(cameraWidget)
            cameraWidget.deleteLater()
            self.cam_managers.pop(cam_name)
        # self.reinit_grid()
        self.grid_style.track_first_widget = None

    def reinit_grid(self):
        for index, mng in enumerate(self.cam_managers.values()):
            cameraWidget: CameraWidget = mng["cameraWidget"]
            self.ui.LiveStreamGrid.removeWidget(cameraWidget)
            self.grid_style.addWidget(cameraWidget, index=cameraWidget.index)

        self.first_cameraWidget = None

    def eventFilter(self, source, event) -> bool:
        if event.type() != QtCore.QEvent.MouseButtonDblClick:
            return super().eventFilter(source, event)
        obj_name_clicked = source.objectName()
        if not self.cam_managers[obj_name_clicked]['is_window_maximized']:
            self.grid_style.filterWidget(cam_managers=self.cam_managers,
                                        ignore_obj_name=obj_name_clicked, 
                                        show=False)
            self.cam_managers[obj_name_clicked]['is_window_maximized'] = True
            self.cam_managers[obj_name_clicked]["cameraWidget"].worker.pause = True
            self.cam_managers[obj_name_clicked]["consumer"].send_predicted_frame.connect(self.cam_managers[obj_name_clicked]["cameraWidget"].update_frame)
        else:
            self.grid_style.filterWidget(cam_managers=self.cam_managers,
                                        ignore_obj_name=obj_name_clicked, 
                                        show=True)
            self.cam_managers[obj_name_clicked]['is_window_maximized'] = False
            self.cam_managers[obj_name_clicked]["consumer"].send_predicted_frame.disconnect()
            self.cam_managers[obj_name_clicked]["cameraWidget"].worker.pause = False

        return True

class LiveStreamFunctions(LiveStreamGrid):
    def __init__(self, parent):
        super().__init__(parent)
        self.p = parent
        
    def remove_all_cameras(self):
        for name, mng in self.cam_managers.items():
            if mng["cameraWidget"].isRunning():
                mng["cameraWidget"].taskStop()
            if mng["consumer"].isRunning():
                mng["consumer"].taskStop()


    def toggleCompactMode(self, state: bool):
        if state:
            self.setGridStyle(CompactGrid(layout=self.ui.LiveStreamGrid, num_col = 3))
        else:
            self.setGridStyle(NormalGrid(layout=self.ui.LiveStreamGrid, num_col = 3))

        self.reinit_grid()
        
    def on_stopButtonClicked(self):
        try:
            for index, mng in enumerate(self.cam_managers.values()):
                cameraWidget: CameraWidget = mng["cameraWidget"]
                cameraWidget.handle_stop(True)
                # cameraWidget.worker.send_data_to_consumer.disconnect()
        except Exception:
            QtWidgets.QMessageBox.critical(self.p, "LỖI!", "Không có camera trên màn hình live. Không thể dừng.")

                
    def on_playButtonClicked(self):
        for index, mng in enumerate(self.cam_managers.values()):
            cameraWidget: CameraWidget = mng["cameraWidget"]
            cameraWidget.handle_stop(False)
    

    @QtCore.pyqtSlot(list)
    def recv_table_data(self, recv_data: list):
        self.initialize_grid(recv_data)
    
    @QtCore.pyqtSlot(list)
    def recv_remove_cam_signal(self, remove_cam_list: list):
        self.remove_camera(remove_cam_list)
        
    
    