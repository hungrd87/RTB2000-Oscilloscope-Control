#!/usr/bin/env python3
"""
Main entry point for RTB2000 Oscilloscope Control GUI
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication


def main():
    """Main application entry point"""
    # Create QApplication first
    app = QApplication(sys.argv)
    app.setApplicationName("RTB2000 Control")
    app.setApplicationVersion("1.0.0")
    
    # Import after QApplication is created
    from rtb2000_control.gui.main_window import MainWindow
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
