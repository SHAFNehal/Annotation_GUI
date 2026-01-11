"""Bounding box graphics item with resize handles"""
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QCursor
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from typing import Optional, Callable
from .models import Annotation


class BoundingBoxItem(QGraphicsRectItem):
    """Custom graphics item for bounding boxes with resize handles"""
    
    HANDLE_SIZE = 8
    HANDLE_HALF = HANDLE_SIZE / 2
    
    def __init__(self, annotation: Annotation, class_color: str = "#FF0000", 
                 on_changed: Optional[Callable[[Annotation], None]] = None, parent=None):
        super().__init__(parent)
        self.annotation = annotation
        self._class_color = class_color
        self._on_changed_callback = on_changed
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        
        # Set initial rect
        self.update_rect()
        
        # Ensure it's visible
        self.setVisible(True)
        
        # Resize handle positions (corners + edges)
        self.handles = []
        self.active_handle = None
        self.is_resizing = False
        
    def set_class_color(self, color: str):
        """Set class color for this box"""
        self._class_color = color
        self.update()
        
    def update_rect(self):
        """Update rectangle from annotation coordinates"""
        width = self.annotation.x_max - self.annotation.x_min
        height = self.annotation.y_max - self.annotation.y_min
        
        # Ensure valid dimensions
        if width <= 0 or height <= 0:
            width = max(1, width)
            height = max(1, height)
        
        rect = QRectF(
            float(self.annotation.x_min),
            float(self.annotation.y_min),
            float(width),
            float(height)
        )
        self.setRect(rect)
        self.prepareGeometryChange()
        
    def update_annotation(self):
        """Update annotation from rectangle"""
        from datetime import datetime
        rect = self.rect()
        self.annotation.x_min = int(rect.x())
        self.annotation.y_min = int(rect.y())
        self.annotation.x_max = int(rect.x() + rect.width())
        self.annotation.y_max = int(rect.y() + rect.height())
        self.annotation.modified_at = datetime.utcnow().isoformat() + "Z"
        # Call callback if provided
        if self._on_changed_callback:
            self._on_changed_callback(self.annotation)
        
    def paint(self, painter: QPainter, option, widget=None):
        """Custom paint with selection highlight and handles"""
        # Get class color - will be set by scene
        color_str = getattr(self, '_class_color', "#FF0000")
        try:
            color = QColor(color_str)
        except:
            color = QColor("#FF0000")
        
        # Ensure we have a valid rect
        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        
        # Draw box
        pen_width = 3 if self.isSelected() else 2
        pen = QPen(color, pen_width)
        if self.isSelected():
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.NoBrush))
        painter.drawRect(rect)
        
        # Draw label
        if self.annotation.class_name:
            painter.setPen(QPen(Qt.white))
            painter.setBrush(QBrush(color))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            label_rect = QRectF(rect.x(), max(0, rect.y() - 20), 100, 18)
            painter.drawRect(label_rect)
            painter.drawText(label_rect, Qt.AlignCenter, self.annotation.class_name)
        
        # Draw resize handles if selected
        if self.isSelected():
            self._draw_handles(painter)
            
    def _draw_handles(self, painter: QPainter):
        """Draw resize handles"""
        rect = self.rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        handles = self._get_handle_positions(rect)
        
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(Qt.white))
        
        for handle_pos in handles:
            handle_rect = QRectF(
                handle_pos.x() - self.HANDLE_HALF,
                handle_pos.y() - self.HANDLE_HALF,
                self.HANDLE_SIZE,
                self.HANDLE_SIZE
            )
            painter.drawRect(handle_rect)
            
    def _get_handle_positions(self, rect: QRectF) -> list:
        """Get positions of all resize handles"""
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        return [
            QPointF(x, y),  # Top-left
            QPointF(x + w/2, y),  # Top-center
            QPointF(x + w, y),  # Top-right
            QPointF(x + w, y + h/2),  # Right-center
            QPointF(x + w, y + h),  # Bottom-right
            QPointF(x + w/2, y + h),  # Bottom-center
            QPointF(x, y + h),  # Bottom-left
            QPointF(x, y + h/2),  # Left-center
        ]
        
    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update annotation when moved
            self.update_annotation()
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)
        
    def mousePressEvent(self, event):
        """Handle mouse press for resizing"""
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            rect = self.rect()
            handles = self._get_handle_positions(rect)
            
            # Check if clicking on a handle
            for i, handle_pos in enumerate(handles):
                handle_rect = QRectF(
                    handle_pos.x() - self.HANDLE_HALF,
                    handle_pos.y() - self.HANDLE_HALF,
                    self.HANDLE_SIZE,
                    self.HANDLE_SIZE
                )
                if handle_rect.contains(pos):
                    self.active_handle = i
                    self.is_resizing = True
                    self.setFlag(QGraphicsItem.ItemIsMovable, False)
                    event.accept()
                    return
                    
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move for resizing"""
        if self.is_resizing and self.active_handle is not None:
            new_pos = event.pos()
            rect = self.rect()
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
            
            # Calculate new rect based on handle
            if self.active_handle == 0:  # Top-left
                new_rect = QRectF(new_pos.x(), new_pos.y(), w + (x - new_pos.x()), h + (y - new_pos.y()))
            elif self.active_handle == 1:  # Top-center
                new_rect = QRectF(x, new_pos.y(), w, h + (y - new_pos.y()))
            elif self.active_handle == 2:  # Top-right
                new_rect = QRectF(x, new_pos.y(), new_pos.x() - x, h + (y - new_pos.y()))
            elif self.active_handle == 3:  # Right-center
                new_rect = QRectF(x, y, new_pos.x() - x, h)
            elif self.active_handle == 4:  # Bottom-right
                new_rect = QRectF(x, y, new_pos.x() - x, new_pos.y() - y)
            elif self.active_handle == 5:  # Bottom-center
                new_rect = QRectF(x, y, w, new_pos.y() - y)
            elif self.active_handle == 6:  # Bottom-left
                new_rect = QRectF(new_pos.x(), y, w + (x - new_pos.x()), new_pos.y() - y)
            elif self.active_handle == 7:  # Left-center
                new_rect = QRectF(new_pos.x(), y, w + (x - new_pos.x()), h)
            else:
                new_rect = rect
                
            # Ensure minimum size
            if new_rect.width() > 10 and new_rect.height() > 10:
                self.setRect(new_rect)
                self.update_annotation()
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.is_resizing:
            self.is_resizing = False
            self.active_handle = None
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def hoverMoveEvent(self, event):
        """Change cursor on handle hover"""
        if self.isSelected():
            pos = event.pos()
            handles = self._get_handle_positions(self.rect())
            for handle_pos in handles:
                handle_rect = QRectF(
                    handle_pos.x() - self.HANDLE_HALF,
                    handle_pos.y() - self.HANDLE_HALF,
                    self.HANDLE_SIZE,
                    self.HANDLE_SIZE
                )
                if handle_rect.contains(pos):
                    self.setCursor(QCursor(Qt.SizeFDiagCursor))
                    return
        self.setCursor(QCursor(Qt.ArrowCursor))
