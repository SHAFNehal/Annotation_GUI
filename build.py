"""Build script for creating standalone executable"""
import PyInstaller.__main__
import sys
import os
from pathlib import Path


def build_executable():
    """Build standalone executable using PyInstaller"""
    # Get script directory
    script_dir = Path(__file__).parent
    
    # PyInstaller arguments
    # Platform-specific path separator for --add-data
    if sys.platform == 'win32':
        data_sep = ';'
    else:
        data_sep = ':'
    
    args = [
        'main.py',
        '--name=AnnotationGUI',
        '--onefile',
        '--windowed',  # No console window
        '--clean',
        '--noconfirm',
        f'--add-data=src{data_sep}src',  # Include src package
    ]
    
    # Platform-specific options
    if sys.platform == 'win32':
        args.append('--icon=NONE')  # Add icon path if you have one
    elif sys.platform == 'darwin':
        args.append('--osx-bundle-identifier=com.annotationgui.app')
    
    print("Building standalone executable...")
    print(f"Arguments: {' '.join(args)}")
    
    PyInstaller.__main__.run(args)
    
    print("\nBuild complete!")
    print(f"Executable location: {script_dir / 'dist' / 'AnnotationGUI'}")
    if sys.platform == 'win32':
        print(f"Windows executable: {script_dir / 'dist' / 'AnnotationGUI.exe'}")
    elif sys.platform == 'darwin':
        print(f"macOS app: {script_dir / 'dist' / 'AnnotationGUI.app'}")
    else:
        print(f"Linux executable: {script_dir / 'dist' / 'AnnotationGUI'}")


if __name__ == "__main__":
    build_executable()
