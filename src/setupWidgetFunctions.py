from __future__ import annotations

import re

import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets

from src.pandasmodel import (SettingTableDelegate, SettingTableModel,
                             SetupTableDelegate, SetupTableModel)
from src.select_roi_dialog import SelectROIDialog
from ui.ui_mainwindow import Ui_MainWindow


def pd_to_list(df) -> list:
    results = list()
    camera_stream = df.shape[0]

    df = df[df["CAM NAME"].notnull() & df["IP"].notnull()]

    df = df[df["COORD"].notnull() & df["COORD"].astype(bool)]
    for _, row in df.iterrows():
        index = int(re.findall(r"\d+", row["CAM NAME"])[-1])
        results.append(
            {
                "INDEX": index - 1,
                "CAM NAME": row["CAM NAME"],
                "IP": row["IP"],
                "ZONE": row["ZONE"],
                "COORD": row["COORD"],
                "STATUS": row["STATUS"],
                "CAM_NUMBER": camera_stream,
            }
        )

    return results


def pd_to_list_for_setting(df) -> list:
    results = list()
    camera_stream = df.shape[0]
    if camera_stream > 0:
        df = df[df["CAM NAME"].notnull()]
        for _, row in df.iterrows():
            results.append(
                {
                    "CAM NAME": row["CAM NAME"],
                    "HEIGHT": 10,
                    "LANE_NUMBER": 2,
                    "FOCAL_LENGTH": 0.3
                }
            )

    return results

class SetupTable(QtWidgets.QWidget):
    delete_rows_requested = QtCore.pyqtSignal(list)
    delete_cameras_requested = QtCore.pyqtSignal(list)
    send_remove_cam_signal = QtCore.pyqtSignal(list)
    send_table_data = QtCore.pyqtSignal(list)
    send_table_data_to_AI = QtCore.pyqtSignal(list)
    send_cam_names = QtCore.pyqtSignal(list, int, float, float)

    def __init__(self, parent):
        super().__init__(parent)
        self.ui: Ui_MainWindow = parent.ui
        self.p = parent

        self.new_row = pd.DataFrame(
            [[np.nan, np.nan, np.nan, [], "Offline"]],
            columns=["CAM NAME", "IP", "ZONE", "COORD", "STATUS"],
        )

        self.df = pd.DataFrame(
            [], columns=["CAM NAME", "IP", "ZONE", "COORD", "STATUS"]
        )
        self.df["COORD"] = self.df["COORD"].astype("object")

        self.setupModel = SetupTableModel(self.df, editable=True, exclude_col=[3, 4])
        self.setupDelegate = SetupTableDelegate()

        self.ui.setupTableView.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.ui.setupTableView.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )

        self.sort_proxy_model = QtCore.QSortFilterProxyModel()
        self.sort_proxy_model.setSourceModel(self.setupModel)
        self.ui.setupTableView.setSortingEnabled(False)
        self.ui.setupTableView.setModel(self.sort_proxy_model)
        self.ui.setupTableView.setItemDelegate(self.setupDelegate)
        self.ui.setupTableView.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )
        self.ui.setupTableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.setupTableView.customContextMenuRequested.connect(self.contextMenu)

    def insert_data(self, index):
        self.setupModel.insertRows(index, count=1, init_data=self.new_row)
        
    def insert_data_above(self, index, additional_cam_names=[]):
        existing_cam_names = self.setupModel.dataframe["CAM NAME"].tolist()
        new_cam_name = self.generate_unique_cam_name(existing_cam_names, additional_cam_names)
        self.new_row = pd.DataFrame(
            [[new_cam_name, np.nan, np.nan, [], "Offline"]],
            columns=["CAM NAME", "IP", "ZONE", "COORD", "STATUS"],
        )
        self.setupModel.insertRows(index, count=1, init_data=self.new_row)

    def insert_data_below(self, index, additional_cam_names=[]):
        existing_cam_names = self.setupModel.dataframe["CAM NAME"].tolist()
        new_cam_name = self.generate_unique_cam_name(existing_cam_names, additional_cam_names)
        self.new_row = pd.DataFrame(
            [[new_cam_name, np.nan, np.nan, [], "Offline"]],
            columns=["CAM NAME", "IP", "ZONE", "COORD", "STATUS"],
        )
        self.setupModel.insertRows(index + 1, count=1, init_data=self.new_row)


    def remove_camera(self, row_index: list[int]) -> None:
        # Get cam name before removing rows
        df: pd.DataFrame = self.setupModel.dataframe
        # get remove row index with status is True (camera is running) (df["STATUS"] == "True") &
        removed_rows = df[df.index.isin(row_index)]
        # get list of cam name
        cam_name_lst = removed_rows.loc[:, "CAM NAME"].to_list()
        self.setupModel.removeRows(row_index, count=1)
        self.send_remove_cam_signal.emit(cam_name_lst)

    def contextMenu(self):
        menu = QtWidgets.QMenu()
        insert_above = menu.addAction("Chèn hàng phía trên")
        insert_below = menu.addAction("Chèn hàng phía dưới")
        remove_data = menu.addAction("Xoá dữ liệu đang chọn")

        if self.ui.setupTableView.selectionModel().hasSelection():
            cam_names_to_remove = [
                self.sort_proxy_model.mapToSource(idx).row()
                for idx in self.ui.setupTableView.selectionModel().selectedRows()
            ]
            remove_data.triggered.connect(
                lambda: self.delete_cameras_requested.emit(cam_names_to_remove)
            )
            remove_data.triggered.connect(
                lambda: self.remove_camera(cam_names_to_remove)
            )
            
        if self.ui.setupTableView.selectedIndexes():
            current_idx = self.sort_proxy_model.mapToSource(
                self.ui.setupTableView.currentIndex()
            ).row()

            additional_cam_names = [self.setupModel.dataframe.loc[i, "CAM NAME"] for i in cam_names_to_remove]
            insert_above.triggered.connect(lambda: self.insert_data_above(current_idx, additional_cam_names))
            insert_below.triggered.connect(lambda: self.insert_data_below(current_idx, additional_cam_names))
            
        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())


class SetupWidgetFunction(SetupTable):
    delete_rows_requested = QtCore.pyqtSignal(list)
    recv_setting_data = QtCore.pyqtSignal(list)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.p = parent
        
        self.setting_df = pd.DataFrame([], columns=["CAM NAME", "LANE_NUMBER", "HEIGHT", "FOCAL_LENGTH"])
        self.settingModel = SettingTableModel(self.setting_df, editable=True, exclude_col=[0])

    @QtCore.pyqtSlot(str, bool)
    def recv_camera_status(self, cam_name: str, status: bool):
        df: pd.DataFrame = self.setupModel.dataframe
        # get column index of STATUS
        col_status_idx = df.columns.get_indexer(["STATUS"])[0]
        # get row index if value in CAM NAME equal to cam_name
        row_idx = df.index[df["CAM NAME"] == cam_name].to_list()
        # return if it doesn't exist
        if len(row_idx) <= 0:
            return
        # update new status value in STATUS
        _status: str = "Online" if status else "Offline"
        self.setupModel.update_data(row_idx[0], col_status_idx, _status)

    @QtCore.pyqtSlot(str, list)
    def recv_coord(self, cam_name: str, points: list):
        df: pd.DataFrame = self.setupModel.dataframe
        coord_idx = df.columns.get_indexer(["COORD"])[0]
        row_idx = df.index[df["CAM NAME"] == cam_name].to_list()
        if len(row_idx) <= 0:
            return
        self.setupModel.update_data(row_idx[0], coord_idx, points)

    def filterColumnSearch(self, idx):
        self.sort_proxy_model.setFilterKeyColumn(idx)

    def update_search(self, text):
        """Connected to tableSearch bar (QLineEdit)"""
        self.sort_proxy_model.setFilterWildcard(f"*{text}*")

    def on_selectROI(self):
        df: pd.DataFrame = self.setupModel.dataframe
        df = df[df["CAM NAME"].notnull() & df["IP"].notnull()]
        df.reset_index(inplace=True, drop=True)

        if df.shape[0] <= 0:
            return

        roi_window = SelectROIDialog(data=df, parent=self.p, server_ip_combo=self.ui.comboBoxServerIP.currentText())
        roi_window.send_coord.connect(self.recv_coord)
        roi_window.exec()

    def on_initButtonClicked(self):
        cam_name_columns = pd_to_list_for_setting(
            self.setupModel.dataframe["CAM NAME"].to_frame()
        )
        height_default = 10
        lane_number_default = 2
        focal_length_default = 0.3

        self.send_cam_names.emit(
            cam_name_columns,
            lane_number_default,
            height_default,
            focal_length_default
        )

    def on_writeExcelClicked(self):
        filetypes = "Excel Files (*.xlsx);;All Files (*.*)"
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Lưu File", ".", filetypes
        )
        try:
            df: pd.DataFrame = self.setupModel.dataframe
            if "STATUS" in df.columns:
                save_df = df.drop("STATUS", axis=1)
            save_df.to_excel(filename, index=None)
            QtWidgets.QMessageBox.information(self.p, "", "Lưu file thành công!")
        except Exception:
            QtWidgets.QMessageBox.critical(
                self.p, "", "Không thể lưu file! Hãy thử lại."
            )

    def on_LiveStreamClicked(self):
        self.send_table_data.emit(pd_to_list(self.setupModel.dataframe))
        self.send_table_data_to_AI.emit(pd_to_list(self.setupModel.dataframe))
        # self.recv_setting_data.connect(self.recv_setting_data_table)
        self.ui.btnLiveStreamPage.setChecked(True)

    def generate_unique_cam_name(self, existing_cam_names, additional_cam_names=[]):
        all_cam_names = existing_cam_names + additional_cam_names
        index = 1
        while True:
            new_cam_name = f"CAM{index:02}"
            if new_cam_name not in all_cam_names:
                return new_cam_name
            index += 1

    def on_addDataClicked(self):
        existing_cam_names = self.setupModel.dataframe["CAM NAME"].tolist()
        new_cam_name = self.generate_unique_cam_name(existing_cam_names)
        self.new_row = pd.DataFrame(
            [[new_cam_name, np.nan, np.nan, [], "Offline"]],
            columns=["CAM NAME", "IP", "ZONE", "COORD", "STATUS"],
        )
        self.insert_data(self.setupModel.rowCount())

    def on_deleteDataClicked(self):
        if not self.ui.setupTableView.selectionModel().hasSelection():
            return
        rows_indexes = [
            self.sort_proxy_model.mapToSource(idx).row()
            for idx in self.ui.setupTableView.selectionModel().selectedRows()
        ]
        self.remove_camera(rows_indexes)

        # Emit the signal with the index of the camera to delete
        self.delete_rows_requested.emit(rows_indexes)

    def on_openFile(self):
        current_df: pd.DataFrame = self.setupModel.dataframe
        num_active_cam: int = len(current_df[current_df["STATUS"] == "Online"])

        if num_active_cam > 0:
            ret = QtWidgets.QMessageBox.warning(
                self.p,
                "CẢNH BÁO",
                "NẾU MỞ FILE MỚI, CÁC DỮ LIỆU VÀ CAMERA HIỆN TẠI SẼ BỊ XOÁ. BẠN CÓ MUỐN TIẾP TỤC?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if ret == QtWidgets.QMessageBox.No:
                return

        cam_name_lst: list = current_df.loc[:, "CAM NAME"].to_list()

        self.send_remove_cam_signal.emit(cam_name_lst)

        filetypes = "Excel Files (*.xls, *.xlsx);;All Files (*.*)"
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.p, "Chọn File cần mở", ".", filetypes
        )
        if not filename:
            QtWidgets.QMessageBox.critical(
                self.p, "LỖI", "KHÔNG THỂ ĐỌC FILE! HÃY THỬ LẠI!"
            )
            return

        req_cols = ["CAM NAME", "IP", "ZONE", "COORD"]
        self.df = pd.read_excel(filename)

        if missing_cols := set(req_cols) - set(self.df.columns):
            QtWidgets.QMessageBox.critical(
                self, "ERROR!", "Các cột bị thiếu: " + ", ".join(missing_cols)
            )
            return

        if "STATUS" not in self.df.columns:
            self.df["STATUS"] = "Offline"
        self.df["COORD"] = self.df["COORD"].astype("object")

        null_mask = self.df["COORD"].isnull()
        self.df.loc[null_mask, "COORD"] = self.df.loc[null_mask, "COORD"].apply(
            lambda _: []
        )
        self.df.loc[:, "COORD"] = self.df.loc[:, "COORD"].apply(pd.eval)

        self.df.reset_index(inplace=True, drop=True)
        QtWidgets.QMessageBox.information(self.p, "", "Đọc file thành công!")
        self.setupModel = SetupTableModel(self.df, editable=True, exclude_col=[3, 4])
        self.sort_proxy_model = QtCore.QSortFilterProxyModel()
        self.sort_proxy_model.setSourceModel(self.setupModel)
        self.ui.setupTableView.setModel(None)
        self.ui.setupTableView.setModel(self.sort_proxy_model)
        self.ui.setupTableView.setItemDelegate(self.setupDelegate)