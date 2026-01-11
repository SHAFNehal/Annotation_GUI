"""Image viewer with pan and zoom functionality"""
from PySide6.QtCore import Qt, QPoint, QPointF, Signal
from PySide6.QtGui import QWheelEvent, QMouseEvent, QKeyEvent, QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from typing import Optional
from .annotation_scene import AnnotationScene


class ImageViewer(QGraphicsView):
    """Custom graphics view with pan/zoom and tool handling"""
    
    # Signals
    box_drawing_started = Signal(QPointF)
    box_drawing_updated = Signal(QPointF)
    box_drawing_finished = Signal(QPointF)
    
    def __init__(self, scene: AnnotationScene, parent=None):
        super().__init__(scene, parent)
        self.scene = scene
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Tool state
        self.current_tool = "select"  # "select", "box", "pan"
        self.is_panning = False
        self.pan_start_pos = QPoint()
        
        # Zoom
        self.zoom_factor = 1.15
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        
    def set_tool(self, tool: str):
        """Set current tool"""
        self.current_tool = tool
        if tool == "pan":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom at mouse position
            zoom_factor = self.zoom_factor if event.angleDelta().y() > 0 else 1.0 / self.zoom_factor
            self.scale(zoom_factor, zoom_factor)
            
            # Clamp zoom
            current_scale = self.transform().m11()
            if current_scale < self.min_zoom:
                self.resetTransform()
                self.scale(self.min_zoom, self.min_zoom)
            elif current_scale > self.max_zoom:
                self.resetTransform()
                self.scale(self.max_zoom, self.max_zoom)
        else:
            super().wheelEvent(event)
            
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if self.current_tool == "box" and event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.scene.start_drawing_box(scene_pos)
            self.box_drawing_started.emit(scene_pos)
        elif self.current_tool == "pan" and event.button() == Qt.LeftButton:
            self.is_panning = True
            self.pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move"""
        if self.current_tool == "box" and self.scene.is_drawing:
            scene_pos = self.mapToScene(event.pos())
            self.scene.update_drawing_box(scene_pos)
            self.box_drawing_updated.emit(scene_pos)
        elif self.current_tool == "pan" and self.is_panning:
            delta = event.pos() - self.pan_start_pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self.pan_start_pos = event.pos()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if self.current_tool == "box" and event.button() == Qt.LeftButton and self.scene.is_drawing:
            scene_pos = self.mapToScene(event.pos())
            self.scene.finish_drawing_box(scene_pos)
            self.box_drawing_finished.emit(scene_pos)
        elif self.current_tool == "pan" and event.button() == Qt.LeftButton:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
            
    def fit_to_window(self):
        """Fit image to window"""
        if self.scene and self.scene.image_item:
            self.fitInView(self.scene.image_item, Qt.KeepAspectRatio)
            
    def zoom_100(self):
        """Zoom to 100%"""
        self.resetTransform()
        
    def zoom_in(self):
        """Zoom in"""
        self.scale(self.zoom_factor, self.zoom_factor)
        
    def zoom_out(self):
        """Zoom out"""
        self.scale(1.0 / self.zoom_factor, 1.0 / self.zoom_factor)
