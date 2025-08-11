#!/usr/bin/env python3
"""
Content Area Widget
Manages different app sections and handles tab switching
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.ui.search_widget import SearchWidget


class ContentArea(QWidget):
    """Content area that manages different app sections"""
    
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the content area UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        
        # Create stacked widget for different sections
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Create different sections
        self.create_search_section()
        self.create_collection_section()
        self.create_statistics_section()
        self.create_settings_section()
    
    def create_search_section(self):
        """Create the search section"""
        self.search_widget = SearchWidget(self.database)
        self.stacked_widget.addWidget(self.search_widget)
    
    def create_collection_section(self):
        """Create the collection management section"""
        collection_widget = QWidget()
        collection_layout = QVBoxLayout(collection_widget)
        collection_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("Collection Management")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Manage your card collection, track conditions, and organize your cards")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(subtitle_label)
        
        collection_layout.addWidget(header_frame)
        
        # Placeholder content
        placeholder = QLabel("Collection management features coming soon!\n\n• Add/remove cards from collection\n• Track card conditions\n• Set acquisition dates\n• Add personal notes and tags\n• Organize by categories")
        placeholder.setFont(QFont("Arial", 12))
        placeholder.setStyleSheet("color: #666666; padding: 40px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        collection_layout.addWidget(placeholder)
        
        collection_layout.addStretch()
        self.stacked_widget.addWidget(collection_widget)
    
    def create_statistics_section(self):
        """Create the statistics section"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("Collection Statistics")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("View detailed statistics about your collection and track its value")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(subtitle_label)
        
        stats_layout.addWidget(header_frame)
        
        # Placeholder content
        placeholder = QLabel("Statistics features coming soon!\n\n• Collection overview\n• Set completion percentages\n• Rarity distribution\n• Value tracking via Cardmarket API\n• Collection growth over time\n• Export reports")
        placeholder.setFont(QFont("Arial", 12))
        placeholder.setStyleSheet("color: #666666; padding: 40px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(placeholder)
        
        stats_layout.addStretch()
        self.stacked_widget.addWidget(stats_widget)
    
    def create_settings_section(self):
        """Create the settings section"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("Settings")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Configure application preferences and manage your data")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(subtitle_label)
        
        settings_layout.addWidget(header_frame)
        
        # Placeholder content
        placeholder = QLabel("Settings features coming soon!\n\n• Application preferences\n• Database management\n• Import/export settings\n• Cardmarket API configuration\n• Theme and appearance\n• Backup and restore")
        placeholder.setFont(QFont("Arial", 12))
        placeholder.setStyleSheet("color: #666666; padding: 40px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(placeholder)
        
        settings_layout.addStretch()
        self.stacked_widget.addWidget(settings_widget)
    
    def switch_to_tab(self, tab_index):
        """Switch to the specified tab"""
        if 0 <= tab_index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(tab_index)
    
    def get_search_widget(self):
        """Get the search widget for signal connections"""
        return self.search_widget
