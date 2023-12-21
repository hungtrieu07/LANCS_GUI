from __future__ import annotations

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from scipy.spatial import distance as dist


class ROISelectorOld(QtWidgets.QLabel):
    finish_select_point = QtCore.pyqtSignal(list)

    def __init__(self, arr: np.ndarray = None, parent=None):
        super(ROISelectorOld, self).__init__(parent)
        self.p = parent
        if arr is None:
            self.arr_pixmap = self.convert_cv_qt(np.zeros(shape=(self.size().height(), self.size().width(), 3), dtype=np.uint8))
        else:
            self.arr_pixmap = self.convert_cv_qt(arr)
        
        self.setContentsMargins(0,0,0,0)
        self.setMouseTracking(True)
        
        self.override_cursor(CURSOR_DRAW)
        
        self.roi_points = []
        self.roi_painter_path = QtGui.QPainterPath()
        self.roi_point_movement = None
        
        self.MODE_EDIT = False
        self.found, self.closest_ind = False, None
        
        self.selected_point = False
    
    """
    Drawing
    """
    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == Qt.LeftButton:
            if not self.is_num_roi_full():
                self.roi_points.append(a0.pos())
        
        self.update()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == Qt.LeftButton:
            if self.MODE_EDIT and self.found:
                self.selected_point = True
        
        self.update()

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == Qt.LeftButton:
            if self.MODE_EDIT:
                self.selected_point = False
        
        self.update()

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.roi_point_movement = ev.pos()
        
        if self.MODE_EDIT:
            # Find nearest point
            self.found, self.closest_ind = self.nearest_point(ev.pos(), threshold=12)
            if self.found:
                self.override_cursor(CURSOR_GRAB)

            if self.selected_point and self.found:
                self.roi_points[self.closest_ind] = self.roi_point_movement

        self.update()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.drawPixmap(self.rect(), self.arr_pixmap)
        
        if not self.MODE_EDIT:  
            if len(self.roi_points) <= 0:
                return super().paintEvent(a0)
            
            if self.roi_point_movement is not None:
                first_point, latest_point = self.roi_points[0], self.roi_points[-1]
                painter.setPen(QtGui.QPen(QtGui.QColor(227, 150, 62), 3, style=Qt.DotLine))
                painter.drawLines([first_point, self.roi_point_movement])
                painter.drawLines([latest_point, self.roi_point_movement])
                    
            painter.setPen(QtGui.QPen(Qt.black, 3, cap=Qt.RoundCap))
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
            self.MODE_EDIT = True
            if not self.found:
                self.override_cursor(CURSOR_DEFAULT)
        
        painter.setPen(QtGui.QPen(Qt.green, 10, cap=Qt.RoundCap))
        painter.drawPoints(self.roi_points)
        
        painter.end()

    """
    Functions
    """
    def nearest_point(self, current_point: QtCore.QPoint, threshold: int = 3) -> tuple[bool, int]:
        pair_dist = self.distance(current_point)
        verified_dist = pair_dist[pair_dist < threshold]
        if not np.any(verified_dist):
            found_nearest = False
            closest_point_ind = None
        else:
        # Smallest distance
            closest_point_ind = np.argmin(pair_dist, axis=1)[0]
            found_nearest = True
        return found_nearest, closest_point_ind
    
    def distance(self, current_point: QtCore.QPoint) -> np.ndarray:
        arr_point = self.cv_lst_point_to_array()
        arr_current_point = np.array([[current_point.x(), current_point.y()]], dtype=np.int32)
        pair_dist = dist.cdist(arr_current_point, arr_point, "euclidean")
        return pair_dist
    
    def cv_lst_point_to_array(self) -> np.ndarray:
        arr_points = np.zeros((len(self.roi_points), 2), dtype=np.uint32)
        for ind, qpoint in enumerate(self.roi_points):
            arr_points[ind] = [qpoint.x(), qpoint.y()]
        
        return arr_points
    
    def is_num_roi_full(self) -> bool:
        return len(self.roi_points) >= 4
    
    def get_point(self) -> list:
        return self.roi_points

    def load_data(self, image_arr: np.ndarray, points: list[float]) -> None:
        self.image_arr = image_arr.copy()
        self.arr_pixmap = self.convert_cv_qt(image_arr)
        self.setPixmap(self.arr_pixmap)
        self.setScaledContents(True)
        
        # if len(points) > 0:
        #     self.points = points
        #     w, h = self.rect().width(), self.rect().height()
        #     self.polygon.clear()
        #     qpoint = QtCore.QPoint()
        #     for point in self.points:
        #         x = int(point[0] * w)
        #         y = int(point[1] * h)
        #         qpoint.setX(x)
        #         qpoint.setY(y) 
        #         self.polygon << qpoint
        
        self.update()

    def current_cursor(self):
        cursor = QtWidgets.QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def override_cursor(self, cursor):
        self._cursor = cursor
        if self.current_cursor() is None:
            QtWidgets.QApplication.setOverrideCursor(cursor)
        else:
            QtWidgets.QApplication.changeOverrideCursor(cursor)

    def convert_cv_qt(self, cv_img: np.ndarray) -> QtGui.QPixmap:
        """Convert from an numpy array to QPixmap"""
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        p = QtGui.QImage(cv_img.data, w, h, bytes_per_line, QtGui.QImage.Format_BGR888)
        min_w = min(p.width(), self.maximumWidth())
        min_h = min(p.height(), self.maximumHeight())
        p = p.scaled(min_w, min_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        return QtGui.QPixmap.fromImage(p)
    
    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.override_cursor(CURSOR_DEFAULT)

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor

"""
Helper functions
"""
def current_cursor():
    cursor = QtWidgets.QApplication.overrideCursor()
    if cursor is not None:
        cursor = cursor.shape()
    return cursor

def override_cursor(cursor):
    if current_cursor() is None:
        QtWidgets.QApplication.setOverrideCursor(cursor)
    else:
        QtWidgets.QApplication.changeOverrideCursor(cursor)

def cv_lst_point_to_array(lst_points: list[QtCore.QPoint]) -> np.ndarray:
    if len(lst_points) <= 0: return
    arr_points = np.zeros((len(lst_points), 2), dtype=np.uint32)
    for ind, qpoint in enumerate(lst_points):
        arr_points[ind] = [qpoint.x(), qpoint.y()]
    
    return arr_points

def distance(current_point: QtCore.QPoint, lst_points: list[QtCore.QPoint]) -> np.ndarray:
    arr_point = cv_lst_point_to_array(lst_points)
    if arr_point is None: return
    arr_current_point = np.array([[current_point.x(), current_point.y()]], dtype=np.int32)
    pair_dist = dist.cdist(arr_current_point, arr_point, "euclidean")
    return pair_dist

def nearest_point(current_point: QtCore.QPoint, lst_points: list[QtCore.QPoint], threshold: int = 3) -> tuple[bool, int]:
    pair_dist = distance(current_point, lst_points)
    if pair_dist is None: return False, None, None
    verified_dist = pair_dist[pair_dist < threshold]
    if not np.any(verified_dist):
        found_nearest = False
        closest_point_ind = None
        closest_dist = None
    else:
    # Smallest distance
        closest_point_ind = np.argmin(pair_dist, axis=1)[0]
        found_nearest = True
        closest_dist = pair_dist[:, closest_point_ind]
    return found_nearest, closest_point_ind, closest_dist



class ROISelector(QtWidgets.QLabel):
    # send_selected_point = QtCore.pyqtSignal(np.ndarray, list)
    
    def __init__(self, *args, image_arr: np.ndarray = None, hooks: list = [], **kwargs):
        super().__init__(*args, **kwargs)
        
        if image_arr is None:
            self.image_arr = np.zeros(shape=(self.size().height(), self.size().width(), 3), dtype=np.uint8)
            self.arr_pixmap = self.convert_cv_qt(self.image_arr)
        else:
            self.image_arr = image_arr
            self.arr_pixmap = self.convert_cv_qt(self.image_arr)
        
        self.setContentsMargins(0,0,0,0)
        self.setMouseTracking(True)
        
        override_cursor(CURSOR_DRAW)
        
        self.hooks = hooks

    """
    Events method
    """
    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.on_mouseDoubleClickEvent(a0)
        self.update()
    
    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.on_mousePressEvent(ev)
        self.update()

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.on_mouseReleaseEvent(ev)
        self.update()

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.on_mouseMoveEvent(ev)
        self.update()
    
    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.drawPixmap(self.rect(), self.arr_pixmap)
        
        self.on_paintEvent(painter, a0)
        
        painter.end()
    
    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.on_resizeEvent(a0)
        self.update()

    """
    Hooks and cb
    """
    def on_mousePressEvent(self, ev: QtGui.QMouseEvent):
        if not self.check_hook_exists(): return
        for hook in self.hooks:
            hook.on_mousePressEvent(self, ev)
    
    def on_mouseMoveEvent(self, ev: QtGui.QMouseEvent):
        if not self.check_hook_exists(): return
        for hook in self.hooks:
            hook.on_mouseMoveEvent(self, ev)
    
    def on_mouseReleaseEvent(self, ev: QtGui.QMouseEvent):
        if not self.check_hook_exists(): return
        for hook in self.hooks:
            hook.on_mouseReleaseEvent(self, ev)
    
    def on_mouseDoubleClickEvent(self, ev: QtGui.QMouseEvent):
        if not self.check_hook_exists(): return
        for hook in self.hooks:
            hook.on_mouseDoubleClickEvent(self, ev)
    
    def on_paintEvent(self, painter: QtGui.QPainter, a0: QtGui.QPaintEvent):
        if not self.check_hook_exists(): return
        for hook in self.hooks:
            hook.on_paintEvent(self, painter, a0)

    def on_resizeEvent(self, a0: QtGui.QResizeEvent):
        if not self.check_hook_exists(): return
        for hook in self.hooks:
            hook.on_resizeEvent(self, a0)

    def clear(self):
        for hook in self.hooks:
            hook.clear(self)
        
        self.update()

    """
    Functions
    """
    def append_hook(self, hook):
        self.hooks.append(hook)
    
    def check_hook_exists(self):
        return len(self.hooks) > 0

    def get_hook_signal(self, hook_name: str, signal_name: str) -> QtCore.pyqtSignal:
        for hook in self.hooks:
            if type(hook).__name__ == hook_name:
                if hasattr(hook, signal_name):
                    return getattr(hook, signal_name)
        
        assert f"No {hook_name} in hooks. All hooks available: {[type(hook).__name__ for hook in self.hooks]}"

    def load_data(self, image_arr: np.ndarray, points: list[float], hook_name: str) -> None:
        self.image_arr = image_arr.copy()
        self.arr_pixmap = self.convert_cv_qt(image_arr)
        self.setPixmap(self.arr_pixmap)
        self.setScaledContents(True)
        
        width = self.rect().width()
        height = self.rect().height()
        
        if len(points) > 0:
            for hook in self.hooks:
                if type(hook).__name__ == hook_name:
                    hook.load_data(points, width, height)
        
        # del loaded_points
        self.update()

    def cv_norm_point_to_lst(self, points: list[QtCore.QPoint | QtCore.QPointF]):
        return self.cv_qp_lst(self.normalize_points(points))

    def normalize_points(self, points: list[QtCore.QPoint | QtCore.QPointF]) -> list:
        norm_points = []
                
        if len(points) > 0:
            for qp in points:
                x, y = qp.x(), qp.y()
                x0, y0 = self.rect().x(), self.rect().y()
                x1, y1 = x0 + self.rect().width(), y0 + self.rect().height()
                if  x >= x0 and x < x1 and y >= y0 and y < y1:
                    x_rel = (x - x0) / (x1 - x0)
                    y_rel = (y - y0) / (y1 - y0)
                    norm_points.append(QtCore.QPointF(x_rel, y_rel))
        
        return norm_points
    
    def cv_qp_lst(self, points: list[QtCore.QPoint | QtCore.QPointF]) -> list:
        lst_points = []
        if len(points) > 0:
            for qp in points:
                lst_points.append([qp.x(), qp.y()])
        
        return lst_points

    def convert_cv_qt(self, cv_img: np.ndarray) -> QtGui.QPixmap:
        """Convert from an numpy array to QPixmap"""
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        p = QtGui.QImage(cv_img.data, w, h, bytes_per_line, QtGui.QImage.Format_BGR888)
        min_w = min(p.width(), self.maximumWidth())
        min_h = min(p.height(), self.maximumHeight())
        p = p.scaled(min_w, min_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        return QtGui.QPixmap.fromImage(p)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        override_cursor(CURSOR_DEFAULT)
