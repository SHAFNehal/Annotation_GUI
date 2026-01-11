"""Main application window"""
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QComboBox,
    QGroupBox, QMessageBox, QFileDialog, QMenuBar, QMenu, QToolBar,
    QStatusBar, QLineEdit, QInputDialog, QColorDialog
)
from pathlib import Path
from typing import List, Optional

from .project_manager import ProjectManager
from .annotation_scene import AnnotationScene
from .image_viewer import ImageViewer
from .commands import CommandHistory, CreateBoxCommand, DeleteBoxCommand, DeleteBoxesCommand, MoveBoxCommand, ResizeBoxCommand, ChangeClassCommand
from .exporters import ExportManager
from .models import Annotation


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Annotation GUI")
        self.setMinimumSize(1200, 800)
        
        # Core components
        self.project_manager = ProjectManager()
        self.command_history = CommandHistory()
        self.scene: Optional[AnnotationScene] = None
        self.viewer: Optional[ImageViewer] = None
        
        # UI components
        self.image_list: Optional[QListWidget] = None
        self.class_list: Optional[QListWidget] = None
        self.class_combo: Optional[QComboBox] = None
        self.status_label: Optional[QLabel] = None
        
        self.setup_ui()
        self.setup_shortcuts()
        
    def setup_ui(self):
        """Setup user interface"""
        # Menu bar
        self.create_menu_bar()
        
        # Toolbar
        self.create_toolbar()
        
        # Status bar
        self.create_status_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left sidebar
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        splitter.setStretchFactor(0, 0)
        
        # Center canvas
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)
        splitter.setStretchFactor(1, 1)
        
        # Right panel
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(2, 0)
        
        # Set splitter sizes
        splitter.setSizes([250, 800, 200])
        
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("&Open Folder...", self.open_folder, QKeySequence.Open)
        file_menu.addAction("&Save Project", self.save_project, QKeySequence.Save)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close, QKeySequence.Quit)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction("&Undo", self.undo, QKeySequence.Undo)
        edit_menu.addAction("&Redo", self.redo, QKeySequence.Redo)
        edit_menu.addSeparator()
        edit_menu.addAction("Select &All", self.select_all_boxes, QKeySequence.SelectAll)
        edit_menu.addAction("&Delete Selected", self.delete_selected_boxes, QKeySequence.Delete)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("Fit to &Window", self.fit_to_window, "Ctrl+0")
        view_menu.addAction("&100% Zoom", self.zoom_100, "Ctrl+1")
        view_menu.addAction("Zoom &In", self.zoom_in, "Ctrl++")
        view_menu.addAction("Zoom &Out", self.zoom_out, "Ctrl+-")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&About", self.show_about)
        help_menu.addAction("Keyboard &Shortcuts", self.show_shortcuts)
        
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Tool buttons
        self.select_tool_btn = QPushButton("Select (S)")
        self.select_tool_btn.setCheckable(True)
        self.select_tool_btn.setChecked(True)
        self.select_tool_btn.clicked.connect(lambda: self.set_tool("select"))
        toolbar.addWidget(self.select_tool_btn)
        
        self.box_tool_btn = QPushButton("Box (B)")
        self.box_tool_btn.setCheckable(True)
        self.box_tool_btn.clicked.connect(lambda: self.set_tool("box"))
        toolbar.addWidget(self.box_tool_btn)
        
        self.pan_tool_btn = QPushButton("Pan (H)")
        self.pan_tool_btn.setCheckable(True)
        self.pan_tool_btn.clicked.connect(lambda: self.set_tool("pan"))
        toolbar.addWidget(self.pan_tool_btn)
        
        toolbar.addSeparator()
        
        # Navigation
        prev_btn = QPushButton("← Previous")
        prev_btn.clicked.connect(self.previous_image)
        toolbar.addWidget(prev_btn)
        
        next_btn = QPushButton("Next →")
        next_btn.clicked.connect(self.next_image)
        toolbar.addWidget(next_btn)
        
        toolbar.addSeparator()
        
        # Zoom
        fit_btn = QPushButton("Refresh")
        fit_btn.clicked.connect(self.fit_to_window)
        toolbar.addWidget(fit_btn)
        
    def create_status_bar(self):
        """Create status bar"""
        self.statusBar().showMessage("Ready")
        self.status_label = QLabel("No project loaded")
        self.statusBar().addPermanentWidget(self.status_label)
        
    def create_left_panel(self) -> QWidget:
        """Create left sidebar panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        label = QLabel("Images")
        layout.addWidget(label)
        
        # Image list
        self.image_list = QListWidget()
        self.image_list.itemDoubleClicked.connect(self.on_image_list_double_click)
        layout.addWidget(self.image_list)
        
        # Status
        self.image_count_label = QLabel("0 images")
        layout.addWidget(self.image_count_label)
        
        return panel
        
    def create_center_panel(self) -> QWidget:
        """Create center canvas panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scene and viewer
        self.scene = AnnotationScene(self.project_manager)
        self.viewer = ImageViewer(self.scene)
        
        # Connect signals
        self.scene.box_created.connect(self.on_box_created)
        
        layout.addWidget(self.viewer)
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Create right panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Classes label
        label = QLabel("Classes")
        layout.addWidget(label)
        
        # Class list
        self.class_list = QListWidget()
        self.class_list.itemDoubleClicked.connect(self.on_class_double_click)
        self.class_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.class_list.customContextMenuRequested.connect(self.show_class_context_menu)
        layout.addWidget(self.class_list)
        
        # Add class button
        add_class_btn = QPushButton("Add Class")
        add_class_btn.clicked.connect(self.add_class)
        layout.addWidget(add_class_btn)
        
        # Delete class button
        delete_class_btn = QPushButton("Delete Class")
        delete_class_btn.clicked.connect(self.delete_selected_class)
        layout.addWidget(delete_class_btn)
        
        layout.addStretch()
        
        # Box properties
        props_group = QGroupBox("Box Properties")
        props_layout = QVBoxLayout(props_group)
        
        self.box_info_label = QLabel("No box selected")
        props_layout.addWidget(self.box_info_label)
        
        class_label = QLabel("Class:")
        props_layout.addWidget(class_label)
        
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.on_class_changed)
        props_layout.addWidget(self.class_combo)
        
        delete_box_btn = QPushButton("Delete Box")
        delete_box_btn.clicked.connect(self.delete_selected_boxes)
        props_layout.addWidget(delete_box_btn)
        
        layout.addWidget(props_group)
        
        return panel
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Tool shortcuts
        QShortcut("S", self, lambda: self.set_tool("select"))
        QShortcut("B", self, lambda: self.set_tool("box"))
        QShortcut("H", self, lambda: self.set_tool("pan"))
        
        # Navigation
        QShortcut("Left", self, self.previous_image)
        QShortcut("Right", self, self.next_image)
        QShortcut("A", self, self.previous_image)
        QShortcut("D", self, self.next_image)
        QShortcut("Home", self, lambda: self.set_current_image(0))
        QShortcut("End", self, lambda: self.set_current_image(len(self.project_manager.project.images) - 1 if self.project_manager.project else 0))
        
        # Number keys for classes
        for i in range(10):
            QShortcut(str(i), self, lambda idx=i: self.assign_class_by_index(idx))
            
        # Box operations
        QShortcut("Escape", self, self.deselect_all_boxes)
        
    def open_folder(self):
        """Open image folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not folder:
            return
        
        # Check if project.json already exists
        project_path = Path(folder).parent / "project.json"
        if project_path.exists():
            # Load existing project (will import annotations from exports)
            if self.project_manager.load_project(str(project_path)):
                self.load_project_ui()
                QMessageBox.information(self, "Project Loaded", 
                    f"Loaded existing project with {len(self.project_manager.project.images)} images.\n"
                    "Existing annotations from exports folder have been imported if available.")
            else:
                QMessageBox.warning(self, "Error", "Failed to load existing project.")
        else:
            # Create new project (will import annotations from exports if available)
            if self.project_manager.create_project(folder, str(project_path)):
                self.load_project_ui()
                # Check if annotations were imported
                total_annotations = sum(len(img.annotations) for img in self.project_manager.project.images)
                if total_annotations > 0:
                    QMessageBox.information(self, "Annotations Imported", 
                        f"Found and imported {total_annotations} existing annotations from exports folder.")
            else:
                QMessageBox.warning(self, "Error", "Failed to load images from folder")
            
    def load_project_ui(self):
        """Load project UI"""
        if not self.project_manager.project:
            return
            
        # Load image list
        self.image_list.clear()
        for i, img_data in enumerate(self.project_manager.project.images):
            item = QListWidgetItem(img_data.filename)
            item.setData(Qt.UserRole, i)
            # Check if annotated
            if img_data.annotations:
                item.setText(f"✓ {img_data.filename}")
            self.image_list.addItem(item)
            
        # Load class list
        self.update_class_list()
        
        # Load first image
        if self.project_manager.project.images:
            self.set_current_image(0)
            
        self.update_status()
        
    def update_class_list(self):
        """Update class list widget"""
        self.class_list.clear()
        self.class_combo.clear()
        
        if not self.project_manager.project:
            return
            
        for i, cls in enumerate(self.project_manager.project.classes):
            # List widget
            item = QListWidgetItem(f"{i}: {cls.name}")
            item.setData(Qt.UserRole, cls.id)
            color = QColor(cls.color)
            item.setForeground(color)
            self.class_list.addItem(item)
            
            # Combo box
            self.class_combo.addItem(cls.name, cls.id)
            
    def set_current_image(self, index: int):
        """Set current image"""
        if not self.project_manager.set_current_image(index):
            return
            
        image_data = self.project_manager.get_current_image()
        if not image_data:
            return
            
        # Load image in scene
        self.scene.load_image(image_data)
        self.viewer.fit_to_window()
        
        # Update image list selection
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            if item.data(Qt.UserRole) == index:
                self.image_list.setCurrentItem(item)
                break
                
        self.update_status()
        self.update_box_properties()
        
    def next_image(self):
        """Navigate to next image"""
        if not self.project_manager.project:
            return
        current = self.project_manager.current_image_index
        if current < len(self.project_manager.project.images) - 1:
            self.save_current_annotations()
            self.set_current_image(current + 1)
            
    def previous_image(self):
        """Navigate to previous image"""
        if not self.project_manager.project:
            return
        current = self.project_manager.current_image_index
        if current > 0:
            self.save_current_annotations()
            self.set_current_image(current - 1)
            
    def save_current_annotations(self):
        """Save current image annotations"""
        if not self.project_manager.project:
            return
        
        # Ensure current image annotations are synced from scene
        if self.scene and self.scene.current_image_data:
            image_data = self.project_manager.get_current_image()
            if image_data:
                # Sync annotations from scene to project (they should already be the same reference)
                # But ensure all boxes in scene are in the annotations list
                scene_annotations = [box_item.annotation for box_item in self.scene.box_items]
                # Update the annotations list to match scene
                image_data.annotations = scene_annotations
        
        # Save project and auto-export
        if self.project_manager.save_project():
            if self.project_manager.project_path:
                ExportManager.export_all(self.project_manager.project, self.project_manager.project_path)
                
    def set_tool(self, tool: str):
        """Set current tool"""
        self.viewer.set_tool(tool)
        self.select_tool_btn.setChecked(tool == "select")
        self.box_tool_btn.setChecked(tool == "box")
        self.pan_tool_btn.setChecked(tool == "pan")
        
    def on_image_list_double_click(self, item: QListWidgetItem):
        """Handle image list double click"""
        index = item.data(Qt.UserRole)
        self.save_current_annotations()
        self.set_current_image(index)
        
    def on_box_created(self, annotation: Annotation):
        """Handle box creation"""
        # Create command
        image_data = self.project_manager.get_current_image()
        if image_data:
            cmd = CreateBoxCommand(image_data, annotation)
            self.command_history.execute_command(cmd)
            
            # Force view update to show the new box
            if self.viewer:
                self.viewer.viewport().update()
                self.viewer.update()
            if self.scene:
                self.scene.update()
                
            self.update_status()
            self.update_box_properties()
            
    def select_all_boxes(self):
        """Select all boxes"""
        if self.scene:
            self.scene.select_all_boxes()
            self.update_box_properties()
            
    def deselect_all_boxes(self):
        """Deselect all boxes"""
        if self.scene:
            self.scene.deselect_all_boxes()
            self.update_box_properties()
            
    def delete_selected_boxes(self):
        """Delete selected boxes"""
        if not self.scene:
            return
        selected = self.scene.get_selected_boxes()
        if not selected:
            return
            
        image_data = self.project_manager.get_current_image()
        if not image_data:
            return
            
        # Create command
        if len(selected) == 1:
            cmd = DeleteBoxCommand(image_data, selected[0])
        else:
            cmd = DeleteBoxesCommand(image_data, selected)
        self.command_history.execute_command(cmd)
        
        # Remove from scene
        for box_item in self.scene.box_items[:]:
            if box_item.annotation in selected:
                self.scene.remove_box_item(box_item)
                
        self.update_status()
        self.update_box_properties()
        
    def on_class_double_click(self, item: QListWidgetItem):
        """Handle class double click - assign to selected boxes"""
        class_id = item.data(Qt.UserRole)
        self.assign_class(class_id)
        
    def assign_class_by_index(self, index: int):
        """Assign class by index (0-9)"""
        if not self.project_manager.project:
            return
        if 0 <= index < len(self.project_manager.project.classes):
            class_id = self.project_manager.project.classes[index].id
            self.assign_class(class_id)
            
    def assign_class(self, class_id: int):
        """Assign class to selected boxes"""
        if not self.scene or not self.project_manager.project:
            return
        selected = self.scene.get_selected_boxes()
        if not selected:
            # If no selection, assign to last created box
            image_data = self.project_manager.get_current_image()
            if image_data and image_data.annotations:
                selected = [image_data.annotations[-1]]
                
        if not selected:
            return
            
        # Get class name
        cls = self.project_manager.get_class(class_id)
        if not cls:
            return
            
        # Create command
        cmd = ChangeClassCommand(selected, class_id, cls.name)
        self.command_history.execute_command(cmd)
        
        # Update scene
        self.scene.update_box_colors()
        self.update_box_properties()
        
    def on_class_changed(self, index: int):
        """Handle class combo box change"""
        if index < 0:
            return
        class_id = self.class_combo.itemData(index)
        if class_id is not None:
            self.assign_class(class_id)
            
    def update_box_properties(self):
        """Update box properties panel"""
        if not self.scene:
            self.box_info_label.setText("No box selected")
            return
            
        selected = self.scene.get_selected_boxes()
        if not selected:
            self.box_info_label.setText("No box selected")
            return
            
        if len(selected) == 1:
            ann = selected[0]
            self.box_info_label.setText(
                f"Class: {ann.class_name}\n"
                f"x_min: {ann.x_min}, y_min: {ann.y_min}\n"
                f"x_max: {ann.x_max}, y_max: {ann.y_max}"
            )
            # Set combo to current class
            for i in range(self.class_combo.count()):
                if self.class_combo.itemData(i) == ann.class_id:
                    self.class_combo.setCurrentIndex(i)
                    break
        else:
            self.box_info_label.setText(f"{len(selected)} boxes selected")
            
    def add_class(self):
        """Add a new class"""
        if not self.project_manager.project:
            return
        name, ok = QInputDialog.getText(self, "Add Class", "Class name:")
        if not ok or not name:
            return
        color = QColorDialog.getColor(QColor("#FF0000"), self, "Select Color")
        if not color.isValid():
            return
        class_id = self.project_manager.add_class(name, color.name())
        self.update_class_list()
        
    def show_class_context_menu(self, pos):
        """Show class context menu"""
        item = self.class_list.itemAt(pos)
        if not item:
            return
        class_id = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.class_list.mapToGlobal(pos))
        
        if action == edit_action:
            self.edit_class(class_id)
        elif action == delete_action:
            self.delete_class(class_id)
            
    def edit_class(self, class_id: int):
        """Edit a class"""
        cls = self.project_manager.get_class(class_id)
        if not cls:
            return
        name, ok = QInputDialog.getText(self, "Edit Class", "Class name:", text=cls.name)
        if ok and name:
            cls.name = name
            color = QColorDialog.getColor(QColor(cls.color), self, "Select Color")
            if color.isValid():
                cls.color = color.name()
            self.update_class_list()
            self.scene.update_box_colors()
            
    def delete_selected_class(self):
        """Delete the selected class from the class list"""
        if not self.project_manager.project:
            return
        
        # Get selected item from class list
        selected_items = self.class_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a class to delete.")
            return
        
        item = selected_items[0]
        class_id = item.data(Qt.UserRole)
        self.delete_class(class_id)
        
    def delete_class(self, class_id: int):
        """Delete a class"""
        # Check if used
        used = False
        for img_data in self.project_manager.project.images:
            for ann in img_data.annotations:
                if ann.class_id == class_id:
                    used = True
                    break
            if used:
                break
        if used:
            QMessageBox.warning(self, "Cannot Delete", "This class is used by annotations.")
            return
        # Remove class
        self.project_manager.project.classes = [c for c in self.project_manager.project.classes if c.id != class_id]
        # Reindex
        for i, cls in enumerate(self.project_manager.project.classes):
            cls.id = i
        self.update_class_list()
        # Update box colors in case any boxes were using this class
        if self.scene:
            self.scene.update_box_colors()
        
    def undo(self):
        """Undo last command"""
        if self.command_history.undo():
            # Reload current image to reflect changes
            self.set_current_image(self.project_manager.current_image_index)
            
    def redo(self):
        """Redo last command"""
        if self.command_history.redo():
            # Reload current image to reflect changes
            self.set_current_image(self.project_manager.current_image_index)
            
    def save_project(self):
        """Save project"""
        self.save_current_annotations()
        QMessageBox.information(self, "Saved", "Project saved successfully.")
        
    def fit_to_window(self):
        """Fit image to window"""
        if self.viewer:
            self.viewer.fit_to_window()
            
    def zoom_100(self):
        """Zoom to 100%"""
        if self.viewer:
            self.viewer.zoom_100()
            
    def zoom_in(self):
        """Zoom in"""
        if self.viewer:
            self.viewer.zoom_in()
            
    def zoom_out(self):
        """Zoom out"""
        if self.viewer:
            self.viewer.zoom_out()
            
    def update_status(self):
        """Update status bar"""
        if not self.project_manager.project:
            self.status_label.setText("No project loaded")
            return
            
        current = self.project_manager.current_image_index
        total = len(self.project_manager.project.images)
        image_data = self.project_manager.get_current_image()
        box_count = len(image_data.annotations) if image_data else 0
        
        self.status_label.setText(f"Image {current + 1} of {total} | {box_count} boxes")
        
        # Update image count
        annotated = sum(1 for img in self.project_manager.project.images if img.annotations)
        self.image_count_label.setText(f"{total} images, {annotated} annotated")
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", "Annotation GUI\n\nA bounding box annotation tool\nfor computer vision projects.")
        
    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts = """
Keyboard Shortcuts:

Navigation:
  ← / → or A / D - Previous/Next image
  Home / End - First/Last image

Tools:
  S - Select tool
  B - Box (draw) tool
  H - Pan tool

Box Operations:
  Delete / Backspace - Delete selected box(es)
  Ctrl+A - Select all boxes
  Escape - Deselect all
  1-9, 0 - Assign class by number

Zoom:
  Ctrl + Mouse Wheel - Zoom in/out
  Ctrl+0 - Fit to window
  Ctrl+1 - 100% zoom
  Ctrl++ / Ctrl+- - Zoom in/out

General:
  Ctrl+Z - Undo
  Ctrl+Y - Redo
  Ctrl+S - Save
  Ctrl+O - Open folder
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts)
        
    def closeEvent(self, event):
        """Handle close event"""
        self.save_current_annotations()
        event.accept()
