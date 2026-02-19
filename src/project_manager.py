"""Project manager for handling project state and persistence"""
import json
import os
import shutil
from pathlib import Path
from typing import Optional, List
from PIL import Image

from .models import Project, ImageData, ClassDefinition, Annotation
from .importers import ImportManager


class ProjectManager:
    """Manages project state, loading, and saving"""
    
    def __init__(self):
        self.project: Optional[Project] = None
        self.project_path: Optional[Path] = None
        self.current_image_index: int = -1
        
    def create_project(self, image_folder: str, project_path: Optional[str] = None) -> bool:
        """Create a new project from an image folder"""
        image_folder_path = Path(image_folder)
        if not image_folder_path.exists():
            return False
            
        # Determine project path
        if project_path:
            self.project_path = Path(project_path)
        else:
            # Use image folder parent as project root
            self.project_path = image_folder_path.parent / "project.json"
        
        # Load images
        image_files = self._find_image_files(image_folder_path)
        if not image_files:
            return False
            
        # Create project
        self.project = Project(
            image_folder=str(image_folder_path.absolute()),
            classes=[ClassDefinition(id=0, name="object", color="#FF0000")]
        )
        
        # Add images
        for img_path in image_files:
            try:
                with Image.open(img_path) as img:
                    width, height = img.size
                image_data = ImageData(
                    filename=img_path.name,
                    filepath=str(img_path.absolute()),
                    width=width,
                    height=height
                )
                self.project.images.append(image_data)
            except Exception:
                continue  # Skip invalid images
                
        self.current_image_index = 0 if self.project.images else -1
        
        # Try to import existing annotations from exports folder
        if self.project_path:
            ImportManager.import_existing_annotations(self.project, self.project_path)
        
        return True
        
    def load_project(self, project_path: str) -> bool:
        """Load an existing project"""
        project_file = Path(project_path)
        if not project_file.exists():
            return False
            
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.project = Project.from_dict(data)
            self.project_path = project_file
            self.current_image_index = 0 if self.project.images else -1
            
            # Try to import existing annotations from exports folder
            ImportManager.import_existing_annotations(self.project, self.project_path)
            
            return True
        except Exception:
            # Try backup
            backup_file = project_file.with_suffix('.json.bak')
            if backup_file.exists():
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.project = Project.from_dict(data)
                    self.project_path = project_file
                    self.current_image_index = 0 if self.project.images else -1
                    
                    # Try to import existing annotations from exports folder
                    ImportManager.import_existing_annotations(self.project, self.project_path)
                    
                    return True
                except Exception:
                    pass
            return False
            
    def save_project(self) -> bool:
        """Save project to file with crash-safe write"""
        if not self.project or not self.project_path:
            return False
            
        try:
            # Create backup
            if self.project_path.exists():
                backup_path = self.project_path.with_suffix('.json.bak')
                shutil.copy2(self.project_path, backup_path)
            
            # Update modified timestamp
            from datetime import datetime
            self.project.modified_at = datetime.utcnow().isoformat() + "Z"
            
            # Write to temp file
            temp_path = self.project_path.with_suffix('.json.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.project.to_dict(), f, indent=2)
            
            # Atomic rename
            if os.name == 'nt':  # Windows
                if self.project_path.exists():
                    os.remove(self.project_path)
                os.rename(temp_path, self.project_path)
            else:  # Unix-like
                os.replace(temp_path, self.project_path)
                
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
            
    def sync_new_images(self) -> tuple:
        """Sync the project image list against the image folder on disk.

        - Removes entries (and their annotations) for images that no longer exist.
        - Adds entries for image files that are new to the folder.

        Returns (new_count, removed_count).
        """
        if not self.project or not self.project.image_folder:
            return (0, 0)
        folder_path = Path(self.project.image_folder)
        if not folder_path.exists():
            return (0, 0)

        # --- Remove deleted images ---
        before_count = len(self.project.images)
        self.project.images = [
            img for img in self.project.images
            if Path(img.filepath).exists()
        ]
        removed_count = before_count - len(self.project.images)

        # Reset current index if it's now out of range
        if self.current_image_index >= len(self.project.images):
            self.current_image_index = max(0, len(self.project.images) - 1)

        # --- Add new images ---
        existing_filenames = {img.filename for img in self.project.images}
        image_files = self._find_image_files(folder_path)

        new_count = 0
        for img_path in image_files:
            if img_path.name not in existing_filenames:
                try:
                    with Image.open(img_path) as img:
                        width, height = img.size
                    image_data = ImageData(
                        filename=img_path.name,
                        filepath=str(img_path.absolute()),
                        width=width,
                        height=height
                    )
                    self.project.images.append(image_data)
                    new_count += 1
                except Exception:
                    continue

        return (new_count, removed_count)

    def get_current_image(self) -> Optional[ImageData]:
        """Get current image data"""
        if not self.project or self.current_image_index < 0:
            return None
        if self.current_image_index >= len(self.project.images):
            return None
        return self.project.images[self.current_image_index]
        
    def set_current_image(self, index: int) -> bool:
        """Set current image index"""
        if not self.project:
            return False
        if 0 <= index < len(self.project.images):
            self.current_image_index = index
            return True
        return False
        
    def add_class(self, name: str, color: str = "#FF0000") -> int:
        """Add a new class and return its ID"""
        if not self.project:
            return -1
        class_id = len(self.project.classes)
        self.project.classes.append(ClassDefinition(id=class_id, name=name, color=color))
        return class_id
        
    def get_class(self, class_id: int) -> Optional[ClassDefinition]:
        """Get class definition by ID"""
        if not self.project:
            return None
        for cls in self.project.classes:
            if cls.id == class_id:
                return cls
        return None
        
    def _find_image_files(self, folder: Path) -> List[Path]:
        """Find all image files in folder"""
        extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
        image_files = []
        for ext in extensions:
            image_files.extend(folder.glob(f'*{ext}'))
            image_files.extend(folder.glob(f'*{ext.upper()}'))
        return sorted(image_files)
