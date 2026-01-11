# Quick Start Guide

## Installation

### Option 1: Run from Source (Recommended for Development)

1. **Install Python 3.8 or higher** if not already installed
   - Download from https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```
   Or use the run scripts:
   - Windows: `run.bat`
   - Linux/Mac: `./run.sh`

### Option 2: Build Standalone Executable

1. **Install dependencies** (including PyInstaller):
   ```bash
   pip install -r requirements.txt
   ```

2. **Build the executable:**
   ```bash
   python build.py
   ```

3. **Find your executable:**
   - Windows: `dist/AnnotationGUI.exe`
   - macOS: `dist/AnnotationGUI.app`
   - Linux: `dist/AnnotationGUI`

The executable is completely standalone - no Python installation needed!

## First Steps

1. **Open a folder with images:**
   - Click "File" → "Open Folder"
   - Select a folder containing your images (JPG, PNG, etc.)

2. **Create your first annotation:**
   - Click the "Box (B)" tool button or press `B`
   - Click and drag on the image to draw a bounding box
   - Press a number key (1-9, 0) to assign a class

3. **Navigate between images:**
   - Use arrow keys (← →) or A/D keys
   - Click on images in the left sidebar

4. **Your annotations are automatically saved** when you navigate between images!

## Tips

- **Undo/Redo**: Press `Ctrl+Z` to undo, `Ctrl+Y` to redo
- **Multi-select**: Hold `Ctrl` and click multiple boxes, or drag a selection rectangle
- **Quick class assignment**: Press number keys 1-9, 0 to assign classes instantly
- **Zoom**: Use `Ctrl + Mouse Wheel` to zoom in/out
- **Fit to window**: Press `Ctrl+0` to fit image to window

## Export Formats

Your annotations are automatically exported to three formats in the `exports/` folder:

- **VOC**: `exports/voc/Annotations/*.xml` - Pascal VOC format
- **COCO**: `exports/coco/annotations.json` - COCO format (single JSON file)
- **YOLO**: `exports/yolo/labels/*.txt` + `classes.txt` - YOLO format

All exports are generated automatically when you save (on navigation or manual save).

## Troubleshooting

**Problem**: "No module named 'PySide6'"
- **Solution**: Run `pip install -r requirements.txt`

**Problem**: Images don't load
- **Solution**: Make sure your images are in common formats (JPG, PNG, BMP, TIFF, WEBP)

**Problem**: Can't build executable
- **Solution**: Make sure PyInstaller is installed: `pip install pyinstaller`

## Need Help?

Check the full README.md for more detailed information and keyboard shortcuts.
