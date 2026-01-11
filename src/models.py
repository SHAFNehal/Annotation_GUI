"""Data models for the annotation application"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import uuid


@dataclass
class ClassDefinition:
    """Class/label definition"""
    id: int
    name: str
    color: str = "#FF0000"


@dataclass
class Annotation:
    """Bounding box annotation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    class_id: int = 0
    class_name: str = ""
    x_min: int = 0
    y_min: int = 0
    x_max: int = 0
    y_max: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    modified_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self):
        return {
            "id": self.id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "x_min": self.x_min,
            "y_min": self.y_min,
            "x_max": self.x_max,
            "y_max": self.y_max,
            "created_at": self.created_at,
            "modified_at": self.modified_at
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            class_id=data.get("class_id", 0),
            class_name=data.get("class_name", ""),
            x_min=data.get("x_min", 0),
            y_min=data.get("y_min", 0),
            x_max=data.get("x_max", 0),
            y_max=data.get("y_max", 0),
            created_at=data.get("created_at", datetime.utcnow().isoformat() + "Z"),
            modified_at=data.get("modified_at", datetime.utcnow().isoformat() + "Z")
        )

    def clamp_to_bounds(self, img_width: int, img_height: int):
        """Clamp box coordinates to image boundaries"""
        self.x_min = max(0, min(self.x_min, img_width - 1))
        self.y_min = max(0, min(self.y_min, img_height - 1))
        self.x_max = max(self.x_min + 1, min(self.x_max, img_width))
        self.y_max = max(self.y_min + 1, min(self.y_max, img_height))

    def is_valid(self) -> bool:
        """Check if annotation has valid dimensions"""
        return self.x_max > self.x_min and self.y_max > self.y_min


@dataclass
class ImageData:
    """Image metadata and annotations"""
    filename: str
    filepath: str
    width: int = 0
    height: int = 0
    annotations: List[Annotation] = field(default_factory=list)

    def to_dict(self):
        return {
            "filename": self.filename,
            "filepath": self.filepath,
            "width": self.width,
            "height": self.height,
            "annotations": [ann.to_dict() for ann in self.annotations]
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            filename=data.get("filename", ""),
            filepath=data.get("filepath", ""),
            width=data.get("width", 0),
            height=data.get("height", 0),
            annotations=[Annotation.from_dict(ann) for ann in data.get("annotations", [])]
        )


@dataclass
class Project:
    """Project data model"""
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    modified_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    image_folder: str = ""
    classes: List[ClassDefinition] = field(default_factory=list)
    images: List[ImageData] = field(default_factory=list)

    def to_dict(self):
        return {
            "version": self.version,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "image_folder": self.image_folder,
            "classes": [{"id": c.id, "name": c.name, "color": c.color} for c in self.classes],
            "images": [img.to_dict() for img in self.images]
        }

    @classmethod
    def from_dict(cls, data):
        classes = [ClassDefinition(id=c["id"], name=c["name"], color=c.get("color", "#FF0000"))
                   for c in data.get("classes", [])]
        images = [ImageData.from_dict(img) for img in data.get("images", [])]
        return cls(
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", datetime.utcnow().isoformat() + "Z"),
            modified_at=data.get("modified_at", datetime.utcnow().isoformat() + "Z"),
            image_folder=data.get("image_folder", ""),
            classes=classes,
            images=images
        )
