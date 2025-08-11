#!/usr/bin/env python3
"""
Riftbound TCG Collection Management
Main application entry point
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QLabel, QTabWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.card_database import CardDatabase
from src.ui.search_widget import SearchWidget
from src.utils.data_importer import DataImporter

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Riftbound TCG Collection Management")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize database
        self.database = CardDatabase()
        
        # Set up the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        layout = QVBoxLayout(central_widget)
        
        # Header
        header_label = QLabel("Riftbound TCG Collection Management")
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setStyleSheet("color: #0078d4; margin: 10px;")
        layout.addWidget(header_label)
        
        # Tab widget for different sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Search tab
        self.search_widget = SearchWidget(self.database)
        self.tab_widget.addTab(self.search_widget, "🔍 Search Cards")
        
        # Collection tab (placeholder)
        collection_widget = QWidget()
        collection_layout = QVBoxLayout(collection_widget)
        collection_layout.addWidget(QLabel("Collection Management - Coming Soon!"))
        self.tab_widget.addTab(collection_widget, "📚 Collection")
        
        # Stats tab (placeholder)
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.addWidget(QLabel("Collection Statistics - Coming Soon!"))
        self.tab_widget.addTab(stats_widget, "📊 Statistics")
        
        # Connect search widget signals
        self.search_widget.card_selected.connect(self.on_card_selected)
        
        # Check if database needs initial import
        self.check_database_import()
    
    def check_database_import(self):
        """Check if database needs initial import from JSON files"""
        try:
            # Try to get some cards from database
            cards = self.database.search_cards()
            
            if not cards:
                # Database is empty, offer to import
                reply = QMessageBox.question(
                    self,
                    "Database Empty",
                    "No cards found in database. Would you like to import from JSON files?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.import_initial_data()
            else:
                print(f"Database already contains {len(cards)} cards")
                
        except Exception as e:
            print(f"Error checking database: {str(e)}")
    
    def import_initial_data(self):
        """Import initial card data from JSON files"""
        try:
            importer = DataImporter(self.database)
            importer.import_all_sets()
            
            QMessageBox.information(
                self,
                "Import Complete",
                "Card data has been successfully imported into the database!"
            )
            
            # Refresh search widget dropdowns
            self.search_widget.populate_dropdowns()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Error importing card data: {str(e)}"
            )
    
    def on_card_selected(self, card):
        """Handle card selection from search results"""
        print(f"Selected card: {card.name} ({card.set_name})")
        # TODO: Show card details dialog or update collection info

def main():
    """Main application entry point"""
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
