#!/usr/bin/env python3
"""
Sidebar Navigation Widget
Provides collapsible navigation for different app sections
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QSizePolicy, QSpacerItem)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class SidebarButton(QPushButton):
    """Custom sidebar button with hover effects"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(44)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 10px 14px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
                color: #444444;
                margin: 2px 8px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                color: #222222;
            }
            QPushButton:checked {
                background-color: #0078d4;
                color: white;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)


class Sidebar(QWidget):
    """Collapsible sidebar navigation widget"""
    
    tab_changed = pyqtSignal(int)  # Signal emitted when tab changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Configure widths
        self.collapsed_width = 60
        # Start expanded
        self.setMinimumWidth(250)
        self.setMaximumWidth(250)
        self.is_collapsed = False
        self.button_texts = []  # Store button texts for restoration
        self.button_icons = []  # Store icon-only texts
        
        self.setup_ui()
        self.setup_animations()
        
        # Set initial style
        self.setStyleSheet("""
            QWidget {
                background-color: #f7f7f9;
                border-right: 1px solid #e0e0e0;
            }
        """)
    
    def setup_ui(self):
        """Set up the sidebar UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header section
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(80)
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        
        header_layout = QVBoxLayout(self.header_frame)
        header_layout.setContentsMargins(16, 16, 16, 16)
        
        # App title
        title_label = QLabel("Riftbound TCG")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #0078d4;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Collection Manager")
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setStyleSheet("color: #666666;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        layout.addWidget(self.header_frame)
        
        # Navigation buttons
        self.nav_buttons = []
        
        # Search button
        self.search_btn = SidebarButton("🔍 Search Cards")
        self.search_btn.clicked.connect(lambda: self.on_tab_clicked(0))
        self.nav_buttons.append(self.search_btn)
        self.button_texts.append("🔍 Search Cards")
        self.button_icons.append("🔍")
        layout.addWidget(self.search_btn)
        
        # Collection button
        self.collection_btn = SidebarButton("📚 Collection")
        self.collection_btn.clicked.connect(lambda: self.on_tab_clicked(1))
        self.nav_buttons.append(self.collection_btn)
        self.button_texts.append("📚 Collection")
        self.button_icons.append("📚")
        layout.addWidget(self.collection_btn)
        
        # Statistics button
        self.stats_btn = SidebarButton("📊 Statistics")
        self.stats_btn.clicked.connect(lambda: self.on_tab_clicked(2))
        self.nav_buttons.append(self.stats_btn)
        self.button_texts.append("📊 Statistics")
        self.button_icons.append("📊")
        layout.addWidget(self.stats_btn)
        
        # Settings button
        self.settings_btn = SidebarButton("⚙️ Settings")
        self.settings_btn.clicked.connect(lambda: self.on_tab_clicked(3))
        self.nav_buttons.append(self.settings_btn)
        self.button_texts.append("⚙️ Settings")
        self.button_icons.append("⚙️")
        layout.addWidget(self.settings_btn)
        
        # Add stretch to push buttons to the top
        layout.addStretch()
        
        # Collapse/expand button
        self.toggle_btn = QPushButton("◀")
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 20px;
                font-size: 16px;
                color: #666666;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                color: #333333;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        
        # Position toggle button at bottom right
        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.toggle_btn)
        layout.addLayout(toggle_layout)
        
        # Set first button as active
        self.search_btn.setChecked(True)
    
    def setup_animations(self):
        """Set up collapse/expand animations"""
        self.collapse_animation = QPropertyAnimation(self, b"maximumWidth")
        self.collapse_animation.setDuration(300)
        self.collapse_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.expand_animation = QPropertyAnimation(self, b"maximumWidth")
        self.expand_animation.setDuration(300)
        self.expand_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def toggle_sidebar(self):
        """Toggle sidebar between collapsed and expanded states"""
        if self.is_collapsed:
            self.expand_sidebar()
        else:
            self.collapse_sidebar()
    
    def collapse_sidebar(self):
        """Collapse the sidebar"""
        self.is_collapsed = True
        # Ensure we can shrink
        self.setMinimumWidth(self.collapsed_width)
        self.collapse_animation.stop()
        self.expand_animation.stop()
        self.collapse_animation.setStartValue(self.width())
        self.collapse_animation.setEndValue(self.collapsed_width)
        self.collapse_animation.start()
        
        # Update toggle button
        self.toggle_btn.setText("▶")
        
        # Hide header and set icon-only text
        self.header_frame.setVisible(False)
        for i, btn in enumerate(self.nav_buttons):
            btn.setToolTip(self.button_texts[i])
            btn.setText(self.button_icons[i])
    
    def expand_sidebar(self):
        """Expand the sidebar"""
        self.is_collapsed = False
        self.expand_animation.stop()
        self.collapse_animation.stop()
        self.expand_animation.setStartValue(self.width())
        self.expand_animation.setEndValue(250)
        self.expand_animation.start()
        
        # Update toggle button
        self.toggle_btn.setText("◀")
        
        # Show header and restore full text
        self.header_frame.setVisible(True)
        for i, btn in enumerate(self.nav_buttons):
            btn.setText(self.button_texts[i])
    
    def on_tab_clicked(self, tab_index):
        """Handle tab button clicks"""
        # Uncheck all buttons
        for btn in self.nav_buttons:
            btn.setChecked(False)
        
        # Check clicked button
        self.nav_buttons[tab_index].setChecked(True)
        
        # Emit signal
        self.tab_changed.emit(tab_index)
    
    def set_active_tab(self, tab_index):
        """Set the active tab programmatically"""
        if 0 <= tab_index < len(self.nav_buttons):
            self.on_tab_clicked(tab_index)
