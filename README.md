# Annotation GUI

A standalone bounding box annotation tool for computer vision projects. Supports exporting to Pascal VOC, YOLO, and COCO formats.

## Features

- **Three-panel layout**: Image list, annotation canvas, and class management
- **Modern annotation features**: Undo/redo, multi-select, keyboard shortcuts
- **Multiple export formats**: Automatically exports to VOC, YOLO, and COCO formats
- **Auto-save**: Saves annotations automatically on navigation
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

### From Source

1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

### Standalone Executable

Build a standalone executable that runs without Python:

```bash
python build.py
```

The executable will be created in the `dist` folder.

## Usage

1. **Open a folder**: File → Open Folder to select a folder containing images
2. **Draw boxes**: Select the Box tool (B key) and click-drag to create bounding boxes
3. **Assign classes**: Use number keys (1-9, 0) or double-click a class to assign to selected boxes
4. **Navigate**: Use arrow keys or A/D to move between images
5. **Save**: Annotations are automatically saved when navigating between images

## Keyboard Shortcuts

- **Navigation**: ←/→ or A/D (previous/next image), Home/End (first/last)
- **Tools**: S (Select), B (Box), H (Pan)
- **Box Operations**: Delete (remove box), Ctrl+A (select all), Escape (deselect)
- **Class Assignment**: 1-9, 0 (assign class by number)
- **Zoom**: Ctrl+Mouse Wheel, Ctrl+0 (fit), Ctrl+1 (100%)
- **General**: Ctrl+Z (undo), Ctrl+Y (redo), Ctrl+S (save)

## Project Structure

When you open a folder, the application creates:
- `project.json` - Working state with all annotations
- `project.json.bak` - Backup of previous save
- `exports/` - Auto-generated export folders:
  - `voc/Annotations/*.xml` - Pascal VOC format
  - `coco/annotations.json` - COCO format
  - `yolo/labels/*.txt` + `classes.txt` - YOLO format

## For more details, check [QUICKSTART.md](QUICKSTART.md)

## Requirements

- Python 3.8+
- PySide6
- Pillow
- PyInstaller (for building standalone executable)

## License

MIT License

## Funding

This project was developed with funding support from the United States Department of Agriculture (USDA).
