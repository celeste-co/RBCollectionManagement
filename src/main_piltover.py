#!/usr/bin/env python3
"""
Riftbound TCG Collection Management - Piltover Archive Edition
Main application entry point using the new Piltover Archive database
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QHBoxLayout, QWidget, 
                             QMessageBox, QVBoxLayout, QPushButton, QLabel)
from PyQt6.QtCore import Qt

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.piltover_card_database import PiltoverCardDatabase
from src.ui.sidebar import Sidebar
from src.ui.content_area import ContentArea


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
        
        # Check if database needs initial import
        self.check_database_import()
    
    def check_database_import(self):
        """Check if database needs initial import from Piltover Archive"""
        try:
            # Try to get some cards from database
            cards = self.database.get_all_variants(limit=5)
            
            if not cards:
                # Database is empty, offer to import
                reply = QMessageBox.question(
                    self,
                    "Database Empty",
                    "No cards found in Piltover Archive database. Would you like to import from the sorted JSON file?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.import_piltover_data()
            else:
                print(f"Piltover database already contains {len(cards)} cards")
                
        except Exception as e:
            print(f"Error checking database: {str(e)}")
    
    def import_piltover_data(self):
        """Import Piltover Archive data from sorted JSON file"""
        try:
            # Import from the sorted JSON file
            sorted_json_path = os.path.join(os.path.dirname(__file__), '..', 'card_data', 'cards.json')
            
            if not os.path.exists(sorted_json_path):
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"Sorted JSON file not found: {sorted_json_path}\n\nPlease run the reorganize_piltover_data.py script first."
                )
                return
            
            success = self.database.import_from_sorted_json(sorted_json_path)
            
            if success:
                QMessageBox.information(
                    self,
                    "Import Complete",
                    "Piltover Archive card data has been successfully imported into the database!"
                )
                
                # Refresh library (dropdowns + results)
                search_widget = self.content_area.get_search_widget()
                search_widget.populate_dropdowns()
                search_widget.perform_search()
            else:
                QMessageBox.critical(
                    self,
                    "Import Failed",
                    "Failed to import card data. Please check the console for error messages."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"An error occurred during import: {str(e)}"
            )
    
    def on_card_selected(self, card):
        """Handle card selection from search results"""
        # This will need to be updated to work with PiltoverCard objects
        print(f"Card selected: {card.name if hasattr(card, 'name') else card}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Riftbound TCG Collection Management")
    app.setApplicationVersion("2.0 - Piltover Archive Edition")
    
    # Create and show main window
    window = PiltoverMainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
