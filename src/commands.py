"""Command pattern for undo/redo functionality"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .models import Annotation, ImageData


class Command(ABC):
    """Base command interface"""
    
    @abstractmethod
    def execute(self):
        """Execute the command"""
        pass
        
    @abstractmethod
    def undo(self):
        """Undo the command"""
        pass


class CreateBoxCommand(Command):
    """Command to create a new bounding box"""
    
    def __init__(self, image_data: ImageData, annotation: Annotation):
        self.image_data = image_data
        self.annotation = annotation
        
    def execute(self):
        self.image_data.annotations.append(self.annotation)
        
    def undo(self):
        if self.annotation in self.image_data.annotations:
            self.image_data.annotations.remove(self.annotation)


class DeleteBoxCommand(Command):
    """Command to delete a bounding box"""
    
    def __init__(self, image_data: ImageData, annotation: Annotation):
        self.image_data = image_data
        self.annotation = annotation
        self.index = -1
        
    def execute(self):
        if self.annotation in self.image_data.annotations:
            self.index = self.image_data.annotations.index(self.annotation)
            self.image_data.annotations.remove(self.annotation)
            
    def undo(self):
        if 0 <= self.index <= len(self.image_data.annotations):
            self.image_data.annotations.insert(self.index, self.annotation)


class DeleteBoxesCommand(Command):
    """Command to delete multiple bounding boxes"""
    
    def __init__(self, image_data: ImageData, annotations: List[Annotation]):
        self.image_data = image_data
        self.annotations = annotations
        self.indices = []
        
    def execute(self):
        self.indices = []
        for ann in self.annotations:
            if ann in self.image_data.annotations:
                idx = self.image_data.annotations.index(ann)
                self.indices.append((idx, ann))
        # Sort by index descending to remove from end
        self.indices.sort(reverse=True)
        for idx, ann in self.indices:
            self.image_data.annotations.remove(ann)
            
    def undo(self):
        # Restore in original order
        self.indices.sort()
        for idx, ann in self.indices:
            if 0 <= idx <= len(self.image_data.annotations):
                self.image_data.annotations.insert(idx, ann)


class MoveBoxCommand(Command):
    """Command to move a bounding box"""
    
    def __init__(self, annotation: Annotation, dx: int, dy: int, img_width: int, img_height: int):
        self.annotation = annotation
        self.dx = dx
        self.dy = dy
        self.img_width = img_width
        self.img_height = img_height
        
    def execute(self):
        self.annotation.x_min = max(0, min(self.annotation.x_min + self.dx, self.img_width - 1))
        self.annotation.y_min = max(0, min(self.annotation.y_min + self.dy, self.img_height - 1))
        self.annotation.x_max = max(self.annotation.x_min + 1, 
                                   min(self.annotation.x_max + self.dx, self.img_width))
        self.annotation.y_max = max(self.annotation.y_min + 1,
                                   min(self.annotation.y_max + self.dy, self.img_height))
        
    def undo(self):
        self.annotation.x_min = max(0, min(self.annotation.x_min - self.dx, self.img_width - 1))
        self.annotation.y_min = max(0, min(self.annotation.y_min - self.dy, self.img_height - 1))
        self.annotation.x_max = max(self.annotation.x_min + 1,
                                   min(self.annotation.x_max - self.dx, self.img_width))
        self.annotation.y_max = max(self.annotation.y_min + 1,
                                   min(self.annotation.y_max - self.dy, self.img_height))


class ResizeBoxCommand(Command):
    """Command to resize a bounding box"""
    
    def __init__(self, annotation: Annotation, x_min: int, y_min: int, x_max: int, y_max: int,
                 img_width: int, img_height: int):
        self.annotation = annotation
        self.old_x_min = annotation.x_min
        self.old_y_min = annotation.y_min
        self.old_x_max = annotation.x_max
        self.old_y_max = annotation.y_max
        self.new_x_min = max(0, min(x_min, img_width - 1))
        self.new_y_min = max(0, min(y_min, img_height - 1))
        self.new_x_max = max(self.new_x_min + 1, min(x_max, img_width))
        self.new_y_max = max(self.new_y_min + 1, min(y_max, img_height))
        
    def execute(self):
        self.annotation.x_min = self.new_x_min
        self.annotation.y_min = self.new_y_min
        self.annotation.x_max = self.new_x_max
        self.annotation.y_max = self.new_y_max
        
    def undo(self):
        self.annotation.x_min = self.old_x_min
        self.annotation.y_min = self.old_y_min
        self.annotation.x_max = self.old_x_max
        self.annotation.y_max = self.old_y_max


class ChangeClassCommand(Command):
    """Command to change class of annotation(s)"""
    
    def __init__(self, annotations: List[Annotation], new_class_id: int, new_class_name: str):
        self.annotations = annotations
        self.new_class_id = new_class_id
        self.new_class_name = new_class_name
        self.old_classes = [(ann.class_id, ann.class_name) for ann in annotations]
        
    def execute(self):
        for ann in self.annotations:
            ann.class_id = self.new_class_id
            ann.class_name = self.new_class_name
            
    def undo(self):
        for ann, (old_id, old_name) in zip(self.annotations, self.old_classes):
            ann.class_id = old_id
            ann.class_name = old_name


class CommandHistory:
    """Manages command history for undo/redo"""
    
    def __init__(self, max_history: int = 50):
        self.history: List[Command] = []
        self.current_index: int = -1
        self.max_history = max_history
        
    def execute_command(self, command: Command):
        """Execute a command and add to history"""
        command.execute()
        # Remove any commands after current index (when redo was possible)
        self.history = self.history[:self.current_index + 1]
        # Add new command
        self.history.append(command)
        self.current_index += 1
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
            
    def undo(self) -> bool:
        """Undo last command"""
        if self.current_index >= 0:
            self.history[self.current_index].undo()
            self.current_index -= 1
            return True
        return False
        
    def redo(self) -> bool:
        """Redo last undone command"""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            self.history[self.current_index].execute()
            return True
        return False
        
    def clear(self):
        """Clear command history"""
        self.history.clear()
        self.current_index = -1
