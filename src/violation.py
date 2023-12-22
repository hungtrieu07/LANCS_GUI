import datetime
import os
import traceback
from typing import Tuple

import pandas as pd
from PyQt5 import QtCore, QtWidgets

from src.displayImage import DisplayImage
from src.pandasmodel import ViolationTableModel
from src.query_thread import QueryViolationThread
from ui.ui_mainwindow import Ui_MainWindow

basedir = os.getcwd()

class ScrollEventFilter(QtCore.QObject):
    def eventFilter(self, obj, event):
        if obj.property("canFetchMore"):
            if event.type() == QtCore.QEvent.ScrollPrepare:
                if obj.verticalScrollBar().value() == obj.verticalScrollBar().maximum():
                    obj.model().fetchMore()
        return QtCore.QObject.eventFilter(self, obj, event)

class ReadOnlyDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # last column
        if index.column() == 1:
            return super().createEditor(parent, option, index)
        
class AlignDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter

class ViolationFilterBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui: Ui_MainWindow = parent.ui
        
        hours = ['{:02d}'.format(i) for i in range(24)]
        mins = ['{:02d}'.format(i) for i in range(60)]

        # From Hour Combobox
        self.ui.fromHourEditVio.clear()
        self.ui.fromHourEditVio.addItems(hours)
        self.ui.fromHourEditVio.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.ui.fromHourEditVio.setMaxVisibleItems(10)
        self.ui.fromHourEditVio.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ui.fromHourEditVio.setCurrentText("00")
        self.ui.fromHourEditVio.activated.connect(lambda: self.on_activateCombobox('from_hour', self.ui.fromHourEditVio))


        # To Hour Combobox
        self.ui.toHourEditVio.clear()
        self.ui.toHourEditVio.addItems(hours)
        self.ui.toHourEditVio.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.ui.toHourEditVio.setMaxVisibleItems(10)
        self.ui.toHourEditVio.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ui.toHourEditVio.setCurrentText("23")
        self.ui.toHourEditVio.activated.connect(lambda: self.on_activateCombobox('to_hour', self.ui.toHourEditVio))

        # From Minute Combobox
        self.ui.fromMinuteEditVio.clear()
        self.ui.fromMinuteEditVio.addItems(mins)
        self.ui.fromMinuteEditVio.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.ui.fromMinuteEditVio.setMaxVisibleItems(10)
        self.ui.fromMinuteEditVio.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ui.fromMinuteEditVio.setCurrentIndex(0)
        self.ui.fromMinuteEditVio.activated.connect(lambda: self.on_activateCombobox('from_min', self.ui.fromMinuteEditVio))

        # To Minute Combobox
        self.ui.toMinuteEditVio.clear()
        self.ui.toMinuteEditVio.addItems(mins)
        self.ui.toMinuteEditVio.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.ui.toMinuteEditVio.setMaxVisibleItems(10)
        self.ui.toMinuteEditVio.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ui.toMinuteEditVio.setCurrentText("59")
        self.ui.toMinuteEditVio.activated.connect(lambda: self.on_activateCombobox('to_min', self.ui.toMinuteEditVio))

        # From Date
        self.ui.fromDateEditVio.setDate(datetime.datetime.now())
        self.from_date_data = self.ui.fromDateEditVio.date().toPyDate()
        self.ui.fromDateEditVio.dateChanged.connect(self.on_fromDateChanged)

        # To Date
        self.ui.toDateEditVio.setDate(datetime.date.today())
        self.to_date_data = self.ui.toDateEditVio.date().toPyDate()
        self.ui.toDateEditVio.dateChanged.connect(self.on_tobyDateTime)

        self.time_data = {
            'from_hour': self.ui.fromHourEditVio.currentText(), 
            'from_min': self.ui.fromMinuteEditVio.currentText(),
            'to_hour': self.ui.toHourEditVio.currentText(),
            'to_min': self.ui.toMinuteEditVio.currentText()
        }
        
    def on_activateCombobox(self, key: str, combobox: QtWidgets.QComboBox) -> None:
        self.time_data[key] = combobox.currentText()

    def on_tobyDateTime(self):
        self.to_date_data = self.ui.toDateEditVio.date().toPyDate()

    def on_fromDateChanged(self):
        self.from_date_data = self.ui.fromDateEditVio.date().toPyDate()  

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

class ViolationFunction(ViolationFilterBar):
    send_display_image_error = QtCore.pyqtSignal(str)
    
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.ui: Ui_MainWindow = parent.ui
        self.p = parent
        
        self.db = parent.db
                
        self.maximized_dict: dict[str, bool] = {"stackBarVio": False, 
                                            "pieChartVio": False, 
                                            # "lineChartVio": False, 
                                            "pieChartBatThuong": False,
                                            "pieChartDiBo": False,
                                            "pieChartDungXe": False,
                                            "pieChartNguocChieu": False,
                                            "pieChartQuaTocDo": False}
        
        for chart_name in self.maximized_dict:
            if not hasattr(self.ui, chart_name):
                continue
            chart_widget: QtWidgets.QWidget = getattr(self.ui, chart_name)
            chart_widget.installEventFilter(self)
        
        self.name_to_pos = {}
        
        # for index in range(self.ui.gridLayout_2.count()):
        #     widget = self.ui.gridLayout_2.itemAt(index).widget()
        #     pos = self.ui.gridLayout_2.getItemPosition(index)
        #     self.name_to_pos[widget.objectName()] = pos

        self.collection = self.db["violation_vehicles"]

        self.df = pd.DataFrame([], columns=["VI PHẠM", "ẢNH PHƯƠNG TIỆN", "TỐC ĐỘ", "BIỂN SỐ", "THỜI GIAN VI PHẠM", "ĐỊA ĐIỂM"])
        # self.new_row = pd.DataFrame([["", "", 0, "", "", ""]], columns=["VI PHẠM", "ẢNH PHƯƠNG TIỆN", "TỐC ĐỘ", "BIỂN SỐ", "THỜI GIAN VI PHẠM", "ĐỊA ĐIỂM"])
        # self.empty_pandas_model = PandasModel(self.dfr_rong, editable=False)

        scroll_event_filter = ScrollEventFilter()

        self.violationModel = ViolationTableModel(self.df, editable=False)
        
        self.violationDelegate = AlignDelegate(self.ui.violationTableView)
        self.ui.violationTableView.setItemDelegate(self.violationDelegate)
        
        self.ui.violationTableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.ui.violationTableView.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.sort_proxy_model = QtCore.QSortFilterProxyModel()
        self.sort_proxy_model.setSourceModel(self.violationModel)
        self.ui.violationTableView.setSortingEnabled(False)
        self.ui.violationTableView.setModel(self.sort_proxy_model)
        self.ui.violationTableView.setItemDelegate(self.violationDelegate)
        # self.ui.violationTableView.setItemDelegateForColumn(1, ViolationTableDelegate())
        self.ui.violationTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.ui.violationTableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.violationTableView.installEventFilter(scroll_event_filter)

        self.displayImage = DisplayImage(parent)

        self.ui.violationTableView.clicked.connect(self.display)

    def filterColumnSearch(self, idx):
        self.sort_proxy_model.setFilterKeyColumn(idx)

    def update_search(self, text):
        """Connected to tableSearch bar (QLineEdit)"""
        self.sort_proxy_model.setFilterWildcard(f"*{text}*")

    def get_columns(self):
        col = self.violationModel.dataframe.columns
        return col.delete(col.get_loc("ẢNH PHƯƠNG TIỆN"))

    def on_FilterClicked(self):
        from_datetime, to_datetime = self.collect_filter_datetime()
        
        query = QueryViolationThread(
            collection=self.collection,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            parent=self.p
        )
        
        query.send_query_data.connect(self.recv_query_data)
        query.send_data_to_charts.connect(self.recv_data_charts)
        # query.send_process_update.connect(lambda x: print("Process update status: ", x))
        query.error.connect(self.on_errorQuery)
        query.finished.connect(query.deleteAll)
        query.finished.connect(self.on_queryFinished)
        query.update_info.connect(self.update_info_query)
        
        if not query.isRunning():
            query.start()
        
        if query.isRunning():
            self.ui.labelLoading.setStyleSheet("QLabel { color: green; }")
            self.ui.labelLoading.setText("Loading...")
            self.ui.labelLoading.setVisible(True)
            self.ui.btnFilterVio.setEnabled(False)

    @QtCore.pyqtSlot(str)
    def update_info_query(self, info: str):
        self.ui.labelLoading.setStyleSheet("QLabel { color: green; }")
        self.ui.labelLoading.setText(info)
        self.ui.labelLoading.setVisible(True)

    @QtCore.pyqtSlot()
    def on_queryFinished(self):
        self.ui.btnFilterVio.setEnabled(True)
        self.ui.labelLoading.setVisible(False)

    @QtCore.pyqtSlot(str)
    def on_errorQuery(self, error: str):
        QtWidgets.QMessageBox.critical(self.p, "ERROR", f"{error}")

        rong = pd.DataFrame([], columns=["VI PHẠM", "ẢNH PHƯƠNG TIỆN", "TỐC ĐỘ", "BIỂN SỐ", "THỜI GIAN VI PHẠM", "ĐỊA ĐIỂM"])

        self.ui.violationTableView.setModel(ViolationTableModel(rong, editable=False))
        try:
            self.ui.stackBarVio.chart.removeAxis(self.ui.stackBarVio.chart.axisX())
            self.ui.stackBarVio.chart.removeAxis(self.ui.stackBarVio.chart.axisY())
            self.ui.stackBarVio.clearChart()
            self.ui.stackBarVio.chart.legend().hide()
            self.ui.stackBarVio.chart.setTitle("")
            
            self.ui.pieChartVio.clearChart()
            self.ui.pieChartVio.chart.legend().hide()
            self.ui.pieChartVio.chart.setTitle("")

            self.ui.pieChartBatThuong.clearChart()
            self.ui.pieChartBatThuong.chart.legend().hide()
            self.ui.pieChartBatThuong.chart.setTitle("")

            self.ui.pieChartDiBo.clearChart()
            self.ui.pieChartDiBo.chart.legend().hide()
            self.ui.pieChartDiBo.chart.setTitle("")

            self.ui.pieChartDungXe.clearChart()
            self.ui.pieChartDungXe.chart.legend().hide()
            self.ui.pieChartDungXe.chart.setTitle("")

            self.ui.pieChartNguocChieu.clearChart()
            self.ui.pieChartNguocChieu.chart.legend().hide()
            self.ui.pieChartNguocChieu.chart.setTitle("")
            
            self.ui.pieChartQuaTocDo.clearChart()
            self.ui.pieChartQuaTocDo.chart.legend().hide()
            self.ui.pieChartQuaTocDo.chart.setTitle("")
            
            # self.ui.lineChartVio.chart.removeAxis(self.ui.stackBarVio.chart.axisX())
            # self.ui.lineChartVio.chart.removeAxis(self.ui.stackBarVio.chart.axisY())
            # self.ui.lineChartVio.clearChart()
            # self.ui.lineChartVio.chart.legend().hide()
            # self.ui.lineChartVio.chart.setTitle("")
        except Exception:
            pass
        
        self.ui.labelLoading.setStyleSheet("QLabel { color: red; }")
        self.ui.labelLoading.setText("Failed to execute")
        self.ui.labelLoading.setVisible(True)
        self.ui.btnFilterVio.setEnabled(True)

    @QtCore.pyqtSlot(pd.DataFrame, pd.Series, pd.Series, list)
    def recv_data_charts(self, total_in_day: pd.DataFrame, type_occurrences: pd.Series, type_location_count: pd.Series, date_range: list):
        self.ui.stackBarVio.update_chart(
            data=total_in_day,
            categories=total_in_day.index.astype(str).to_list(),
            chart_title="Biểu đồ vi phạm",
            label_angle=90,
            axisY_title="Số lượng vi phạm",
            axisX_title="Thời gian vi phạm"
        )
        
        try:
            self.ui.pieChartVio.update_chart(
                data=type_occurrences,
                chart_title="Biểu đồ vi phạm"
            )
        except:
            pass
        
        try:
            self.ui.pieChartBatThuong.update_chart(
                data=type_location_count.xs("Vật thể lạ", level="type"),
                chart_title="Biểu đồ điểm nóng có vật thể lạ"
            )
        except:
            pass

        try:
            self.ui.pieChartDiBo.update_chart(
                data=type_location_count.xs("Người đi bộ", level="type"),
                chart_title="Biểu đồ điểm nóng nhiều người đi bộ"
            )
        except:
            pass
            
        try:
            self.ui.pieChartDungXe.update_chart(
                data=type_location_count.xs("Dừng đỗ xe", level="type"),
                chart_title="Biểu đồ điểm nóng dừng đỗ xe trái phép"
            )
        except:
            pass

        try:
            self.ui.pieChartQuaTocDo.update_chart(
                data=type_location_count.xs("Quá tốc độ", level="type"),
                chart_title="Biểu đồ điểm nóng vi phạm về tốc độ"
            )
        except:
            pass
            
        try:
            self.ui.pieChartNguocChieu.update_chart(
                data=type_location_count.xs("Ngược chiều", level="type"),
                chart_title="Biểu đồ điểm nóng xảy ra đi ngược chiều"
            )
        except:
            pass
        
        
        # self.ui.lineChartVio.update_chart(
        #     data=avg_speed,
        #     date_range=date_range,
        #     chart_title="Biểu đồ tốc độ trung bình"
        # )

    @QtCore.pyqtSlot(pd.DataFrame)
    def recv_query_data(self, data: pd.DataFrame):
        self.df = data
        self.violationModel = ViolationTableModel(self.df.copy(), editable=False)
        self.sort_proxy_model.setSourceModel(self.violationModel)
        self.ui.violationTableView.setModel(self.sort_proxy_model)
        self.violationDelegate = AlignDelegate(self.ui.violationTableView)
        self.ui.violationTableView.setItemDelegate(self.violationDelegate)

        self.ui.violationTableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.ui.violationTableView.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.ui.violationTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        
        # Call showDocument for each row of the DataFrame
        # for i, data in self.df.iterrows():
        #     self.showDocument(i, data)
        
    def showDocument(self, i, data):
        icon_path = ""

        if data["type"] in self.violationModel.icons_mapping:
            icon_path = self.violationModel.icons_mapping[data["type"]]

        # Set icon data using the model
        self.violationModel.setData(self.violationModel.index(i, 0), icon_path, QtCore.Qt.DecorationRole)

        if "speed" in data and not pd.isna(data["speed"]):
            self.violationModel.setData(self.violationModel.index(i, 2), f'{int(data["speed"])}', QtCore.Qt.EditRole)
        else:
            self.violationModel.setData(self.violationModel.index(i, 2), "", QtCore.Qt.EditRole)

        dt = datetime.datetime.strptime(data["time"], "%Y-%m-%dT%H:%M:%S.%f")
        formatted_datetime = dt.strftime("%d/%m/%Y %H:%M:%S")
        self.violationModel.setData(self.violationModel.index(i, 3), formatted_datetime, QtCore.Qt.EditRole)
        self.violationModel.setData(self.violationModel.index(i, 4), data["location"], QtCore.Qt.EditRole)

    def display(self, item):
        if item.column() == 1:
            try:
                selected_index = self.ui.violationTableView.currentIndex()
                row = selected_index.row()

                from_time, to_time = self.collect_filter_datetime()
                from_time_str = from_time.isoformat(timespec='milliseconds')
                to_time_str = to_time.isoformat(timespec='milliseconds')
                
                data = self.collection.find(
                    {'time': 
                        {
                            '$gte': from_time_str,
                            '$lte': to_time_str
                        }
                    })[row]

                pathImage = data["path"]
                self.displayImage.display_image(pathImage)
                self.displayImage.show()
            except Exception as error:
                self.send_display_image_error.emit(str(error))

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
        index = self.ui.gridLayout_2.indexOf(widget)
        row, col = self.ui.gridLayout_2.getItemPosition(index)[:2]
        self.ui.gridLayout_2.addWidget(widget, row, col, rowspan, colspan)

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
