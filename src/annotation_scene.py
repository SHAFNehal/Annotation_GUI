"""Annotation scene for displaying images and bounding boxes"""
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPixmap, QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from typing import List, Optional
from .models import ImageData, Annotation
from .bounding_box_item import BoundingBoxItem
from .project_manager import ProjectManager


class AnnotationScene(QGraphicsScene):
    """Custom scene for image and annotation display"""
    
    # Signals
    box_selected = Signal(object)  # Emits Annotation
    boxes_selected = Signal(list)  # Emits list of Annotations
    box_created = Signal(object)  # Emits Annotation
    
    def __init__(self, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.image_item: Optional[QGraphicsPixmapItem] = None
        self.box_items: List[BoundingBoxItem] = []
        self.current_image_data: Optional[ImageData] = None
        
        # Drawing state
        self.is_drawing = False
        self.draw_start_pos: Optional[QPointF] = None
        self.draw_rect_item: Optional[QGraphicsRectItem] = None
        
    def load_image(self, image_data: ImageData):
        """Load an image into the scene"""
        self.clear_scene()
        self.current_image_data = image_data
        
        # Load image
        pixmap = QPixmap(image_data.filepath)
        if pixmap.isNull():
            return False
            
        self.image_item = QGraphicsPixmapItem(pixmap)
        # Set image z-value to 0 (background)
        self.image_item.setZValue(0)
        self.addItem(self.image_item)
        self.setSceneRect(self.image_item.boundingRect())
        
        # Load annotations
        for annotation in image_data.annotations:
            self.add_box_item(annotation)

        # Force update
        self.update()
        for view in self.views():
            view.viewport().update()
        return True
        
    def clear_scene(self):
        """Clear all items from scene"""
        self.box_items.clear()
        self.image_item = None
        self.current_image_data = None
        self.clear()
        
    def add_box_item(self, annotation: Annotation):
        """Add a bounding box item"""
        # Get class color
        color = "#FF0000"
        if self.project_manager.project:
            for cls in self.project_manager.project.classes:
                if cls.id == annotation.class_id:
                    color = cls.color
                    break
        box_item = BoundingBoxItem(annotation, class_color=color, 
                                   on_changed=self._on_box_changed)
        self.addItem(box_item)
        self.box_items.append(box_item)
        
        # Ensure box is above image (z-order)
        if self.image_item:
            box_item.setZValue(self.image_item.zValue() + 1)
        
        # Force update
        box_item.update()
        self.update()

        # Update all viewports to render the new box
        for view in self.views():
            view.viewport().update()
        
    def remove_box_item(self, box_item: BoundingBoxItem):
        """Remove a bounding box item"""
        if box_item in self.box_items:
            self.box_items.remove(box_item)
            self.removeItem(box_item)
            
    def get_selected_boxes(self) -> List[Annotation]:
        """Get list of selected annotations"""
        selected = []
        for box_item in self.box_items:
            if box_item.isSelected():
                selected.append(box_item.annotation)
        return selected
        
    def select_all_boxes(self):
        """Select all boxes"""
        for box_item in self.box_items:
            box_item.setSelected(True)
            
    def deselect_all_boxes(self):
        """Deselect all boxes"""
        for box_item in self.box_items:
            box_item.setSelected(False)
            
    def start_drawing_box(self, pos: QPointF):
        """Start drawing a new box"""
        if not self.current_image_data:
            return
        self.is_drawing = True
        self.draw_start_pos = pos
        
        # Create temporary rectangle
        self.draw_rect_item = QGraphicsRectItem()
        pen = QPen(QColor(255, 0, 0), 2, Qt.DashLine)
        self.draw_rect_item.setPen(pen)
        self.draw_rect_item.setBrush(QBrush(Qt.NoBrush))
        self.addItem(self.draw_rect_item)
        
    def update_drawing_box(self, pos: QPointF):
        """Update drawing box while dragging"""
        if not self.is_drawing or not self.draw_start_pos:
            return
            
        rect = QRectF(self.draw_start_pos, pos).normalized()
        self.draw_rect_item.setRect(rect)
        
    def finish_drawing_box(self, pos: QPointF) -> Optional[Annotation]:
        """Finish drawing box and create annotation"""
        if not self.is_drawing or not self.draw_start_pos or not self.current_image_data:
            return None
            
        # Remove temporary rectangle
        if self.draw_rect_item:
            self.removeItem(self.draw_rect_item)
            self.draw_rect_item = None
            
        # Create annotation
        rect = QRectF(self.draw_start_pos, pos).normalized()
        
        # Clamp to image bounds
        img_width = self.current_image_data.width
        img_height = self.current_image_data.height
        x_min = max(0, min(int(rect.x()), img_width - 1))
        y_min = max(0, min(int(rect.y()), img_height - 1))
        x_max = max(x_min + 1, min(int(rect.x() + rect.width()), img_width))
        y_max = max(y_min + 1, min(int(rect.y() + rect.height()), img_height))
        
        if x_max <= x_min or y_max <= y_min:
            self.is_drawing = False
            return None
            
        # Get default class
        default_class_id = 0
        default_class_name = "object"
        if self.project_manager.project and self.project_manager.project.classes:
            default_class_id = self.project_manager.project.classes[0].id
            default_class_name = self.project_manager.project.classes[0].name
            
        annotation = Annotation(
            class_id=default_class_id,
            class_name=default_class_name,
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max
        )
        
        # Add to image data
        self.current_image_data.annotations.append(annotation)
        
        # Add box item
        self.add_box_item(annotation)
        
        # Force scene update to show the new box
        self.update()
        self.invalidate()
        # Ensure scene rect includes all items
        self.setSceneRect(self.itemsBoundingRect())

        self.is_drawing = False
        self.box_created.emit(annotation)
        return annotation
        
    def cancel_drawing_box(self):
        """Cancel drawing box"""
        if self.draw_rect_item:
            self.removeItem(self.draw_rect_item)
            self.draw_rect_item = None
        self.is_drawing = False
        
    def _on_box_changed(self, annotation: Annotation):
        """Handle box change"""
        # Clamp to image bounds
        if self.current_image_data:
            annotation.clamp_to_bounds(
                self.current_image_data.width,
                self.current_image_data.height
            )
            # Update rect to match clamped values
            for box_item in self.box_items:
                if box_item.annotation == annotation:
                    box_item.update_rect()
                    break
            
    def update_box_colors(self):
        """Update box colors based on class colors"""
        if not self.project_manager.project:
            return
        class_colors = {cls.id: cls.color for cls in self.project_manager.project.classes}
        for box_item in self.box_items:
            color = class_colors.get(box_item.annotation.class_id, "#FF0000")
            box_item.set_class_color(color)
            box_item.update()
