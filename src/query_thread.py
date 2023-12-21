import datetime
from threading import Lock

import numpy as np
import pandas as pd
import xarray as xr
from PyQt5 import QtCore

from src.query import query_date_time


class QueryDateTimeThread(QtCore.QThread):
    send_query_data = QtCore.pyqtSignal(xr.Dataset, int)
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)
    
    def __init__(self, collection, from_datetime: datetime.datetime, to_datetime: datetime.datetime, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.p = parent
        self.collection = collection
        self.from_datetime = from_datetime
        self.to_datetime = to_datetime
        from_datetime_str = self.from_datetime.isoformat(timespec='milliseconds')
        to_datetime_str = self.to_datetime.isoformat(timespec='milliseconds')
        self.pipeline = query_date_time(from_datetime_str, to_datetime_str)
        self.lst_date = pd.date_range(self.from_datetime.date(), self.to_datetime.date(), freq="D")
        self.lst_date = self.lst_date.strftime("%d/%m/%Y").to_list()
    
    def run(self) -> None:
        try:
            document = self.collection.aggregate(self.pipeline)
        except Exception as error:
            self.error.emit("Có lỗi xảy ra khi truy vấn dữ liệu!")
            return
        
        data = self.preprocess_query_document(document)

        if data is not None:
            self.send_query_data.emit(data, len(self.lst_date))
        self.finished.emit()

    def preprocess_query_document(self, document) -> xr.Dataset:
        vehicle_lst = ["CAR", "BUS", "TRUCK", "TRAILER"]
        index_lst = ("CAM NAME", "Date", "Time")

        vehicles = {veh: (index_lst, []) for veh in vehicle_lst}

        cam_ids = []
        times = ["{:02d}:00".format(i) for i in range(24)]

        for doc in document:
            cam_ids.append("CAM{:02d}".format(int(doc["_id"]) + 1))

            vehicles_date = {k: np.zeros((len(self.lst_date), len(times)), dtype=np.int16) for k in vehicles.keys()}
            
            for data in doc["Data"]:
                date_idx = self.lst_date.index(data["Date"])


                for veh in vehicles:
                    vehicles_date[veh][date_idx][data["Time"]] = data[veh]

            for veh in vehicles:
                vehicles[veh][1].append(vehicles_date[veh].tolist())

                        
        is_arr_inp_empty = all(len(d[1]) == 0 for d in vehicles.values())
        all_zeros = all(np.all(np.array(data[1]) == 0) for data in vehicles.values())
        
        if is_arr_inp_empty or all_zeros:
            self.error.emit("Không có dữ liệu trong khoảng thời gian được chọn!")
            return
        
        x3d = xr.Dataset(
            vehicles,
            coords = {
                "CAM NAME": cam_ids,
                "Date": self.lst_date,
                "Time": times
            }
        )
        
        cam_names = x3d["CAM NAME"].values
        cam_numbers = [int(name[3:]) for name in cam_names]
        sorted_indices = np.argsort(cam_numbers)
        sorted_cam_names = cam_names[sorted_indices]
        sorted_dataset = x3d.assign_coords({"CAM NAME": sorted_cam_names})
                
        return sorted_dataset

class QueryViolationThread(QtCore.QThread):
    update_info = QtCore.pyqtSignal(str)
    send_query_data = QtCore.pyqtSignal(pd.DataFrame)
    send_data_to_charts = QtCore.pyqtSignal(pd.DataFrame, pd.Series, pd.Series, list)
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)
    
    def __init__(self, collection, from_datetime: datetime.datetime, to_datetime: datetime.datetime, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.p = parent
        self.collection = collection
        self.from_datetime = from_datetime
        self.to_datetime = to_datetime
        self.from_datetime_str = self.from_datetime.isoformat(timespec='milliseconds')
        self.to_datetime_str = self.to_datetime.isoformat(timespec='milliseconds')
        # self.pipeline = query_date_time(from_datetime_str, to_datetime_str)
        date_range = create_date_range(start_date_str=self.from_datetime, end_date_str=self.to_datetime)
        self.date_range = date_range.strftime("%y-%m-%d %H:00").to_list()
        self._lock = Lock()
    
    def run(self) -> None:
        with self._lock:
            try:
                document = self.collection.find(
                    {
                        "time": {
                            '$gte': self.from_datetime_str,
                            "$lte": self.to_datetime_str
                        }
                    },
                    {
                        "type": 1,
                        "location": 1,
                        "path": 1,
                        "speed": 1,
                        "time": 1
                    }
                )
            except Exception as error:
                self.error.emit("Có lỗi xảy ra khi truy vấn dữ liệu!")
                return
                        
            df = self.check_query_error(document)
            if df is not None:
                self.send_query_data.emit(df)
                self.update_info.emit("Spawn process...")
                # pool = mp.Pool(processes=1)
                self.update_info.emit("Process data...")
                # result = pool.apply_async(process_data, (df,))
                # total_in_day, type_occurrences, type_location_count = result.get()
                total_in_day, type_occurrences, type_location_count = process_data(df.copy())
                self.send_data_to_charts.emit(total_in_day, type_occurrences, type_location_count, self.date_range)
                # pool.terminate()
                # pool.join()
            else:
                self.error.emit("Lỗi khi truy vấn dữ liệu!")
            self.finished.emit()

    def check_query_error(self, document):
        try:
            if self.collection.count_documents({}) == 0:
                self.error.emit("Không có dữ liệu vi phạm trên CSDL!")
                return
            else:
                df = pd.DataFrame([])
                for data in document:
                    df = df._append(data, ignore_index=True)
                try:
                    if 'speed' in df.columns:
                        # self.df = self.df.drop(['_id'], axis=1)
                        new_cols = ['type', 'path', 'speed', 'time', 'location']
                        df = df[new_cols]
                    else:
                        df['speed'] = ''
                        new_cols = ['type', 'path', 'speed', 'time', 'location']
                        df = df[new_cols]
                except Exception:
                    return
                
            return df
        except Exception as error:
            self.error.emit("Lỗi kết nối tới CSDL!")
            return
    
    def deleteAll(self):
        self.update_info.disconnect()
        self.send_data_to_charts.disconnect()
        self.send_query_data.disconnect()
        self.finished.disconnect()
        self.error.disconnect()
        self.wait()
        self.quit()
        self.deleteLater()
        

def process_data(df: pd.DataFrame):    
    df_ = df.loc[:, ["type", "time", "location"]].copy()
    df_["time"] = pd.to_datetime(df_["time"], format="%Y-%m-%dT%H:%M:%S.%f")
    df_["Date"] = df_["time"].dt.date
    df_["Hour"] = df_["time"].dt.hour
    df_t = df_.drop(["location", "time"], axis=1)
    
    group_date_hour = df_t.groupby(["Date", "Hour", "type"]).size().unstack()
    total_in_day = group_date_hour.groupby("Date").sum()
    
    # Pie chart
    # cols = ["type", "location"]
    # curr_idx = self.ui.comboVioPie.currentIndex()
    type_occurrences = df.loc[:, "type"].value_counts()
    
    # Overspeed?
    df_speed = df[df.loc[:, "type"] == "Quá tốc độ"].copy()
    df_speed["time"] = pd.to_datetime(df_speed["time"], format="%Y-%m-%dT%H:%M:%S.%f")
    df_speed["Date"] = df_speed["time"].dt.date
    df_speed["Date"] = df_speed["Date"].astype(str)
    df_speed["Hour"] = df_speed["time"].dt.hour
    df_speed["Hour"] = df_speed["Hour"].astype(str)
    df_speed["time"] = df_speed["time"].dt.strftime("%y-%m-%d %H:00")
    
    # avg_speed_loc = df_speed.loc[:, ["location", "speed"]].groupby("location")["speed"].mean()
    # avg_speed = df_speed.groupby(["location", "Date", "Hour"])["speed"].mean()
    # avg_speed = df_speed.loc[:, ["location", "time", "speed"]].groupby(["location", "time"])["speed"].mean()
    # df_avg_speed = avg_speed.reset_index()
    # avg_speed_loc = avg_speed.groupby("location").mean()
    
    df_type = df.loc[:,  ["type",  "location"]].copy()

    df_count = df_type.groupby(["type", "location"]).size()
    
    return total_in_day, type_occurrences, df_count


def create_date_range(start_date_str, end_date_str):
    # Convert the start and end date strings to pandas Timestamp objects
    start_date = pd.to_datetime(start_date_str, format="%Y-%m-%d %H:%M")
    end_date = pd.to_datetime(end_date_str, format="%Y-%m-%d %H:%M")

    # Generate the date range using pd.date_range
    date_range = pd.date_range(start=start_date, end=end_date, freq='H')

    return date_range
