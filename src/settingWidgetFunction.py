from __future__ import annotations

import configparser
import re
from typing import Any

import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets

from src.pandasmodel import SettingTableDelegate, SettingTableModel
from ui.ui_mainwindow import Ui_MainWindow


def pd_to_list_for_setting(df) -> list:
    results = list()
    camera_stream = df.shape[0]
    if camera_stream > 0:
        df = df[df["CAM NAME"].notnull()]
        for _, row in df.iterrows():
            index = int(re.findall(r"\d+", row["CAM NAME"])[-1])
            results.append(
                {
                    "INDEX": index - 1,
                    "CAM NAME": row["CAM NAME"],
                    "HEIGHT": row["HEIGHT"],
                    "LANE_NUMBER": row["LANE_NUMBER"],
                    "FOCAL_LENGTH": row["FOCAL_LENGTH"],
                }
            )

    return results

class SettingTable(QtWidgets.QWidget):
    send_setting_table = QtCore.pyqtSignal(list)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.ui: Ui_MainWindow = parent.ui
        
        self.new_row = pd.DataFrame([[np.nan, np.nan, np.nan, np.nan]], columns=["CAM NAME", "LANE_NUMBER", "HEIGHT", "FOCAL_LENGTH"])
        
        self.df = pd.DataFrame([], columns=["CAM NAME", "LANE_NUMBER", "HEIGHT", "FOCAL_LENGTH"])
        
        self.settingModel = SettingTableModel(self.df, editable=True, exclude_col=[0])
        self.settingDelegate = SettingTableDelegate()
        
        self.ui.settingTableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.ui.settingTableView.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        
        self.sort_proxy_model = QtCore.QSortFilterProxyModel()
        self.sort_proxy_model.setSourceModel(self.settingModel)
        self.ui.settingTableView.setSortingEnabled(False)
        self.ui.settingTableView.setModel(self.sort_proxy_model)
        self.ui.settingTableView.setItemDelegate(self.settingDelegate)
        self.ui.settingTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.ui.settingTableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.settingTableView.customContextMenuRequested.connect(self.contextMenu)
        
    def insert_data(self, index):
        default_values = {
            "LANE_NUMBER": 2,
            "HEIGHT": 0.035,
            "FOCAL_LENGTH": 0.017
        }
        
        self.new_row["LANE_NUMBER"] = default_values["LANE_NUMBER"]
        self.new_row["HEIGHT"] = default_values["HEIGHT"]
        self.new_row["FOCAL_LENGTH"] = default_values["FOCAL_LENGTH"]

        self.settingModel.insertRows(index, count=1, init_data=self.new_row)
        
    def remove_camera(self, row_indexes: list[int]) -> None:
        self.settingModel.removeRows(row_indexes, count=1)

    # Inside your contextMenu method:
    def contextMenu(self):
        menu = QtWidgets.QMenu()
        insert_above = menu.addAction("Chèn dòng phía trên")
        insert_below = menu.addAction("Chèn dòng phía dưới")
        remove_data = menu.addAction("Xoá các dòng đã chọn")

        selected_indexes = self.ui.settingTableView.selectionModel().selectedIndexes()
        selected_rows = list(set(index.row() for index in selected_indexes))

        if selected_rows:
            current_idx = self.sort_proxy_model.mapToSource(self.ui.settingTableView.currentIndex()).row()
            
            insert_above.triggered.connect(lambda: self.insert_data(current_idx))
            insert_below.triggered.connect(lambda: self.insert_data(current_idx + 1))
            remove_data.triggered.connect(lambda: self.remove_camera(selected_rows))

        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

        
class SettingWidgetFunction(SettingTable):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.p = parent
        
        # Connect the delete_rows_requested signal to the on_delete_rows_requested slot
        self.parent().setup_functions.delete_cameras_requested.connect(
            self.on_delete_rows_requested
        )
        
    @QtCore.pyqtSlot(list)
    def on_delete_rows_requested(self, cam_indices_to_remove):
        try:
            cam_names_to_remove = [
                self.settingModel.dataframe.loc[index, "CAM NAME"]
                for index in cam_indices_to_remove
            ]

            self.remove_camera_by_cam_names(cam_names_to_remove)
        except Exception:
            pass

    def generate_cam_name(self, index):
        return f"CAM{index + 1:02}"  # Two-digit format

    def on_addDataClicked(self):
        new_cam_name = self.generate_cam_name(self.settingModel.rowCount())
        self.new_row = pd.DataFrame([[new_cam_name, np.nan, np.nan, np.nan]], columns=["CAM NAME", "LANE_NUMBER", "HEIGHT", "FOCAL_LENGTH"])
        
        self.insert_data(self.settingModel.rowCount())

    def setup_connections(self):
        self.parent().send_cam_names.connect(self.receive_cam_names)
        
    def on_writeConfigFileClicked(self):
        config = configparser.ConfigParser()
        filetypes = "Config Files (*.ini);;All Files (*.*)"
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Lưu File", ".", filetypes)
        try:
            df: pd.DataFrame = self.settingModel.dataframe
            column_names = df.columns.tolist()
            
            # Create a ConfigParser instance
            config = configparser.ConfigParser()

            # Loop over column names to create sections
            for column in column_names:
                section_name = column  # Use column name as section name
                config[section_name] = {}
                
                for index, value in df[column].items():
                    config[section_name][f'Row_{index+1}'] = str(value)

            # Save the config to a file
            with open(filename, 'w') as configfile:
                config.write(configfile)
            QtWidgets.QMessageBox.information(self.p, "SUCCESS", "Lưu file thành công!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.p, "ERROR", f"Không thể lưu file! Chi tiết lỗi: {str(e)}")
            
    def on_openConfigFileClicked(self):
        filetypes = "Config Files (*.ini);;All Files (*.*)"
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Mở file", ".", filetypes)
        
        if filename:
            try:
                # Read the configuration file
                config = configparser.ConfigParser()
                config.read(filename)
                
                # Create a dictionary to store the data
                data_dict = {}

                # Loop through sections in the config
                for section_name in config.sections():
                    section_data = dict(config.items(section_name))
                    data_dict[section_name] = section_data

                # Create a DataFrame from the dictionary
                df = pd.DataFrame(data_dict)

                # Set the DataFrame as the data for your SettingTableModel
                self.settingModel.set_data(df)

                QtWidgets.QMessageBox.information(self, "SUCCESS", "Mở file cấu hình camera thành công!")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "ERROR", f"Lỗi khi mở file cấu hình: {str(e)}")
        
    @QtCore.pyqtSlot(list)
    def remove_camera_by_cam_names(self, cam_names: list):
        df: pd.DataFrame = self.settingModel.dataframe
        rows_to_remove = df[df["CAM NAME"].isin(cam_names)].index.tolist()
        self.remove_camera(rows_to_remove)
        
    @QtCore.pyqtSlot(list, int, float, float)
    def receive_cam_names(self, cam_names: list, lane_default: int, height_default: float, focal_length_default: float):
        self.lane_number = lane_default
        self.height_default = height_default
        self.distance_coeff_default = focal_length_default
        
        df = pd.DataFrame(cam_names)
        self.settingModel.set_data(df)
        
    @QtCore.pyqtSlot()
    def send_setting_data_to_AI(self):
        self.send_setting_table.emit(pd_to_list_for_setting(self.settingModel.dataframe))
