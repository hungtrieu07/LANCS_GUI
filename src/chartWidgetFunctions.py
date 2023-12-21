import datetime
from typing import Tuple

import pandas as pd
import xarray as xr
from PyQt5 import QtCore, QtWidgets

from src.pandasmodel import PandasModel
from src.query_thread import QueryDateTimeThread
from ui.ui_mainwindow import Ui_MainWindow


class SetupFilterBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p = parent
        self.ui: Ui_MainWindow = parent.ui
        self.db = parent.db

        hours = ['{:02d}'.format(i) for i in range(24)]
        mins = ['{:02d}'.format(i) for i in range(60)]

        # From Hour Combobox
        self.ui.fromHourEdit.clear()
        self.ui.fromHourEdit.addItems(hours)
        self.ui.fromHourEdit.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.ui.fromHourEdit.setMaxVisibleItems(10)
        self.ui.fromHourEdit.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ui.fromHourEdit.setCurrentText("00")
        self.ui.fromHourEdit.activated.connect(lambda: self.on_activateCombobox('from_hour', self.ui.fromHourEdit))


        # To Hour Combobox
        self.ui.toHourEdit.clear()
        self.ui.toHourEdit.addItems(hours)
        self.ui.toHourEdit.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.ui.toHourEdit.setMaxVisibleItems(10)
        self.ui.toHourEdit.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ui.toHourEdit.setCurrentText("23")
        self.ui.toHourEdit.activated.connect(lambda: self.on_activateCombobox('to_hour', self.ui.toHourEdit))

        # From Minute Combobox
        self.ui.fromMinuteEdit.clear()
        self.ui.fromMinuteEdit.addItems(mins)
        self.ui.fromMinuteEdit.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.ui.fromMinuteEdit.setMaxVisibleItems(10)
        self.ui.fromMinuteEdit.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ui.fromMinuteEdit.setCurrentIndex(0)
        self.ui.fromMinuteEdit.activated.connect(lambda: self.on_activateCombobox('from_min', self.ui.fromMinuteEdit))

        # To Minute Combobox
        self.ui.toMinuteEdit.clear()
        self.ui.toMinuteEdit.addItems(mins)
        self.ui.toMinuteEdit.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.ui.toMinuteEdit.setMaxVisibleItems(10)
        self.ui.toMinuteEdit.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ui.toMinuteEdit.setCurrentText("59")
        self.ui.toMinuteEdit.activated.connect(lambda: self.on_activateCombobox('to_min', self.ui.toMinuteEdit))

        # From Date
        self.ui.fromDateEdit.setDate(datetime.datetime.now())
        self.from_date_data = self.ui.fromDateEdit.date().toPyDate()
        self.ui.fromDateEdit.dateChanged.connect(self.on_fromDateChanged)

        # To Date
        self.ui.toDateEdit.setDate(datetime.date.today())
        self.to_date_data = self.ui.toDateEdit.date().toPyDate()
        self.ui.toDateEdit.dateChanged.connect(self.on_tobyDateTime)

        self.time_data = {
            'from_hour': self.ui.fromHourEdit.currentText(), 
            'from_min': self.ui.fromMinuteEdit.currentText(),
            'to_hour': self.ui.toHourEdit.currentText(),
            'to_min': self.ui.toMinuteEdit.currentText()
        }

    def on_activateCombobox(self, key: str, combobox: QtWidgets.QComboBox) -> None:
        self.time_data[key] = combobox.currentText()

    def on_tobyDateTime(self):
        self.to_date_data = self.ui.toDateEdit.date().toPyDate()

    def on_fromDateChanged(self):
        self.from_date_data = self.ui.fromDateEdit.date().toPyDate()  

    def collect_filter_datetime(self) -> Tuple[datetime.datetime, datetime.datetime]:
        """ Query database """
        # From Hour minute 
        from_dt_hm = datetime.datetime.strptime('-'.join([self.time_data['from_hour'], self.time_data['from_min']]), "%H-%M").time()
        # From datetime and hour minute
        from_datetime = datetime.datetime.combine(self.from_date_data, from_dt_hm)
        
        # To Hour minute      
        to_dt_hm = datetime.datetime.strptime('-'.join([self.time_data['to_hour'], self.time_data['to_min']]), "%H-%M").time()
        # To datetime and hour minute
        to_datetime = datetime.datetime.combine(self.to_date_data, to_dt_hm)

        return from_datetime, to_datetime


class ChartWidgetFunctions(SetupFilterBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p = parent
                
        self.maximized_dict: dict[str, bool] = {"stackedTotalBar": False,
                                                "stackedDayBar": False,
                                                "stackedHourBar": False,
                                                "frameMostTime": False,
                                                "frameMostTotal": False}
        
        for chart_name in self.maximized_dict:
            if not hasattr(self.ui, chart_name):
                continue
            
            chart_widget: QtWidgets.QWidget = getattr(self.ui, chart_name)
            
            if type(chart_widget).__name__ == "CustomStackBar":
                chart_widget.installEventFilter(self)
        
        self.name_to_pos = {}
        
        for index in range(self.ui.gridLayout.count()):
            widget = self.ui.gridLayout.itemAt(index).widget()
            pos = self.ui.gridLayout.getItemPosition(index)
            self.name_to_pos[widget.objectName()] = pos
                
        self.collection = self.db['vehicles']
        
        self.dfr_rong = pd.DataFrame([], columns=["CAM NAME", "Total Vehicles", "Average"])
        self.empty_pandas_model = PandasModel(self.dfr_rong, editable=False)
                
        self.ui.stackedHourBar.installEventFilter(self)
        self.ui.stackedTotalBar.installEventFilter(self)
        self.ui.stackedDayBar.installEventFilter(self)
        
        self.ui.mostTotalTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.ui.mostTotalTable.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.ui.mostTimeTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.ui.mostTimeTable.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
    def analysis_table(self, x3d: xr.Dataset, num_dates: int) -> None:
        most_vehicles_total_df = x3d.sum(dim=["Date", "Time"]).to_dataframe().sum(axis=1).sort_values(axis=0, ascending=False).to_frame(name="Total Vehicles").reset_index()
        
        most_vehicles_total_df = most_vehicles_total_df.assign(Average = lambda x: x["Total Vehicles"] // num_dates)
        
        # most_vehicles_time_df = x3d.to_dataframe().sum(axis=1).sort_values(axis=0, ascending=False).to_frame(name="Total").reset_index().head(5)
        
        most_vehicles_time_df = x3d.to_dataframe().sum(axis=1).to_frame(name="Total").reset_index()

        most_vehicles_time_df = most_vehicles_time_df.loc[most_vehicles_time_df.groupby("CAM NAME")["Total"].idxmax()].reset_index(drop=True)
        
        most_total_model = PandasModel(most_vehicles_total_df, editable=False)
        most_time_model = PandasModel(most_vehicles_time_df, editable=False)
        
        self.ui.mostTotalTable.setModel(None)
        self.ui.mostTotalTable.setModel(most_total_model)
        
        self.ui.mostTimeTable.setModel(None)
        self.ui.mostTimeTable.setModel(most_time_model)
        
    def on_FilterClicked(self):
        from_datetime, to_datetime = self.collect_filter_datetime()
                
        query = QueryDateTimeThread(
            collection=self.collection,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            parent=self.p
        )
        
        query.send_query_data.connect(self.on_FinishQuery)
        query.error.connect(self.on_errorQuery)
        query.finished.connect(query.quit)
        query.finished.connect(query.deleteLater)
        
        if not query.isRunning():
            query.start()

    @QtCore.pyqtSlot(str)
    def on_errorQuery(self, error: str):
        QtWidgets.QMessageBox.critical(self.p, "LỖI", "Lỗi xảy ra khi truy vấn dữ liệu thống kê!")

        self.ui.mostTotalTable.setModel(self.empty_pandas_model)
        self.ui.mostTimeTable.setModel(self.empty_pandas_model)
        try:
            self.ui.stackedTotalBar.clearChart()
            self.ui.stackedTotalBar.chart.removeAxis(self.ui.stackedTotalBar.chart.axisX())
            self.ui.stackedTotalBar.chart.removeAxis(self.ui.stackedTotalBar.chart.axisY())
            self.ui.stackedTotalBar.chart.legend().hide()
            self.ui.stackedTotalBar.chart.setTitle("")

            self.ui.stackedDayBar.clearChart()
            self.ui.stackedDayBar.chart.removeAxis(self.ui.stackedDayBar.chart.axisX())
            self.ui.stackedDayBar.chart.removeAxis(self.ui.stackedDayBar.chart.axisY())
            self.ui.stackedDayBar.chart.legend().hide()
            self.ui.stackedDayBar.chart.setTitle("")

            self.ui.stackedHourBar.clearChart()
            self.ui.stackedHourBar.chart.removeAxis(self.ui.stackedHourBar.chart.axisX())
            self.ui.stackedHourBar.chart.removeAxis(self.ui.stackedHourBar.chart.axisY())
            self.ui.stackedHourBar.chart.legend().hide()
            self.ui.stackedHourBar.chart.setTitle("")
        except Exception:
            pass

    @QtCore.pyqtSlot(xr.Dataset, int)
    def on_FinishQuery(self, x3d: xr.Dataset, num_dates):
        self.x3d = x3d
        self.analysis_table(self.x3d, num_dates)
        
        self.df_by_cam = self.x3d.sum(dim=["Date", "Time"]).to_dataframe()
        
        self.ui.stackedTotalBar.update_chart(
            data=self.df_by_cam, 
            categories=self.df_by_cam.index.to_list(), 
            chart_title="Tổng số phương tiện của mỗi camera", 
            axisX_title="Tên camera", 
            axisY_title="Số lượng phương tiện")
                
        self.ui.stackedTotalBar.series.clicked.connect(self.on_ClickedTotalBar)

    def on_ClickedTotalBar(self, index, barset):
        df_by_day = self.x3d.sum(dim="Time").to_dataframe()

        self.clicked_cam_name = self.df_by_cam.index.to_list()[index]

        df_by_day_cam: pd.DataFrame = df_by_day.loc[self.clicked_cam_name]

        # self.ui.stackedHourBar.setBar(percent=False)
        self.ui.stackedDayBar.update_chart(
            data=df_by_day_cam,
            categories=df_by_day_cam.index.to_list(),
            chart_title=f"Tổng số phương tiện mỗi ngày từ camera {self.clicked_cam_name}",
            axisX_title="Ngày",
            axisY_title="Số lượng phương tiện",
            label_angle=-90,
        )

        self.ui.stackedDayBar.series.clicked.connect(self.on_ClickedDayBar)

    def on_ClickedDayBar(self, index, barset):
        
        df_by_day_cam: pd.DataFrame =  self.x3d.sum(dim="Time").to_dataframe().loc[self.clicked_cam_name]

        clicked_day_name = df_by_day_cam.index.to_list()[index]
        df_by_day_cam_and_day: pd.DataFrame = self.x3d.to_dataframe().loc[self.clicked_cam_name, clicked_day_name]

        self.ui.stackedHourBar.setBar(percent=True)
        self.ui.stackedHourBar.update_chart(
            data=df_by_day_cam_and_day,
            categories=df_by_day_cam_and_day.index.to_list(),
            chart_title=f"Số phương tiện mỗi giờ vào ngày {clicked_day_name} từ camera {self.clicked_cam_name}",
            axisX_title="Giờ",
            axisY_title="Số lượng phương tiện",
            series_label_format="@value ",
        )

    def filter_chart(self, chart_dict: dict, ignore_obj_name: str, show: bool):            
        for obj_name in chart_dict:                
            if obj_name == ignore_obj_name:
                continue

            if not hasattr(self.ui, obj_name):
                continue
            
            chart_widget: QtWidgets.QWidget = getattr(self.ui, obj_name)
            row_span, col_span = self.name_to_pos[obj_name][2:]
            
            if show:
                self.setWidgetSpan(chart_widget, row_span, col_span)
                chart_widget.show()
            else:
                self.setWidgetSpan(chart_widget, 1, 1)
                chart_widget.hide()

    def setWidgetSpan(self, widget, rowspan=1, colspan=1):
        index = self.ui.gridLayout.indexOf(widget)
        row, col = self.ui.gridLayout.getItemPosition(index)[:2]
        self.ui.gridLayout.addWidget(widget, row, col, rowspan, colspan)

    def eventFilter(self, source, event) -> bool:
        if event.type() != QtCore.QEvent.MouseButtonDblClick:
            return super().eventFilter(source, event)
        
        obj_name_clicked = source.objectName()
        
        if not hasattr(self.ui, obj_name_clicked): 
            return
        
        if not self.maximized_dict[obj_name_clicked]:
            self.filter_chart(chart_dict=self.maximized_dict,
                              ignore_obj_name=obj_name_clicked,
                              show=False)
            self.maximized_dict[obj_name_clicked] = True
        else:
            self.filter_chart(chart_dict=self.maximized_dict,
                              ignore_obj_name=obj_name_clicked, 
                              show=True)
            self.maximized_dict[obj_name_clicked] = False

        return True