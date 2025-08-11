#!/usr/bin/env python3
"""
Riftbound TCG Collection Management - Piltover Archive Edition
Main application entry point using the new Piltover Archive database
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QWidget, 
                             QMessageBox, QVBoxLayout, QPushButton, QLabel)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QMovie

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.piltover_card_database import PiltoverCardDatabase
from src.ui.sidebar import Sidebar
from src.ui.content_area import ContentArea
from src.update_local_database import LocalDatabaseUpdater


class DatabaseUpdateWorker(QThread):
    """Background worker for database updates"""
    update_complete = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.updater = LocalDatabaseUpdater()
    
    def run(self):
        """Run database update in background"""
        try:
            success = self.updater.update_database()
            if success:
                self.update_complete.emit(True, "Database updated successfully from cards.json")
            else:
                self.update_complete.emit(False, "Database update failed")
        except Exception as e:
            self.update_complete.emit(False, f"Error during update: {str(e)}")


class PiltoverMainWindow(QMainWindow):
    """Main application window using Piltover Archive database"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Riftbound TCG Collection Management - Piltover Archive")
        self.setGeometry(100, 100, 1600, 900)
        
        # Initialize Piltover database
        self.database = PiltoverCardDatabase()
        
        # Set up the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = Sidebar()
        layout.addWidget(self.sidebar)
        
        # Create content area
        self.content_area = ContentArea(self.database)
        layout.addWidget(self.content_area)
        
        # Connect sidebar signals
        self.sidebar.tab_changed.connect(self.content_area.switch_to_tab)
        
        # Connect search widget signals
        search_widget = self.content_area.get_search_widget()
        search_widget.card_selected.connect(self.on_card_selected)
        
        # Don't start database update here - wait until window is shown
        self.update_worker = None
    
    def showEvent(self, event):
        """Called when the window is shown - safe to start database update"""
        super().showEvent(event)
        # Start automatic database update after window is shown
        self.start_database_update()
    
    def start_database_update(self):
        """Start automatic database update on startup"""
        print("🔄 Starting automatic database update from cards.json...")
        
        # Create and start update worker
        self.update_worker = DatabaseUpdateWorker()
        self.update_worker.update_complete.connect(self.on_update_complete)
        self.update_worker.start()
    
    def on_update_complete(self, success: bool, message: str):
        """Handle database update completion"""
        if success:
            print(f"✅ {message}")
            # Refresh the search widget to show updated data (now deferred until after update)
            search_widget = self.content_area.get_search_widget()
            search_widget.populate_dropdowns()
            search_widget.perform_search()
        else:
            print(f"❌ {message}")
            # Even if update fails, try to load existing data
            try:
                search_widget = self.content_area.get_search_widget()
                search_widget.populate_dropdowns()
                search_widget.perform_search()
            except Exception as e:
                print(f"Error loading existing data: {e}")
    
    def on_card_selected(self, card):
        """Handle card selection from search results"""
        # This will need to be updated to work with PiltoverCard objects
        print(f"Card selected: {card.name if hasattr(card, 'name') else card}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Riftbound TCG Collection Management")
    app.setApplicationVersion("1.2 - Dev Build")
    
    # Create and show main window
    window = PiltoverMainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
