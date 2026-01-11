"""Importers for loading existing annotations from export formats"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict
from .models import Project, ImageData, Annotation, ClassDefinition


class VOCImporter:
    """Imports annotations from Pascal VOC XML format"""
    
    @staticmethod
    def import_from_folder(exports_dir: Path, project: Project) -> bool:
        """Import annotations from VOC format"""
        annotations_dir = exports_dir / "voc" / "Annotations"
        if not annotations_dir.exists():
            return False
        
        imported = False
        # Create a mapping of filename to ImageData
        filename_to_image = {img.filename: img for img in project.images}
        
        # Also try matching by stem (filename without extension)
        stem_to_image = {Path(img.filename).stem: img for img in project.images}
        
        for xml_file in annotations_dir.glob("*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Get filename from XML
                filename_elem = root.find("filename")
                if filename_elem is None:
                    continue
                filename = filename_elem.text
                
                # Try to find matching image
                image_data = filename_to_image.get(filename)
                if not image_data:
                    # Try by stem
                    xml_stem = xml_file.stem
                    image_data = stem_to_image.get(xml_stem)
                
                if not image_data:
                    continue
                
                # Only import if image has no existing annotations (don't overwrite project.json data)
                if image_data.annotations:
                    continue
                
                # Clear existing annotations for this image (should be empty anyway)
                image_data.annotations.clear()
                
                # Parse objects
                for obj in root.findall("object"):
                    name_elem = obj.find("name")
                    if name_elem is None:
                        continue
                    class_name = name_elem.text
                    
                    # Find or create class
                    class_id = VOCImporter._get_or_create_class(project, class_name)
                    
                    bndbox = obj.find("bndbox")
                    if bndbox is None:
                        continue
                    
                    xmin = int(float(bndbox.find("xmin").text))
                    ymin = int(float(bndbox.find("ymin").text))
                    xmax = int(float(bndbox.find("xmax").text))
                    ymax = int(float(bndbox.find("ymax").text))
                    
                    annotation = Annotation(
                        class_id=class_id,
                        class_name=class_name,
                        x_min=xmin,
                        y_min=ymin,
                        x_max=xmax,
                        y_max=ymax
                    )
                    
                    # Clamp to image bounds
                    annotation.clamp_to_bounds(image_data.width, image_data.height)
                    
                    if annotation.is_valid():
                        image_data.annotations.append(annotation)
                        imported = True
                        
            except Exception as e:
                print(f"Error importing VOC file {xml_file}: {e}")
                continue
        
        return imported
    
    @staticmethod
    def _get_or_create_class(project: Project, class_name: str) -> int:
        """Get class ID by name, or create new class if not found"""
        for cls in project.classes:
            if cls.name == class_name:
                return cls.id
        
        # Create new class
        class_id = len(project.classes)
        project.classes.append(ClassDefinition(id=class_id, name=class_name, color="#FF0000"))
        return class_id


class YOLOImporter:
    """Imports annotations from YOLO format"""
    
    @staticmethod
    def import_from_folder(exports_dir: Path, project: Project) -> bool:
        """Import annotations from YOLO format"""
        labels_dir = exports_dir / "yolo" / "labels"
        classes_file = exports_dir / "yolo" / "classes.txt"
        
        if not labels_dir.exists():
            return False
        
        imported = False
        
        # Load class names from classes.txt if it exists
        class_names = {}
        if classes_file.exists():
            try:
                with open(classes_file, 'r', encoding='utf-8') as f:
                    for idx, line in enumerate(f):
                        class_name = line.strip()
                        if class_name:
                            class_names[idx] = class_name
                            # Ensure class exists in project
                            YOLOImporter._get_or_create_class(project, class_name)
            except Exception:
                pass
        
        # Create mapping of filename stem to ImageData
        stem_to_image = {Path(img.filename).stem: img for img in project.images}
        
        for label_file in labels_dir.glob("*.txt"):
            try:
                stem = label_file.stem
                image_data = stem_to_image.get(stem)
                
                if not image_data:
                    continue
                
                # Only import if image has no existing annotations (don't overwrite project.json data)
                if image_data.annotations:
                    continue
                
                # Clear existing annotations (should be empty anyway)
                image_data.annotations.clear()
                
                # Read annotations
                with open(label_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        parts = line.split()
                        if len(parts) < 5:
                            continue
                        
                        try:
                            class_id = int(parts[0])
                            center_x = float(parts[1])
                            center_y = float(parts[2])
                            width = float(parts[3])
                            height = float(parts[4])
                            
                            # Convert from normalized YOLO format to absolute pixels
                            x_min = int((center_x - width / 2) * image_data.width)
                            y_min = int((center_y - height / 2) * image_data.height)
                            x_max = int((center_x + width / 2) * image_data.width)
                            y_max = int((center_y + height / 2) * image_data.height)
                            
                            # Get class name
                            class_name = class_names.get(class_id, f"class_{class_id}")
                            
                            # Ensure class exists
                            actual_class_id = YOLOImporter._get_or_create_class(project, class_name)
                            
                            annotation = Annotation(
                                class_id=actual_class_id,
                                class_name=class_name,
                                x_min=x_min,
                                y_min=y_min,
                                x_max=x_max,
                                y_max=y_max
                            )
                            
                            # Clamp to image bounds
                            annotation.clamp_to_bounds(image_data.width, image_data.height)
                            
                            if annotation.is_valid():
                                image_data.annotations.append(annotation)
                                imported = True
                                
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing YOLO line in {label_file}: {e}")
                            continue
                            
            except Exception as e:
                print(f"Error importing YOLO file {label_file}: {e}")
                continue
        
        return imported
    
    @staticmethod
    def _get_or_create_class(project: Project, class_name: str) -> int:
        """Get class ID by name, or create new class if not found"""
        for cls in project.classes:
            if cls.name == class_name:
                return cls.id
        
        # Create new class
        class_id = len(project.classes)
        project.classes.append(ClassDefinition(id=class_id, name=class_name, color="#FF0000"))
        return class_id


class COCOImporter:
    """Imports annotations from COCO JSON format"""
    
    @staticmethod
    def import_from_folder(exports_dir: Path, project: Project) -> bool:
        """Import annotations from COCO format"""
        json_file = exports_dir / "coco" / "annotations.json"
        if not json_file.exists():
            return False
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                coco_data = json.load(f)
            
            imported = False
            
            # Load categories and create class mapping
            category_id_to_class = {}
            for cat in coco_data.get("categories", []):
                cat_id = cat.get("id")
                cat_name = cat.get("name", f"class_{cat_id}")
                class_id = COCOImporter._get_or_create_class(project, cat_name)
                category_id_to_class[cat_id] = (class_id, cat_name)
            
            # Create mapping of filename to ImageData
            filename_to_image = {img.filename: img for img in project.images}
            
            # Create mapping of COCO image_id to ImageData
            # Only include images that don't have annotations (to avoid overwriting project.json data)
            coco_image_id_to_image = {}
            for img_entry in coco_data.get("images", []):
                coco_image_id = img_entry.get("id")
                filename = img_entry.get("file_name")
                image_data = filename_to_image.get(filename)
                if image_data and not image_data.annotations:
                    coco_image_id_to_image[coco_image_id] = image_data
            
            # Load annotations
            for ann_entry in coco_data.get("annotations", []):
                coco_image_id = ann_entry.get("image_id")
                image_data = coco_image_id_to_image.get(coco_image_id)
                
                if not image_data:
                    continue
                
                category_id = ann_entry.get("category_id")
                if category_id not in category_id_to_class:
                    continue
                
                class_id, class_name = category_id_to_class[category_id]
                
                bbox = ann_entry.get("bbox", [])
                if len(bbox) < 4:
                    continue
                
                # COCO format: [x, y, width, height]
                x_min = int(bbox[0])
                y_min = int(bbox[1])
                width = int(bbox[2])
                height = int(bbox[3])
                x_max = x_min + width
                y_max = y_min + height
                
                annotation = Annotation(
                    class_id=class_id,
                    class_name=class_name,
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max
                )
                
                # Clamp to image bounds
                annotation.clamp_to_bounds(image_data.width, image_data.height)
                
                if annotation.is_valid():
                    image_data.annotations.append(annotation)
                    imported = True
            
            return imported
            
        except Exception as e:
            print(f"Error importing COCO file: {e}")
            return False
    
    @staticmethod
    def _get_or_create_class(project: Project, class_name: str) -> int:
        """Get class ID by name, or create new class if not found"""
        for cls in project.classes:
            if cls.name == class_name:
                return cls.id
        
        # Create new class
        class_id = len(project.classes)
        project.classes.append(ClassDefinition(id=class_id, name=class_name, color="#FF0000"))
        return class_id


class ImportManager:
    """Manages importing annotations from export formats"""
    
    @staticmethod
    def import_existing_annotations(project: Project, project_path: Path) -> bool:
        """Import existing annotations from exports folder if available"""
        if not project_path or not project:
            return False
        
        exports_dir = project_path.parent / "exports"
        if not exports_dir.exists():
            return False
        
        imported = False
        
        # Try COCO first (single file, most complete)
        if COCOImporter.import_from_folder(exports_dir, project):
            print("Imported annotations from COCO format")
            imported = True
        # Then try VOC (per-image XML files)
        elif VOCImporter.import_from_folder(exports_dir, project):
            print("Imported annotations from VOC format")
            imported = True
        # Finally try YOLO (per-image TXT files)
        elif YOLOImporter.import_from_folder(exports_dir, project):
            print("Imported annotations from YOLO format")
            imported = True
        
        return imported
