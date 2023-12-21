from __future__ import annotations

import random
import typing

import numpy as np
import pandas as pd
from PyQt5 import QtChart, QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget


class StackedVerticalBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.p = parent
        self.vlayout = QtWidgets.QVBoxLayout()        
        self.chartview = QtChart.QChartView()
        self.chartview.setParent(self)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)
        self.vlayout.addWidget(self.chartview)
        self.vlayout.setSpacing(0)
        self.vlayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.vlayout)
    
    def update_chart(self, data: pd.DataFrame, categories: list, chart_title: str = "", axisX_title: str = "", axisY_title: str = "", label_format: str = "%d"):
        # self.series = QtChart.QHorizontalStackedBarSeries()
        self.series = QtChart.QStackedBarSeries()
        
                
        for col in data.columns:
            columnSeriesObj = data[col]
            col_set = QtChart.QBarSet(col)
            col_set.append(columnSeriesObj.values)            
            self.series.append(col_set)
        
        self.chart = QtChart.QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle(chart_title)
        self.chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)
        
        axisX = QtChart.QBarCategoryAxis()
        axisX.setTitleText(axisX_title)
        if categories:
            categories = categories # data.loc[:, "CAM NAME"].to_list() # ignore cam name
            axisX.append(categories)
                
        axisY = QtChart.QValueAxis()
        axisY.setRange(0, data.to_numpy().max())
        axisY.setLabelFormat(label_format)
        axisY.setTitleText(axisY_title)
        
        self.series.setLabelsVisible(True)
        self.series.setLabelsFormat("@value")
        
        self.chart.setAxisX(axisX, self.series)
        self.chart.addAxis(axisY, Qt.AlignLeft)
        
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        
        self.chartview.setChart(self.chart)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)

class StackedHorizontalPercentBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.p = parent
        self.vlayout = QtWidgets.QVBoxLayout()        
        self.chartview = QtChart.QChartView()
        self.chartview.setParent(self)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)
        self.vlayout.addWidget(self.chartview)
        self.vlayout.setSpacing(0)
        self.vlayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.vlayout)
    
    def update_chart(self, data: pd.DataFrame, categories: list, chart_title: str = "", axisX_title: str = "", axisY_title: str = "", label_format: str = "%d"):
        # self.series = QtChart.QHorizontalStackedBarSeries()
        self.series = QtChart.QHorizontalPercentBarSeries()
        
                
        for col in data.columns:
            columnSeriesObj = data[col]
            col_set = QtChart.QBarSet(col)
            col_set.append(columnSeriesObj.values)            
            self.series.append(col_set)
        
        self.chart = QtChart.QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle(chart_title)
        self.chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)
        
        axisY = QtChart.QBarCategoryAxis()
        axisY.setTitleText(axisY_title)
        if categories:
            categories = categories # data.loc[:, "CAM NAME"].to_list() # ignore cam name
            axisY.append(categories)
        
        axisX = QtChart.QValueAxis()
        axisX.setRange(0, 100)
        axisX.setLabelFormat(label_format)
        axisX.setTitleText(axisX_title)
        
        self.series.setLabelsVisible(True)
        self.series.setLabelsFormat("@value %")
        
        self.chart.setAxisY(axisY, self.series)
        self.chart.addAxis(axisX, Qt.AlignBottom)
        
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        
        self.chartview.setChart(self.chart)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)

class CustomStackBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.p = parent
        self.step = 0.1
        self.categories = None
        
        self.minimize_font = 13
        self.maximize_font = 14
        
        self.minimize_title_font = 13
        self.maximize_title_font = 14
        
        self.minimize_size = None
        self.maximize_size = None
        
        self.bar_width_max = None
        self.bar_width_min = None
        
        self.chart = None
        
        self.label = QtWidgets.QLabel()
        
        self.vlayout = QtWidgets.QVBoxLayout()
        self.series = QtChart.QStackedBarSeries()        
        self.chartview = QtChart.QChartView()
        self.scrollbar = QtWidgets.QScrollBar(
            QtCore.Qt.Horizontal,
            sliderMoved=self.recalculate_range,
            pageStep=100
        )
        self.slider = QtWidgets.QSlider(
            QtCore.Qt.Horizontal, sliderMoved=self.recalculate_range
        )
        self.scrollbar.setRange(0, 100)
        self.scrollbar.setValue(0)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        
        self.chartview.setParent(self)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)
        self.chartview.setMouseTracking(True)
        self.vlayout.addWidget(self.label)
        self.vlayout.addWidget(self.chartview)
        self.vlayout.addWidget(self.scrollbar)
        self.vlayout.addWidget(self.slider)
        self.vlayout.setSpacing(0)
        self.vlayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.vlayout)
        self.setContentsMargins(0,0,0,0)
        self.setMouseTracking(True)
        self.label.hide()

    def no_data(self, text):
        self.chartview.hide()
        self.scrollbar.hide()
        self.slider.hide()
        self.label.setText(text)
        self.label.show()

    def clearChart(self):
        self.series.clear()

    def update_font_slice(self, default: bool = True):
        return
        current_size = self.chartview.size()
        
        if self.maximize_size is not None:
            if current_size.width() * current_size.height() > self.maximize_size.width() * self.maximize_size.height():
                self.maximize_size = current_size
        
        if default:
            if self.minimize_size is not None and self.maximize_size is not None:
                self.chartview.setMaximumSize(self.minimize_size)
                self.chartview.setMinimumSize(self.minimize_size)            
            
            font_bar = self.minimize_font
            font_title = self.minimize_title_font
        else:
            if self.maximize_size is None:
                self.maximize_size = current_size
            else:
                self.chartview.setMaximumSize(self.maximize_size)
                self.chartview.setMinimumSize(self.maximize_size)
            self.chartview.resize(self.maximize_size)
                
            font_bar = self.maximize_font
            font_title = self.maximize_title_font

        # if self.series is None: return
        
        
        
        # for slice in self.series.slices():
        #     slice.setLabelFont(font_slice)
        
        if self.chart is None: return
        
        axisX = self.chart.axisX()
        if axisX is not None:
            title_font = axisX.titleFont()
            title_font.setPointSize(font_bar)
            title_font.setBold(True)
            
            label_font = axisX.labelsFont()
            label_font.setPointSize(font_bar)
            label_font.setBold(True)
            
            axisX.setLabelsFont(label_font)
            axisX.setTitleFont(title_font)
        
        axisY = self.chart.axisY()
        if axisY is not None:
            title_font = axisY.titleFont()
            title_font.setPointSize(font_bar)
            title_font.setBold(True)
            
            label_font = axisY.labelsFont()
            label_font.setPointSize(font_bar)
            label_font.setBold(True)
            
            axisY.setLabelsFont(label_font)
            axisY.setTitleFont(title_font)
        
        if self.series is None:
            return
        
        
        markers = self.chart.legend().markers(self.series)

        for idx, barset in enumerate(self.series.barSets()):
            font_barset = barset.labelFont()
            font_barset.setPointSize(font_bar)
            barset.setLabelFont(font_barset)
            
            font_marker = markers[idx].font()
            font_marker.setPointSize(font_bar)
            
            markers[idx].setFont(font_marker)
        
        font = self.chart.titleFont()
        font.setPointSize(font_title)
        font.setBold(True)
        self.chart.setTitleFont(font)

    def setBar(self, percent=False):
        if percent:
            self.series = QtChart.QPercentBarSeries()
        else:
            self.series = QtChart.QStackedBarSeries()

    def update_chart(self, data: pd.DataFrame, categories: list, chart_title: str = "", axisX_title: str = "", axisY_title: str = "", label_format: str = "%d", series_label_format="@value", label_angle=0):
        self.clearChart()
        for item in [self.chartview, self.slider, self.scrollbar]:
            if not item.isVisible():
                item.show()
        self.label.hide()
        
        self.categories = categories
        self.series = QtChart.QStackedBarSeries()
        
        self.current_min_val = 0
        self.current_max_val = len(categories) - 1
        
        for col in data.columns:
            columnSeriesObj = data[col]
            col_set = QtChart.QBarSet(col)
            col_set.append(columnSeriesObj.values)           
            self.series.append(col_set)

        font = QtGui.QFont()
        font.setPointSize(self.minimize_font)

        self.chart = QtChart.QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle(chart_title)
        
        font_title = self.chart.titleFont()
        # font_title.setPixelSize(self.minimize_title_font)
        font_title.setBold(True)
        self.chart.setTitleFont(font_title)
        
        self.chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)
        
        axisX = QtChart.QBarCategoryAxis()
        axisX.setTitleText(axisX_title)
        axisX.setLabelsAngle(label_angle)
        
        title_font = axisX.titleFont()
        # title_font.setPointSize(self.minimize_font)
        title_font.setBold(True)
        
        label_font = axisX.labelsFont()
        # label_font.setPointSize(self.minimize_font)
        # label_font.setBold(True)
        
        # axisX.setLabelsFont(label_font)
        axisX.setTitleFont(title_font)

        if categories:
            categories = categories # data.loc[:, "CAM NAME"].to_list() # ignore cam name
            axisX.append(categories)
                
        axisY = QtChart.QValueAxis()
        axisY.setRange(0, data.to_numpy().sum(axis=1).max())
        axisY.setLabelFormat(label_format)
        axisY.setTitleText(axisY_title)
        
        title_font = axisY.titleFont()
        # title_font.setPointSize(self.minimize_font)
        title_font.setBold(True)
        
        label_font = axisY.labelsFont()
        # label_font.setPointSize(self.minimize_font)
        label_font.setBold(True)
        
        # axisY.setLabelsFont(label_font)
        axisY.setTitleFont(title_font)

        self.series.setLabelsVisible(True)
        self.series.setLabelsFormat(series_label_format)
        self.series.setLabelsPosition(QtChart.QAbstractBarSeries.LabelsPosition.LabelsCenter)
        
        self.chart.setAxisX(axisX, self.series)
        self.chart.addAxis(axisY, Qt.AlignLeft)
        
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignRight)
        
        self.chartview.setChart(self.chart)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)
        
        self.series.hovered.connect(self.showToolTips)

        self.lims = np.array([0, len(categories) - 1])
        
        markers = self.chart.legend().markers(self.series)
        
        for idx, barset in enumerate(self.series.barSets()):
            font_barset = barset.labelFont()
            # font_barset.setPointSize(self.minimize_font)
            barset.setLabelFont(font_barset)
            
            font_marker = markers[idx].font()
            # font_marker.setPointSize(self.minimize_font)
            
            markers[idx].setFont(font_marker)
        
        if self.bar_width_min is None:
            self.bar_width_min = self.series.barWidth()
        
        if self.minimize_size is None:
            self.minimize_size = self.chartview.size()
    
    def showToolTips(self, status: bool, index: int, barset: QtChart.QBarSet):
        if status:
            text = "{}: {}".format(barset.label(), int(barset.at(index)))
            self.chartview.setToolTip(text)

    def recalculate_range(self):
        if self.categories is None:
            return 
        zoom_ratio = self.slider.sliderPosition() / (
            self.slider.maximum() * 1.001)
        step = 1 - zoom_ratio
        pan_level = self.scrollbar.sliderPosition() * zoom_ratio / self.scrollbar.maximum()
        min_chart = pan_level * (len(self.categories) - 1)
        if self.scrollbar.sliderPosition() == self.scrollbar.maximum():
            max_chart = len(self.categories) - 1
        else:
            max_chart = (len(self.categories) - 1) * step + min_chart
        
        if self.chart.axisX() is not None:
            self.chart.axisX().setRange(self.categories[int(min_chart)], self.categories[int(max_chart)])



class CustomPieChart(QtWidgets.QWidget):
    def __init__(self, parent: QWidget | None = ...) -> None:
        super().__init__(parent=parent)
        self.p = parent        
        
        self.minimize_font = 13

        self.maximize_font = 14
        
        self.minimize_title_font = 13
        
        self.maximize_title_font = 14
                
        self.maximize_size = None
        self.minimize_size = None
        self.max_id = None
        
        self.chart = None
        self.vlayout = QtWidgets.QVBoxLayout()
        self.series = QtChart.QPieSeries()      
        self.chartview = QtChart.QChartView()
        self.chartview.setParent(self)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)
        self.vlayout.addWidget(self.chartview)
        self.vlayout.setSpacing(0)
        self.vlayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.vlayout)
        self.setContentsMargins(0,0,0,0)

    def clearChart(self):
        self.series.clear()

    def update_font_slice(self, default: bool = True):        
        return
        current_size = self.chartview.size()
        
        if self.maximize_size is not None:
            if current_size.width() * current_size.height() > self.maximize_size.width() * self.maximize_size.height():
                self.maximize_size = current_size
        
        if default:
            if self.minimize_size is not None and self.maximize_size is not None:
                self.chartview.setMaximumSize(self.minimize_size)
                self.chartview.setMinimumSize(self.minimize_size)            
            
            font_slice = self.minimize_font
            font_title = self.minimize_title_font
        else:
            if self.maximize_size is None:
                self.maximize_size = current_size
            else:
                self.chartview.setMaximumSize(self.maximize_size)
                self.chartview.setMinimumSize(self.maximize_size)
            self.chartview.resize(self.maximize_size)
                
            font_slice = self.maximize_font
            font_title = self.maximize_title_font
       
        if self.chart is None: return
        
        font = self.chart.titleFont()
        font.setPointSize(font_title)
        font.setBold(True)
        self.chart.setTitleFont(font)

        markers = self.chart.legend().markers(self.series)
        
        if self.series is None: return
        
        for idx, slice in enumerate(self.series.slices()):
            font_s = slice.labelFont()
            font_s.setPointSize(font_slice)
            slice.setLabelFont(font_s)
            
            font_m = markers[idx].font()
            font_m.setPointSize(font_slice)
            if self.max_id is not None:
                if self.max_id == idx:
                    font_m.setBold(True)

            markers[idx].setFont(font_m)

    def update_chart(self, data: pd.Series, chart_title: str):
        self.clearChart()
        self.series = QtChart.QPieSeries()
        for type_name in data.keys():
            self.series.append(type_name, data[type_name])

        list_val = data.to_list()
        self.max_id = np.argmax(list_val)
        
        self.series.setLabelsVisible(True)        

        self.chart = QtChart.QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle(chart_title)
        
        font = self.chart.titleFont()
        # font.setPointSize(self.minimize_title_font)
        font.setBold(True)
        self.chart.setTitleFont(font)
        
        self.chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)
        
        self.chartview.setChart(self.chart)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)

        markers = self.chart.legend().markers(self.series)
        for idx, slice in enumerate(self.series.slices()):
            self.chart.legend().markers(self.series)[idx].setLabel(slice.label())
            font_s = slice.labelFont()
            # font_s.setPointSize(self.minimize_font)
            slice.setLabelFont(font_s)
            
            font_m = markers[idx].font()
            # font_m.setPointSize(self.minimize_font)
            
            if idx == self.max_id:
                slice.setLabel("{} ({:.1f}%)".format(int(slice.value()), slice.percentage() * 100))
                slice.setExploded()
                slice.setLabelVisible()
                slice.setPen(QtGui.QPen(Qt.darkRed, 2))
                slice.setBrush(Qt.green)
                slice.setLabelPosition(QtChart.QPieSlice.LabelPosition.LabelInsideHorizontal)
                font_m.setBold(True)
                markers[idx].setFont(font_m)
            else:
                font_m.setBold(False)
                markers[idx].setFont(font_m)
                slice.setLabelVisible(False)
            
            markers[idx].clicked.connect(self.handleMarkerClicked)
        
        self.chart.legend().setAlignment(Qt.AlignRight)
        
        self.series.hovered.connect(self.showToolTips)
        self.series.clicked.connect(self.handleSeriesClicked)
        
        if self.minimize_size is None:
            self.minimize_size = self.chartview.size()

    def handleSeriesClicked(self, slice: QtChart.QPieSlice):
        series = self.sender()
        slice.setLabel("{} ({:.1f}%)".format(int(slice.value()), slice.percentage() * 100))
        
        slice_index = series.slices().index(slice)
        marker = self.chart.legend().markers(series)[slice_index]
        if slice.isLabelVisible():
            slice.setLabelVisible(False)
            font = slice.labelFont()
            font.setBold(False)
            marker.setFont(font)
        else:
            slice.setLabelVisible(True)
            font = slice.labelFont()
            font.setBold(True)
            marker.setFont(font)

    def handleMarkerClicked(self):
        marker = self.sender()
        index = self.chart.legend().markers(self.series).index(marker)
        slice = self.series.slices()[index]
        slice.setLabel("{} ({:.1f}%)".format(int(slice.value()), slice.percentage() * 100))
        if slice.isLabelVisible():
            font = slice.labelFont()
            font.setBold(False)
            marker.setFont(font)
            slice.setLabelVisible(False)
        else:
            font = slice.labelFont()
            font.setBold(True)
            marker.setFont(font)
            slice.setLabelVisible(True)

    def showToolTips(self, slice: QtChart.QPieSlice, state: bool):
        if state:
            text = "{} ({:.1f}%)".format(int(slice.value()), slice.percentage() * 100)
            self.chartview.setToolTip(text)

class CustomLineChart(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.p = parent
        
        self.scat_series_lst = []
        self.line_series_lst = []
        
        self.marker_series_dict = {}
        self.map_name_to_line = {}
        
        self.stored_scatter = {}
        self.stored_line = {}
        
        self.color_palette = []

        self.date_range = None

        self.step = 0.1

        self.scrollbar = QtWidgets.QScrollBar(
            QtCore.Qt.Horizontal,
            sliderMoved=self.recalculate_range,
            pageStep=100,
        )
        self.slider = QtWidgets.QSlider(
            QtCore.Qt.Horizontal, sliderMoved=self.recalculate_range
        )
        self.scrollbar.setRange(0, 100)
        self.scrollbar.setValue(0)
        self.scrollbar.setPageStep(100)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)

        self.vlayout = QtWidgets.QVBoxLayout()
        self.chart = QtChart.QChart()
        self.chartview = QtChart.QChartView()
        self.chartview.setParent(self)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)
        self.vlayout.addWidget(self.chartview)
        self.vlayout.addWidget(self.scrollbar)
        self.vlayout.addWidget(self.slider)
        self.vlayout.setSpacing(0)
        self.vlayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.vlayout)

    def clearChart(self):
        self.stored_scatter.clear()
        self.marker_series_dict.clear()
        self.color_palette.clear()
        self.scat_series_lst.clear()
        self.line_series_lst.clear()
        self.map_name_to_line.clear()
        self.date_range = None
        self.chart.removeAllSeries()

    def update_chart(self, data: pd.Series, date_range: list[str], chart_title: str = ""):
        self.clearChart()
        self.date_range = date_range     
        locations = [loc for loc in data.index.get_level_values("location").unique()]

        while len(self.color_palette) < len(locations):
            R = random.randint(0, 255)
            G = random.randint(0, 255)
            B = random.randint(0, 255)
            color = QtGui.QColor(R, G, B)
            self.color_palette.append(color)

        self.chart = QtChart.QChart()
        self.chart.setTitle(chart_title)
        font = QtGui.QFont()
        font.setPixelSize(14)
        font.setBold(True)
        self.chart.setTitleFont(font)
        self.chart.createDefaultAxes()
        self.chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        for i, loc in enumerate(locations):
            data_loc = data.xs(loc, level="location")
            scat_series = QtChart.QScatterSeries()
            scat_series.setName(loc)
            scat_series.setColor(self.color_palette[i])
            
            line_series = QtChart.QLineSeries()
            line_series.setName(loc)
            line_series.setColor(self.color_palette[i])
            
            for idx, date in enumerate(date_range):
                if date in data_loc:
                    scat_series.append(idx, data_loc[date])
                    line_series.append(idx, data_loc[date])
                else:
                    line_series.append(idx, 0)
                scat_series.hovered.connect(self.showToolTips)

            self.scat_series_lst.append(scat_series)
            self.line_series_lst.append(line_series)
            
            self.chart.addSeries(scat_series)
            self.chart.addSeries(line_series)
        
        axisX = QtChart.QBarCategoryAxis()
        axisX.append(date_range)
        axisX.setLabelsAngle(80)
        
        axisY = QtChart.QValueAxis()
        axisY.setRange(0, data.max() + 100)
        axisY.setLabelFormat("%d")
        axisY.setTickCount(10)
                
        self.chart.addAxis(axisX, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(axisY, QtCore.Qt.AlignmentFlag.AlignLeft)
        
        self.chart.legend().setVisible(True)
        
        self.chart.axisX().setTitleText("Thời gian (năm-tháng-ngày giờ)")
        self.chart.axisX().setGridLineVisible(True)
        self.chart.axisY().setTitleText("Tốc độ trung bình")
        self.chart.axisY().setGridLineVisible(True)
        
        legend = self.chart.legend()
        legend.setMarkerShape(QtChart.QLegend.MarkerShapeCircle)
        font = QtGui.QFont()
        font.setPointSize(12)
        legend.setFont(font)
        legend.setAlignment(Qt.AlignRight)
        
        for i in range(len(locations)):
            series_name = self.scat_series_lst[i].name()
            
            scat_marker = self.chart.legend().markers(self.scat_series_lst[i])[0]
            line_marker = self.chart.legend().markers(self.line_series_lst[i])[0]

            line_marker.setVisible(False)
            line_marker.setBrush(self.color_palette[i])
            self.map_name_to_line[series_name] = self.line_series_lst[i]

            scat_marker.setVisible(True)
            scat_marker.setLabel(series_name)
            scat_marker.setBrush(self.color_palette[i % len(locations)])
            scat_marker.clicked.connect(self.handleMarkerClicked)
            self.marker_series_dict[scat_marker] = self.scat_series_lst[i]
            
            self.scat_series_lst[i].attachAxis(axisX)
            self.scat_series_lst[i].attachAxis(axisY)
            
            self.line_series_lst[i].attachAxis(axisX)
            self.line_series_lst[i].attachAxis(axisY)
                        
        self.chartview.setChart(self.chart)
        self.chartview.setRenderHint(QtGui.QPainter.Antialiasing)

    def showToolTips(self, point: typing.Union[QtCore.QPointF, QtCore.QPoint], state: bool):
        if state:
            text = f"Value: {int(point.y())}"
            self.chartview.setToolTip(text)
  
    def handleMarkerClicked(self):
        marker = self.sender()
    
        scat_series = self.marker_series_dict[marker]
        location = scat_series.name()
        line_series = self.map_name_to_line[location]
        
        if scat_series.count() > 0:
            self.stored_scatter[location] = scat_series.pointsVector()
            self.stored_line[location] = line_series.pointsVector()
            scat_series.clear()
            marker.setBrush(QtGui.QBrush(QtCore.Qt.gray))
            line_series.clear()
        else:
            for point in self.stored_scatter[location]:
                scat_series.append(point)
            for point in self.stored_line[location]:
                line_series.append(point)
            marker.setBrush(scat_series.color())
        
        self.chart.legend().update()

    def recalculate_range(self):
        if self.date_range is None:
            return
        zoom_ratio = self.slider.sliderPosition() / (
            self.slider.maximum() * 1.001)
        step = 1 - zoom_ratio
        pan_level = self.scrollbar.sliderPosition() * zoom_ratio / self.scrollbar.maximum()
        min_chart = pan_level * (len(self.date_range) - 1)
        
        if self.scrollbar.sliderPosition() == self.scrollbar.maximum():
            max_chart = len(self.date_range) - 1
        else:
            max_chart = (len(self.date_range) - 1) * step + min_chart
        
        extra_space = len(self.date_range) - (max_chart - min_chart + 1)
        page_step = 100 - extra_space
        self.scrollbar.setPageStep(int(page_step))