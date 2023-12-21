import os

from PyQt5 import QtCore, QtGui, QtWidgets


class ImageViewer(QtWidgets.QGraphicsView):
    def __init__(self, parent):
        super().__init__(parent)
        self.begin_drag = None
        self.begin_drag_pos = None
    
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.itemAt(event.pos()) is None:
            self.begin_drag=True
            self.begin_drag_pos=event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.begin_drag and self.begin_drag_pos is not None:
            delta = self.begin_drag_pos - event.pos()
            old_center = QtCore.QPointF(
                (self.mapToScene(self.pos()).x() + self.width()) / 2,
                (self.mapToScene(self.pos()).y() + self.height()) / 2
            )
            self.centerOn(old_center+delta)
            self.update()

        else:
            super().mouseMoveEvent(event)
        pass

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.begin_drag:
            self.begin_drag=False
            self.begin_drag_pos=None

        super().mouseReleaseEvent(event)

class DisplayImage(QtWidgets.QWidget):
    def __init__(self, parent) -> None:
        super().__init__()
        self.p = parent
        self.graphic_view = QtWidgets.QGraphicsView(self.p)
        self.graphic_view.viewport().installEventFilter(self)
        self.graphic_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.graphic_scene = QtWidgets.QGraphicsScene(self.p)
        self.verlayout = QtWidgets.QVBoxLayout()
        self.verlayout.addWidget(self.graphic_view)
        self.setLayout(self.verlayout)
        self.current_pixmap_item = None
    
    def display_image(self, image_path: str) -> None:
        # Clear the previous image
        if self.current_pixmap_item is not None:
            self.graphic_scene.removeItem(self.current_pixmap_item)
        
        if os.path.isfile(image_path):
            pixmap = QtGui.QPixmap(image_path)
            pixmap = pixmap.scaled(
                self.width(), self.height(),
                QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation
            )
        else:
            pixmap = QtGui.QPixmap(1920, 1080)
            pixmap.fill(QtCore.Qt.black)
        
        pixmap_item = self.graphic_scene.addPixmap(pixmap)
        self.graphic_view.setScene(self.graphic_scene)
        self.showMaximized()

        # Update the current pixmap item reference
        self.current_pixmap_item = pixmap_item

    def eventFilter(self, source, event):
        if (source == self.graphic_view.viewport() and 
            event.type() == QtCore.QEvent.Wheel and
            event.modifiers() == QtCore.Qt.ControlModifier):
            if event.angleDelta().y() > 0:
                scale = 1.25
            else:
                scale = .8
            self.graphic_view.scale(scale, scale)
            # do not propagate the event to the scroll area scrollbars
            return True
        return super().eventFilter(source,event)
