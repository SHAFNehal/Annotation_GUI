"""Main entry point for Annotation GUI application"""
import sys
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Annotation GUI")
    app.setOrganizationName("AnnotationGUI")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
