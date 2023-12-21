import cv2
import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtWidgets

from src.pandasmodel import PandasModel
from src.roi_hooks import ROI_Hook
from src.roi_selector import CURSOR_DEFAULT, ROISelector, override_cursor
from ui.ui_selectROIdialog import Ui_SelectROIDialog

# detector = Detector(model='src/yolov5n_lane_0321_2.onnx')

class SelectROIDialog(QtWidgets.QDialog):
    send_coord = QtCore.pyqtSignal(str, list)
    send_is_close = QtCore.pyqtSignal()
    
    def __init__(self, data: pd.DataFrame, parent=None, server_ip_combo=None) -> None:
        super().__init__(parent)
        self.ui = Ui_SelectROIDialog()
        self.ui.setupUi(self)
        
        self.server_ip_combo = server_ip_combo
        
        self.model = PandasModel(data, editable=False)
        
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.horizontalHeader().setSectionsMovable(True)
        self.ui.tableView.horizontalHeader().setVisible(True)
        self.ui.tableView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        # self.ui.tableView.setWordWrap(True)
        self.ui.tableView.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.ui.tableView.verticalHeader().setVisible(False)
        self.ui.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.ui.tableView.selectionModel().selectionChanged.connect(self.on_RowSelected)
        self.ui.tableView.setColumnHidden(2, True)
        self.ui.tableView.setColumnHidden(4, True)
                
        self.ui.btnFinish.clicked.connect(self.on_FinishClick)
        self.ui.btnNext.clicked.connect(self.on_NextClick)
        self.ui.btnBack.clicked.connect(self.on_BackClick)
        self.ui.btnClear.clicked.connect(self.on_ClearClick)
        
        for _ in range(self.model.rowCount()):
            roi_hook = ROI_Hook(self.server_ip_combo)
            roi_selector = ROISelector(parent=parent, hooks=[roi_hook])
            roi_selector.get_hook_signal("ROI_Hook", "send_point_coord").connect(self.append_selected_points)
            self.ui.stackROILabel.addWidget(roi_selector)
        
        self.ui.tableView.selectRow(0)
        self.ui.stackROILabel.setCurrentIndex(0)
        self.current_roi_selector: ROISelector = self.ui.stackROILabel.currentWidget()
        self.setMinimumSize(800, 600)
        self.showMaximized()

        self.ui.retranslateUi(self)
    
    def on_ClearClick(self):
        self.current_roi_selector.clear()

    def on_FinishClick(self):
        self.send_is_close.emit()
        self.deleteLater()
        override_cursor(CURSOR_DEFAULT)

    def on_NextClick(self):
        curr = self.ui.tableView.selectionModel().currentIndex().row()
        if curr >= self.model.rowCount() - 1:
            self.ui.tableView.selectRow(self.model.rowCount() - 1)
        else:
            self.ui.tableView.selectRow(curr + 1)

    def on_BackClick(self):
        curr = self.ui.tableView.selectionModel().currentIndex().row()
        if curr <= 0:
            self.ui.tableView.selectRow(0)
        else:
            self.ui.tableView.selectRow(curr - 1)

    @QtCore.pyqtSlot(np.ndarray, list)
    def append_selected_points(self, frame: np.ndarray, points: list):
        coord_idx = self.model.dataframe.columns.get_indexer(["COORD"])[0]
        cam_name = self.model.dataframe.loc[self.ui.stackROILabel.currentIndex(), "CAM NAME"]
        self.model.update_data(self.ui.stackROILabel.currentIndex(), coord_idx, points)
        self.send_coord.emit(cam_name, points)

    def on_RowSelected(self, selected, deselected):
        pos = self.ui.tableView.selectionModel().currentIndex()
        current_cam_id = pos.row()
        ip = self.model.dataframe.loc[current_cam_id, "IP"]
        coord = self.model.dataframe.loc[current_cam_id, "COORD"]
        cap = cv2.VideoCapture(ip)
        if cap.isOpened():
            _, frame = cap.read()
            self.ui.stackROILabel.setCurrentIndex(current_cam_id)
            self.current_roi_selector: ROISelector = self.ui.stackROILabel.currentWidget()
            # if self.lst_lane:
            #     self.current_roi_selector.append_hook(Lane_Hook())
            # print("coord at cam {}: ".format(pos), coord)
            self.current_roi_selector.load_data(frame, coord, "ROI_Hook")
            self.current_roi_selector.get_hook_signal("ROI_Hook", "send_point_coord").connect(self.append_selected_points)

            # self.current_roi_selector.finish_select_point.connect(self.append_selected_points)
            cap.release()
        else:
            QtWidgets.QMessageBox.information(self,
                        "ERROR", # title
                        "IP \"%s\" is invalid.\nPlease check again" % ip, # content
                        QtWidgets.QMessageBox.Ok)
            return
            
    def closeEvent(self, event) -> None:
        ret = QtWidgets.QMessageBox.information(self,
            "Quit CCTV", # title
            "Are you sure to Quit?", # content
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if ret == QtWidgets.QMessageBox.Yes:
            self.send_is_close.emit()
            override_cursor(CURSOR_DEFAULT)
            self.ui.stackROILabel.deleteLater()
            event.accept()
        else:
            event.ignore()
        