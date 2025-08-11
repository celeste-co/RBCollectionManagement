#!/usr/bin/env python3
"""
Riftbound TCG Collection Management
Main application entry point
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Riftbound TCG Collection Management")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome label
        welcome_label = QLabel("Welcome to Riftbound TCG Collection Management")
        welcome_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Status label
        status_label = QLabel("Application initialized successfully!")
        status_label.setFont(QFont("Arial", 12))
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        # Set window icon (placeholder)
        # self.setWindowIcon(QIcon("resources/icon.png"))

def main():
    """Main application function"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Riftbound TCG Collection Management")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("celeste-co")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
