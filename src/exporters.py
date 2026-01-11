"""Exporters for VOC, YOLO, and COCO formats"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List
from .models import Project, ImageData, Annotation


class VOCExporter:
    """Exports annotations in Pascal VOC XML format"""
    
    @staticmethod
    def export(project: Project, output_dir: Path):
        """Export project to VOC format"""
        annotations_dir = output_dir / "voc" / "Annotations"
        annotations_dir.mkdir(parents=True, exist_ok=True)
        
        for image_data in project.images:
            if not image_data.annotations:
                continue
                
            # Create XML
            root = ET.Element("annotation")
            
            # Folder and filename
            folder_elem = ET.SubElement(root, "folder")
            folder_elem.text = Path(image_data.filepath).parent.name
            filename_elem = ET.SubElement(root, "filename")
            filename_elem.text = image_data.filename
            
            # Source
            source = ET.SubElement(root, "source")
            database = ET.SubElement(source, "database")
            database.text = "AnnotationGUI"
            
            # Size
            size = ET.SubElement(root, "size")
            width_elem = ET.SubElement(size, "width")
            width_elem.text = str(image_data.width)
            height_elem = ET.SubElement(size, "height")
            height_elem.text = str(image_data.height)
            depth_elem = ET.SubElement(size, "depth")
            depth_elem.text = "3"
            
            # Segmented
            segmented = ET.SubElement(root, "segmented")
            segmented.text = "0"
            
            # Objects
            for ann in image_data.annotations:
                if not ann.is_valid():
                    continue
                obj = ET.SubElement(root, "object")
                name = ET.SubElement(obj, "name")
                name.text = ann.class_name
                pose = ET.SubElement(obj, "pose")
                pose.text = "Unspecified"
                truncated = ET.SubElement(obj, "truncated")
                truncated.text = "0"
                difficult = ET.SubElement(obj, "difficult")
                difficult.text = "0"
                
                bndbox = ET.SubElement(obj, "bndbox")
                xmin = ET.SubElement(bndbox, "xmin")
                xmin.text = str(ann.x_min)
                ymin = ET.SubElement(bndbox, "ymin")
                ymin.text = str(ann.y_min)
                xmax = ET.SubElement(bndbox, "xmax")
                xmax.text = str(ann.x_max)
                ymax = ET.SubElement(bndbox, "ymax")
                ymax.text = str(ann.y_max)
            
            # Write XML
            xml_file = annotations_dir / f"{Path(image_data.filename).stem}.xml"
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(xml_file, encoding="utf-8", xml_declaration=True)


class YOLOExporter:
    """Exports annotations in YOLO format"""
    
    @staticmethod
    def export(project: Project, output_dir: Path):
        """Export project to YOLO format"""
        labels_dir = output_dir / "yolo" / "labels"
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        # Write classes.txt
        classes_file = output_dir / "yolo" / "classes.txt"
        with open(classes_file, 'w', encoding='utf-8') as f:
            for cls in project.classes:
                f.write(f"{cls.name}\n")
        
        # Export labels for each image (only create files for images with annotations)
        for image_data in project.images:
            if not image_data.annotations:
                continue  # Skip images without annotations
                
            label_file = labels_dir / f"{Path(image_data.filename).stem}.txt"
            
            with open(label_file, 'w', encoding='utf-8') as f:
                for ann in image_data.annotations:
                    if not ann.is_valid():
                        continue
                    
                    # Ensure we have valid image dimensions
                    if image_data.width <= 0 or image_data.height <= 0:
                        continue
                    
                    # Convert to YOLO format (normalized center-width-height)
                    center_x = (ann.x_min + ann.x_max) / 2.0 / image_data.width
                    center_y = (ann.y_min + ann.y_max) / 2.0 / image_data.height
                    width = (ann.x_max - ann.x_min) / image_data.width
                    height = (ann.y_max - ann.y_min) / image_data.height
                    
                    # Clamp to [0, 1]
                    center_x = max(0.0, min(1.0, center_x))
                    center_y = max(0.0, min(1.0, center_y))
                    width = max(0.0, min(1.0, width))
                    height = max(0.0, min(1.0, height))
                    
                    f.write(f"{ann.class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")


class COCOExporter:
    """Exports annotations in COCO JSON format"""
    
    @staticmethod
    def export(project: Project, output_dir: Path):
        """Export project to COCO format"""
        coco_dir = output_dir / "coco"
        coco_dir.mkdir(parents=True, exist_ok=True)
        
        # Build COCO structure
        coco_data = {
            "info": {
                "description": "AnnotationGUI Export",
                "version": project.version,
                "year": 2024
            },
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": []
        }
        
        # Categories
        for cls in project.classes:
            coco_data["categories"].append({
                "id": cls.id,
                "name": cls.name,
                "supercategory": "none"
            })
        
        # Images and annotations
        image_id = 1
        annotation_id = 1
        
        for image_data in project.images:
            # Add image (add all images, even if they have no annotations)
            coco_data["images"].append({
                "id": image_id,
                "width": image_data.width,
                "height": image_data.height,
                "file_name": image_data.filename
            })
            
            # Add annotations for this image
            for ann in image_data.annotations:
                # Validate annotation
                if not ann.is_valid():
                    continue
                
                # Ensure valid coordinates
                if ann.x_max <= ann.x_min or ann.y_max <= ann.y_min:
                    continue
                
                # Ensure coordinates are within image bounds
                if ann.x_min < 0 or ann.y_min < 0:
                    continue
                if ann.x_max > image_data.width or ann.y_max > image_data.height:
                    continue
                
                bbox = [
                    float(ann.x_min),
                    float(ann.y_min),
                    float(ann.x_max - ann.x_min),
                    float(ann.y_max - ann.y_min)
                ]
                area = float((ann.x_max - ann.x_min) * (ann.y_max - ann.y_min))
                
                # Ensure positive area
                if area <= 0:
                    continue
                
                coco_data["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": ann.class_id,
                    "bbox": bbox,
                    "area": area,
                    "iscrowd": 0
                })
                annotation_id += 1
            
            image_id += 1
        
        # Write JSON
        json_file = coco_dir / "annotations.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(coco_data, f, indent=2)


class ExportManager:
    """Manages all export operations"""
    
    @staticmethod
    def export_all(project: Project, project_path: Path):
        """Export to all formats"""
        if not project_path:
            return False
        
        if not project:
            return False
            
        output_dir = project_path.parent / "exports"
        
        try:
            # Debug: Count annotations before export
            total_annotations = sum(len(img.annotations) for img in project.images)
            print(f"Exporting {total_annotations} annotations across {len(project.images)} images")
            
            VOCExporter.export(project, output_dir)
            YOLOExporter.export(project, output_dir)
            COCOExporter.export(project, output_dir)
            
            print(f"Export completed successfully to {output_dir}")
            return True
        except Exception as e:
            import traceback
            print(f"Export error: {e}")
            traceback.print_exc()
            return False
