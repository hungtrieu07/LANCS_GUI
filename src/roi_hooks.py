from __future__ import annotations

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from src.roi_selector import (CURSOR_DEFAULT, CURSOR_DRAW, CURSOR_GRAB,
                              CURSOR_MOVE, CURSOR_POINT, ROISelector,
                              nearest_point, override_cursor)
from src.YOLO_detector import Detector


# Base hook
class Hooks(QtCore.QObject):
    def __init__(self, *args, **kwargs):
        super(Hooks, self).__init__(*args, **kwargs)
        ...

    def on_mousePressEvent(self, roi_selector: ROISelector, ev: QtGui.QMouseEvent):
        ...

    def on_mouseMoveEvent(self, roi_selector: ROISelector, ev: QtGui.QMouseEvent):
        ...

    def on_mouseReleaseEvent(self, roi_selector: ROISelector, ev: QtGui.QMouseEvent):
        ...

    def on_mouseDoubleClickEvent(
        self, roi_selector: ROISelector, ev: QtGui.QMouseEvent
    ):
        ...

    def on_paintEvent(
        self, roi_selector: ROISelector, painter: QtGui.QPainter, a0: QtGui.QPaintEvent
    ):
        ...

    def on_resizeEvent(self, roi_selector: ROISelector, a0: QtGui.QResizeEvent):
        ...

    def load_data(self, points: list):
        ...

    def clear(self):
        ...


"""
ROI hook to draw and edit ROI on Select ROi Window
"""


class ROI_Hook(Hooks):
    send_point_coord = QtCore.pyqtSignal(np.ndarray, list)

    def __init__(self, server_ip_combo, *args, **kwargs):
        super(ROI_Hook, self).__init__(*args, **kwargs)
        self.server_ip_combo = server_ip_combo
        self.roi_points = []
        self.norm_points = []
        self.MODE_EDIT = False
        self.found = False
        self.is_point_selected = False
        self.track_point_movement = None
        self.roi_painter_path = QtGui.QPainterPath()

        self.lane_points = []
        self.norm_lane_points = []

        self.lane_check_ss = []
        self.norm_lane_check_ss = []
        self.detector = Detector(f"http://{self.server_ip_combo}:8080/predictions/LaneDetection")

        self.prev_roi_point = 0

    def load_data(self, points: list[QtCore.QPoint | QtCore.QPointF], w: int, h: int):
        qp_lst = [QtCore.QPointF(p[0], p[1]) for p in points]
        self.norm_points = qp_lst
        self.roi_points.clear()
        for point in self.norm_points:
            x = int(point.x() * w)
            y = int(point.y() * h)
            self.roi_points.append(QtCore.QPoint(x, y))

    def clear(self, roi_selector: ROISelector):
        self.roi_points.clear()
        self.roi_painter_path.clear()
        self.MODE_EDIT = False
        self.found = False
        override_cursor(CURSOR_DRAW)
        self.send_point_coord.emit(roi_selector.image_arr, self.roi_points)

        self.prev_roi_point = 0
        self.lane_points.clear()
        self.lane_check_ss.clear()

    def on_mouseDoubleClickEvent(
        self, roi_selector: ROISelector, ev: QtGui.QMouseEvent
    ):
        if ev.button() == Qt.LeftButton:
            if len(self.roi_points) < 4:
                self.roi_points.append(ev.pos())

    def on_mousePressEvent(self, roi_selector: ROISelector, ev: QtGui.QMouseEvent):
        if ev.button() == Qt.LeftButton:
            if self.MODE_EDIT and self.found:
                self.is_point_selected = True

    def on_mouseReleaseEvent(self, roi_selector: ROISelector, ev: QtGui.QMouseEvent):
        if ev.button() == Qt.LeftButton:
            if self.MODE_EDIT:
                self.is_point_selected = False

    def on_mouseMoveEvent(self, roi_selector: ROISelector, ev: QtGui.QMouseEvent):
        self.track_point_movement = ev.pos()

        len_roi_points = len(self.roi_points)
        len_lane_points = len(self.lane_points) * 2
        # len_check_ss = (len(self.lane_check_ss) * 2)

        lst_points = []
        lst_points.extend(self.roi_points)
        lst_points.extend(self.flatten_qp_lst(self.lane_points))
        lst_points.extend(self.flatten_qp_lst(self.lane_check_ss))

        if self.MODE_EDIT:
            # Find nearest point
            self.found, closest_ind, _ = nearest_point(
                ev.pos(), lst_points=lst_points, threshold=20
            )
            # found_lane, closest_ind_lane, closest_dist_lane = nearest_point(ev.pos(), lst_points=self.flatten_qp_lst(self.lane_points), threshold=12)

            if self.found:
                override_cursor(CURSOR_GRAB)

            if self.is_point_selected and self.found:
                override_cursor(CURSOR_MOVE)
                if closest_ind < len_roi_points:
                    self.roi_points[closest_ind] = self.track_point_movement
                if len_roi_points <= closest_ind < (len_roi_points + len_lane_points):
                    self.lane_points[(closest_ind - len_roi_points) // 2][
                        (closest_ind - len_roi_points) % 2
                    ] = self.track_point_movement
                if (len_roi_points + len_lane_points) <= closest_ind:
                    self.lane_check_ss[(closest_ind - len_roi_points - len_lane_points)//2][(closest_ind - len_roi_points - len_lane_points)%2] = self.track_point_movement
    
    def on_paintEvent(self, roi_selector: ROISelector, painter: QtGui.QPainter, a0: QtGui.QPaintEvent):
        if not self.MODE_EDIT:
            if not self.found and not self.is_point_selected:
                override_cursor(CURSOR_DRAW)
              
            if len(self.roi_points) <= 0:
                return

            if self.track_point_movement is not None:
                first_point, latest_point = self.roi_points[0], self.roi_points[-1]
                painter.setPen(
                    QtGui.QPen(QtGui.QColor(227, 150, 62), 3, style=Qt.DotLine)
                )
                painter.drawLines([first_point, self.track_point_movement])
                painter.drawLines([latest_point, self.track_point_movement])

            painter.setPen(QtGui.QPen(Qt.black, 1, cap=Qt.RoundCap))
            polygon = QtGui.QPolygonF(self.roi_points)
            self.roi_painter_path.addPolygon(polygon)
            painter.drawPath(self.roi_painter_path)

        if len(self.roi_points) == 4:
            self.roi_painter_path.clear()
            brush = QtGui.QBrush()
            brush.setStyle(Qt.Dense7Pattern)
            painter.setBrush(brush)
            polygon = QtGui.QPolygonF(self.roi_points)
            painter.drawPolygon(polygon)
            if not self.found:
                override_cursor(CURSOR_DEFAULT)

            self.send_point_coord.emit(
                roi_selector.image_arr,
                roi_selector.cv_norm_point_to_lst(self.roi_points),
            )
            if not self.MODE_EDIT:
                lst_lane, check_ss = self.detector.auto_lane(
                    roi_selector.image_arr,
                    roi_selector.cv_norm_point_to_lst(self.roi_points),
                    num_lane=2,
                )

                if len(self.lane_points) <= 0:
                    self.lane_points = self.cv_lst_norm_to_qp(
                        lst_lane,
                        width=roi_selector.rect().width(),
                        height=roi_selector.rect().height(),
                    )

                if len(self.lane_check_ss) <= 0:
                    self.lane_check_ss = self.cv_lst_norm_to_qp(
                        check_ss,
                        width=roi_selector.rect().width(),
                        height=roi_selector.rect().height(),
                    )

            if len(self.lane_points) > 0:
                for qp_pair in self.lane_points:
                    painter.setPen(QtGui.QPen(Qt.blue, 1, cap=Qt.RoundCap))
                    painter.drawLines(qp_pair)

            if len(self.lane_check_ss) > 0:
                for qp_pair in self.lane_check_ss:
                    painter.setPen(QtGui.QPen(Qt.red, 1, cap=Qt.RoundCap))
                    painter.drawLines(qp_pair)

            self.MODE_EDIT = True

        painter.setPen(QtGui.QPen(Qt.green, 10, cap=Qt.RoundCap))
        painter.drawPoints(self.roi_points)
        painter.drawPoints(self.flatten_qp_lst(self.lane_points))
        painter.drawPoints(self.flatten_qp_lst(self.lane_check_ss))

    def on_resizeEvent(self, roi_selector: ROISelector, a0: QtGui.QResizeEvent):
        w, h = roi_selector.rect().width(), roi_selector.rect().height()
        if len(self.norm_points) <= 0: return
        self.roi_points.clear()
        for point in self.norm_points:
            x = int(point.x() * w)
            y = int(point.y() * h)
            self.roi_points.append(QtCore.QPoint(x, y))

        if len(self.norm_lane_points) <= 0:
            return
        self.lane_points.clear()
        for point in self.norm_lane_points:
            x1 = int(point[0].x() * w)
            y1 = int(point[0].y() * h)
            x2 = int(point[1].x() * w)
            y2 = int(point[1].y() * h)
            self.lane_points.append([QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2)])

        if len(self.norm_lane_check_ss) <= 0:
            return
        self.lane_check_ss.clear()
        for point in self.norm_lane_check_ss:
            x1 = int(point[0].x() * w)
            y1 = int(point[0].y() * h)
            x2 = int(point[1].x() * w)
            y2 = int(point[1].y() * h)
            self.lane_check_ss.append([QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2)])

    def flatten_qp_lst(
        self, points: list[list[QtCore.QPoint | QtCore.QPointF]]
    ) -> list[QtCore.QPoint | QtCore.QPointF]:
        flat_lst = []
        for qp_pair in points:
            flat_lst.extend(qp_pair)

        return flat_lst

    def cv_lst_norm_to_qp(
        self, points: list, width: int, height: int
    ) -> list[list[QtCore.QPoint]]:
        qp_lst = []
        if len(points) > 0:
            for pair in points:
                qp1 = QtCore.QPoint(pair[0] * width, pair[1] * height)
                qp2 = QtCore.QPoint(pair[2] * width, pair[3] * height)
                qp_lst.append([qp1, qp2])
        return qp_lst

    def cv_lst_qp_norm(self, points: list):
        self.norm_lane_points.clear()
        for pair in points:
            qp1 = QtCore.QPointF(pair[0], pair[1])
            qp2 = QtCore.QPointF(pair[2], pair[3])
            self.norm_lane_points.append([qp1, qp2])


class Lane_Hook(Hooks):
    def __init__(self, *args, **kwargs):
        super(Lane_Hook, self).__init__(*args, **kwargs)
        self.lane_points = []
        self.denorm_points = []
        self.is_point_selected = False
        self.found = False
        self.track_point_movement = None

    def load_data(self, points: list):
        self.denorm_points.clear()
        for pair in points:
            qp1 = QtCore.QPointF(pair[0], pair[1])
            qp2 = QtCore.QPointF(pair[2], pair[3])
            self.denorm_points.append([qp1, qp2])

    def on_mousePressEvent(self, roi_selector: ROISelector, ev: QtGui.QMouseEvent):
        if ev.button() == Qt.LeftButton:
            if self.found:
                self.is_point_selected = True

    def on_mouseReleaseEvent(self, roi_selector: ROISelector, ev: QtGui.QMouseEvent):
        if ev.button() == Qt.LeftButton:
            if self.found:
                self.is_point_selected = False

    def on_mouseMoveEvent(self, roi_selector: ROISelector, ev: QtGui.QMouseEvent):
        self.track_point_movement = ev.pos()

        # Find nearest point
        self.found, self.closest_ind = nearest_point(
            ev.pos(), lst_points=self.flatten_qp_lst(self.lane_points), threshold=15
        )
        if self.found:
            override_cursor(CURSOR_GRAB)

        if self.is_point_selected and self.found:
            override_cursor(CURSOR_MOVE)
            self.lane_points[self.closest_ind // 2][
                self.closest_ind % 2
            ] = self.track_point_movement

    def on_paintEvent(
        self, roi_selector: ROISelector, painter: QtGui.QPainter, a0: QtGui.QPaintEvent
    ):
        for qp in self.lane_points:
            painter.setPen(QtGui.QPen(Qt.blue, 1, cap=Qt.RoundCap))
            painter.drawLines(qp)
            painter.setPen(QtGui.QPen(Qt.red, 10, cap=Qt.RoundCap))
            painter.drawPoints(qp)

        roi_selector.update()

    def on_resizeEvent(self, roi_selector: ROISelector, a0: QtGui.QResizeEvent):
        if len(self.denorm_points) <= 0:
            return
        self.lane_points.clear()
        w, h = roi_selector.rect().width(), roi_selector.rect().height()
        for point in self.denorm_points:
            x1 = int(point[0].x() * w)
            y1 = int(point[0].y() * h)
            x2 = int(point[1].x() * w)
            y2 = int(point[1].y() * h)
            self.lane_points.append([QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2)])

    def clear(self, roi_selector: ROISelector):
        self.is_point_selected = False
        self.found = False
        self.track_point_movement = None
        self.lane_points.clear()

    def cv_lst_to_qp(self, points: list) -> list[list[QtCore.QPoint | QtCore.QPointF]]:
        qp_lst = []
        for point in points:
            qp_lst.append(
                [QtCore.QPoint(point[0], point[1]), QtCore.QPoint(point[2], point[3])]
            )

        return qp_lst

    def flatten_qp_lst(
        self, points: list[list[QtCore.QPoint | QtCore.QPointF]]
    ) -> list[QtCore.QPoint | QtCore.QPointF]:
        flat_lst = []
        for qp_pair in points:
            flat_lst.extend(qp_pair)

        return flat_lst
