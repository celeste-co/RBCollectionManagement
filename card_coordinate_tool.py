#!/usr/bin/env python3
"""
Card Name Coordinate Drawing Tool

This external tool allows users to draw coordinates where card names are located
on Riftbound card images for both Classic and Battlefield card formats.
The coordinates are saved to enable the quiz feature to properly blank out card names.
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFileDialog, QMessageBox,
    QGroupBox, QListWidget, QListWidgetItem, QScrollArea,
    QSplitter, QTextEdit, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QBrush, QColor, QFont,
    QMouseEvent, QPaintEvent, QResizeEvent
)


class CardImageWidget(QWidget):
    """Widget for displaying card image and drawing name coordinates"""
    
    coordinates_changed = pyqtSignal(list)  # Emits list of rectangles
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_pixmap: Optional[QPixmap] = None
        self.original_pixmap: Optional[QPixmap] = None
        self.scale_factor = 1.0
        self.name_rectangles: List[QRect] = []
        self.current_drawing_rect: Optional[QRect] = None
        self.drawing_start_pos: Optional[tuple] = None
        self.is_drawing = False
        
        # Visual settings
        self.rect_color = QColor(255, 0, 0, 100)  # Semi-transparent red
        self.rect_border_color = QColor(255, 0, 0, 255)  # Solid red border
        self.current_rect_color = QColor(0, 255, 0, 100)  # Semi-transparent green
        
        self.setMinimumSize(400, 600)
        self.setMouseTracking(True)
        
        print("🖼️ CardImageWidget initialized")
    
    def load_image(self, image_path: str) -> bool:
        """Load an image file into the widget"""
        try:
            self.original_pixmap = QPixmap(image_path)
            if self.original_pixmap.isNull():
                print(f"❌ Failed to load image: {image_path}")
                return False
            
            self.scale_image_to_fit()
            self.name_rectangles.clear()
            self.current_drawing_rect = None
            self.is_drawing = False
            print(f"✅ Loaded image: {image_path}")
            self.update()
            return True
        except Exception as e:
            print(f"❌ Error loading image {image_path}: {e}")
            return False
    
    def scale_image_to_fit(self):
        """Scale the image to fit within the widget while maintaining aspect ratio"""
        if not self.original_pixmap:
            return
        
        widget_size = self.size()
        image_size = self.original_pixmap.size()
        
        # Calculate scale factor to fit image in widget
        scale_x = widget_size.width() / image_size.width()
        scale_y = widget_size.height() / image_size.height()
        self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up beyond original size
        
        # Scale the pixmap
        new_size = image_size * self.scale_factor
        self.image_pixmap = self.original_pixmap.scaled(
            new_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        
        print(f"🔍 Scaled image: {image_size.width()}x{image_size.height()} -> {new_size.width()}x{new_size.height()} (factor: {self.scale_factor:.2f})")
    
    def resizeEvent(self, event: QResizeEvent):
        """Handle widget resize by rescaling the image"""
        super().resizeEvent(event)
        if self.original_pixmap:
            old_scale = self.scale_factor
            self.scale_image_to_fit()
            
            # Adjust existing rectangles for new scale
            if old_scale != self.scale_factor and old_scale > 0:
                scale_ratio = self.scale_factor / old_scale
                for i, rect in enumerate(self.name_rectangles):
                    self.name_rectangles[i] = QRect(
                        int(rect.x() * scale_ratio),
                        int(rect.y() * scale_ratio),
                        int(rect.width() * scale_ratio),
                        int(rect.height() * scale_ratio)
                    )
            
            self.update()
    
    def paintEvent(self, event: QPaintEvent):
        """Paint the image and name coordinate rectangles"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.image_pixmap:
            # Center the image in the widget
            widget_rect = self.rect()
            image_rect = self.image_pixmap.rect()
            
            x = (widget_rect.width() - image_rect.width()) // 2
            y = (widget_rect.height() - image_rect.height()) // 2
            
            # Draw the image
            painter.drawPixmap(x, y, self.image_pixmap)
            
            # Draw existing name rectangles
            for rect in self.name_rectangles:
                adjusted_rect = QRect(rect.x() + x, rect.y() + y, rect.width(), rect.height())
                painter.setBrush(QBrush(self.rect_color))
                painter.setPen(QPen(self.rect_border_color, 2))
                painter.drawRect(adjusted_rect)
            
            # Draw current drawing rectangle
            if self.current_drawing_rect:
                adjusted_rect = QRect(
                    self.current_drawing_rect.x() + x,
                    self.current_drawing_rect.y() + y,
                    self.current_drawing_rect.width(),
                    self.current_drawing_rect.height()
                )
                painter.setBrush(QBrush(self.current_rect_color))
                painter.setPen(QPen(QColor(0, 255, 0, 255), 2))
                painter.drawRect(adjusted_rect)
    
    def get_image_offset(self) -> Tuple[int, int]:
        """Get the offset of the image within the widget"""
        if not self.image_pixmap:
            return 0, 0
        
        widget_rect = self.rect()
        image_rect = self.image_pixmap.rect()
        
        x = (widget_rect.width() - image_rect.width()) // 2
        y = (widget_rect.height() - image_rect.height()) // 2
        
        return x, y
    
    def widget_to_image_coords(self, widget_x: int, widget_y: int) -> Tuple[int, int]:
        """Convert widget coordinates to image coordinates"""
        offset_x, offset_y = self.get_image_offset()
        image_x = widget_x - offset_x
        image_y = widget_y - offset_y
        return image_x, image_y
    
    def mousePressEvent(self, event: QMouseEvent):
        """Start drawing a rectangle"""
        if event.button() == Qt.MouseButton.LeftButton and self.image_pixmap:
            image_x, image_y = self.widget_to_image_coords(event.pos().x(), event.pos().y())
            
            # Check if click is within image bounds
            if 0 <= image_x <= self.image_pixmap.width() and 0 <= image_y <= self.image_pixmap.height():
                self.is_drawing = True
                self.drawing_start_pos = (image_x, image_y)
                self.current_drawing_rect = QRect(image_x, image_y, 0, 0)
                print(f"🖱️ Started drawing at image coords: ({image_x}, {image_y})")
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Update the current drawing rectangle"""
        if self.is_drawing and self.drawing_start_pos and self.image_pixmap:
            image_x, image_y = self.widget_to_image_coords(event.pos().x(), event.pos().y())
            
            start_x, start_y = self.drawing_start_pos
            
            # Create rectangle from start position to current position
            left = min(start_x, image_x)
            top = min(start_y, image_y)
            width = abs(image_x - start_x)
            height = abs(image_y - start_y)
            
            self.current_drawing_rect = QRect(left, top, width, height)
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Finish drawing a rectangle"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            if self.current_drawing_rect and self.current_drawing_rect.width() > 5 and self.current_drawing_rect.height() > 5:
                # Add the rectangle to the list
                self.name_rectangles.append(QRect(self.current_drawing_rect))
                print(f"➕ Added rectangle: {self.current_drawing_rect}")
                self.coordinates_changed.emit(self.get_coordinates_data())
            
            # Reset drawing state
            self.is_drawing = False
            self.drawing_start_pos = None
            self.current_drawing_rect = None
            self.update()
    
    def clear_rectangles(self):
        """Clear all drawn rectangles"""
        self.name_rectangles.clear()
        self.current_drawing_rect = None
        self.is_drawing = False
        print("🗑️ Cleared all rectangles")
        self.update()
        self.coordinates_changed.emit([])
    
    def get_coordinates_data(self) -> List[Dict]:
        """Get coordinate data scaled to original image dimensions"""
        if not self.original_pixmap or not self.name_rectangles:
            return []
        
        # Scale coordinates back to original image size
        original_size = self.original_pixmap.size()
        scaled_size = self.image_pixmap.size() if self.image_pixmap else original_size
        
        scale_x = original_size.width() / scaled_size.width()
        scale_y = original_size.height() / scaled_size.height()
        
        coordinates = []
        for rect in self.name_rectangles:
            coord_data = {
                'x': int(rect.x() * scale_x),
                'y': int(rect.y() * scale_y),
                'width': int(rect.width() * scale_x),
                'height': int(rect.height() * scale_y)
            }
            coordinates.append(coord_data)
        
        print(f"📏 Generated coordinates for {len(coordinates)} rectangles (scale: {scale_x:.2f}x{scale_y:.2f})")
        return coordinates


class CoordinateToolWindow(QMainWindow):
    """Main window for the coordinate drawing tool"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Riftbound Card Name Coordinate Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Data storage
        self.card_coordinates: Dict[str, Dict] = {}
        self.current_card_format = "classic"  # "classic" or "battlefield"
        self.current_image_path = ""
        self.card_data: Dict = {}
        self.available_cards: List[Dict] = []
        self.current_card_index = 0
        
        # Load existing coordinates if available
        self.coordinates_file = "card_name_coordinates.json"
        self.load_coordinates()
        
        # Load card data for format detection
        self.load_card_data()
        
        self.setup_ui()
        self.load_sample_images()
        
        print("🚀 Coordinate Tool Window initialized")
    
    def setup_ui(self):
        """Set up the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create splitter for main layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        central_layout = QHBoxLayout(central_widget)
        central_layout.addWidget(splitter)
        
        # Left panel - Controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Image display
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
    
    def create_left_panel(self) -> QWidget:
        """Create the left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Header
        header_label = QLabel("Card Name Coordinate Tool")
        header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)
        
        # Instructions
        instructions = QTextEdit()
        instructions.setMaximumHeight(120)
        instructions.setHtml("""
        <b>Instructions:</b><br>
        1. Click "Auto-Load Cards" to start batch processing<br>
        2. Card format is automatically detected<br>
        3. Click and drag to draw rectangles over card names<br>
        4. Press Enter to save and go to next card<br>
        <br>
        <b>Controls:</b><br>
        • Left click + drag: Draw rectangle<br>
        • Enter: Save coordinates and go to next card<br>
        • Escape: Clear all rectangles<br>
        • Manual mode: Load individual images
        """)
        instructions.setReadOnly(True)
        layout.addWidget(instructions)
        
        # Card format selection
        format_group = QGroupBox("Card Format")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Classic", "Battlefield"])
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        
        layout.addWidget(format_group)
        
        # Image selection
        image_group = QGroupBox("Image Selection")
        image_layout = QVBoxLayout(image_group)
        
        load_button = QPushButton("Load Card Image")
        load_button.clicked.connect(self.load_image)
        image_layout.addWidget(load_button)
        
        # Auto-load cards button
        auto_load_button = QPushButton("Auto-Load Cards from Database")
        auto_load_button.clicked.connect(self.start_auto_load_mode)
        auto_load_button.setStyleSheet("""
            QPushButton {
                background-color: #107c10;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0e6e0e;
            }
        """)
        image_layout.addWidget(auto_load_button)
        
        self.image_label = QLabel("No image loaded")
        self.image_label.setWordWrap(True)
        image_layout.addWidget(self.image_label)
        
        # Card navigation (for auto-load mode)
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("← Previous")
        self.prev_button.clicked.connect(self.load_previous_card)
        self.prev_button.setEnabled(False)
        nav_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self.load_next_card)
        self.next_button.setEnabled(False)
        nav_layout.addWidget(self.next_button)
        
        image_layout.addLayout(nav_layout)
        
        # Card info display
        self.card_info_label = QLabel("Press Enter to go to next card")
        self.card_info_label.setWordWrap(True)
        self.card_info_label.setStyleSheet("font-style: italic; color: #666; padding: 5px;")
        image_layout.addWidget(self.card_info_label)
        
        layout.addWidget(image_group)
        
        # Drawing controls
        drawing_group = QGroupBox("Drawing Controls")
        drawing_layout = QVBoxLayout(drawing_group)
        
        clear_button = QPushButton("Clear Rectangles")
        clear_button.clicked.connect(self.clear_rectangles)
        drawing_layout.addWidget(clear_button)
        
        layout.addWidget(drawing_group)
        
        # Coordinates display
        coords_group = QGroupBox("Current Coordinates")
        coords_layout = QVBoxLayout(coords_group)
        
        self.coords_display = QTextEdit()
        self.coords_display.setMaximumHeight(150)
        self.coords_display.setReadOnly(True)
        coords_layout.addWidget(self.coords_display)
        
        layout.addWidget(coords_group)
        
        # Save/Load buttons
        save_group = QGroupBox("Data Management")
        save_layout = QVBoxLayout(save_group)
        
        save_button = QPushButton("Save Coordinates")
        save_button.clicked.connect(self.save_coordinates)
        save_layout.addWidget(save_button)
        
        # Save and next button
        save_next_button = QPushButton("Save & Next Card")
        save_next_button.clicked.connect(self.save_and_next)
        save_next_button.setStyleSheet("""
            QPushButton {
                background-color: #d83b01;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a92d01;
            }
        """)
        save_layout.addWidget(save_next_button)
        
        load_button = QPushButton("Load Coordinates")
        load_button.clicked.connect(self.load_coordinates)
        save_layout.addWidget(load_button)
        
        export_button = QPushButton("Export All Data")
        export_button.clicked.connect(self.export_coordinates)
        save_layout.addWidget(export_button)
        
        layout.addWidget(save_group)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right image display panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Image display
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_widget = CardImageWidget()
        self.image_widget.coordinates_changed.connect(self.on_coordinates_changed)
        scroll_area.setWidget(self.image_widget)
        
        layout.addWidget(scroll_area)
        
        return panel
    
    def load_sample_images(self):
        """Load sample images for testing"""
        # Try to find sample images in the card_img directory
        card_img_dir = Path(__file__).parent / "card_img"
        if card_img_dir.exists():
            print(f"🔍 Looking for sample images in: {card_img_dir}")
            # Look for any .webp files
            sample_files = list(card_img_dir.glob("**/*.webp"))[:5]  # Get first 5 images
            if sample_files:
                print(f"📸 Found {len(sample_files)} sample images")
    
    def on_format_changed(self, format_name: str):
        """Handle card format change"""
        self.current_card_format = format_name.lower()
        print(f"🔄 Card format changed to: {self.current_card_format}")
        
        # Clear current rectangles when format changes
        if hasattr(self, 'image_widget'):
            self.image_widget.clear_rectangles()
    
    def load_image(self):
        """Load a card image for coordinate drawing"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Card Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        
        if file_path:
            if self.image_widget.load_image(file_path):
                self.current_image_path = file_path
                self.image_label.setText(f"Loaded: {Path(file_path).name}")
                print(f"✅ Successfully loaded image: {file_path}")
            else:
                QMessageBox.warning(self, "Error", f"Failed to load image: {file_path}")
    
    def clear_rectangles(self):
        """Clear all drawn rectangles"""
        self.image_widget.clear_rectangles()
    
    def on_coordinates_changed(self, coordinates: List[Dict]):
        """Handle coordinate changes from the image widget"""
        # Display coordinates in the text area
        if coordinates:
            coords_text = "Rectangles (original image scale):\n"
            for i, coord in enumerate(coordinates):
                coords_text += f"{i+1}: x={coord['x']}, y={coord['y']}, w={coord['width']}, h={coord['height']}\n"
        else:
            coords_text = "No rectangles drawn"
        
        self.coords_display.setText(coords_text)
        print(f"📊 Coordinates updated: {len(coordinates)} rectangles")
    
    def save_coordinates(self):
        """Save current coordinates for the loaded image"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "No image loaded!")
            return
        
        coordinates = self.image_widget.get_coordinates_data()
        if not coordinates:
            QMessageBox.warning(self, "Warning", "No coordinates to save!")
            return
        
        # Create a key based on image filename and format
        image_name = Path(self.current_image_path).stem
        key = f"{image_name}_{self.current_card_format}"
        
        # Store coordinates data
        self.card_coordinates[key] = {
            'image_path': self.current_image_path,
            'image_name': image_name,
            'format': self.current_card_format,
            'coordinates': coordinates,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to file
        try:
            with open(self.coordinates_file, 'w', encoding='utf-8') as f:
                json.dump(self.card_coordinates, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "Success", f"Coordinates saved for {key}")
            print(f"💾 Saved coordinates for {key}: {len(coordinates)} rectangles")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save coordinates: {str(e)}")
            print(f"❌ Error saving coordinates: {e}")
    
    def load_coordinates(self):
        """Load coordinates from file"""
        try:
            if os.path.exists(self.coordinates_file):
                with open(self.coordinates_file, 'r', encoding='utf-8') as f:
                    self.card_coordinates = json.load(f)
                print(f"📂 Loaded {len(self.card_coordinates)} coordinate sets from {self.coordinates_file}")
            else:
                self.card_coordinates = {}
                print(f"📄 No existing coordinates file found, starting fresh")
        
        except Exception as e:
            print(f"❌ Error loading coordinates: {e}")
            self.card_coordinates = {}
    
    def export_coordinates(self):
        """Export all coordinate data to a file"""
        if not self.card_coordinates:
            QMessageBox.warning(self, "Warning", "No coordinate data to export!")
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self,
            "Export Coordinates",
            "card_name_coordinates_export.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.card_coordinates, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Success", f"Coordinates exported to {file_path}")
                print(f"📤 Exported coordinates to {file_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export coordinates: {str(e)}")
                print(f"❌ Error exporting coordinates: {e}")
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        from PyQt6.QtCore import Qt
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Enter key pressed - go to next card or save and next
            if self.available_cards and self.current_card_index < len(self.available_cards):
                self.save_and_next()
            else:
                self.load_next_card()
        elif event.key() == Qt.Key.Key_Escape:
            # Escape - clear current rectangles
            self.clear_rectangles()
        else:
            super().keyPressEvent(event)
    
    def load_card_data(self):
        """Load card data from cards.json for format detection"""
        try:
            cards_json_path = Path("card_data/cards.json")
            if cards_json_path.exists():
                with open(cards_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.card_data = {card['variantNumber']: card for card in data.get('variants', [])}
                print(f"📂 Loaded data for {len(self.card_data)} cards")
            else:
                print("📄 No cards.json found - format detection disabled")
                self.card_data = {}
        except Exception as e:
            print(f"❌ Error loading card data: {e}")
            self.card_data = {}
    
    def detect_card_format(self, image_path: str) -> str:
        """Detect if a card is classic or battlefield format based on card data"""
        try:
            # Extract variant number from image path
            image_name = Path(image_path).stem
            
            if image_name in self.card_data:
                card = self.card_data[image_name]
                if card.get('type') == 'Battlefield':
                    print(f"🏛️ Detected battlefield card: {image_name}")
                    return "battlefield"
                else:
                    print(f"🃏 Detected classic card: {image_name} (type: {card.get('type', 'Unknown')})")
                    return "classic"
            else:
                print(f"❓ Card data not found for {image_name}, defaulting to classic")
                return "classic"
        except Exception as e:
            print(f"❌ Error detecting card format: {e}")
            return "classic"
    
    def start_auto_load_mode(self):
        """Start auto-loading cards from the card_img directory"""
        try:
            card_img_dir = Path("card_img")
            if not card_img_dir.exists():
                QMessageBox.warning(self, "Warning", "card_img directory not found!")
                return
            
            # Find all card images
            self.available_cards = []
            for set_dir in card_img_dir.iterdir():
                if set_dir.is_dir() and set_dir.name in ['OGN', 'OGS']:
                    for image_file in set_dir.glob("*.webp"):
                        if image_file.name != "Cardback.webp":
                            self.available_cards.append({
                                'path': str(image_file),
                                'name': image_file.stem,
                                'set': set_dir.name
                            })
            
            if not self.available_cards:
                QMessageBox.warning(self, "Warning", "No card images found!")
                return
            
            # Sort cards by variant number
            self.available_cards.sort(key=lambda x: x['name'])
            self.current_card_index = 0
            
            # Enable navigation
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
            
            # Load first card
            self.load_current_card()
            
            print(f"🚀 Auto-load mode started with {len(self.available_cards)} cards")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start auto-load mode: {str(e)}")
            print(f"❌ Error starting auto-load mode: {e}")
    
    def load_current_card(self):
        """Load the current card in auto-load mode"""
        if not self.available_cards or self.current_card_index >= len(self.available_cards):
            return
        
        card = self.available_cards[self.current_card_index]
        image_path = card['path']
        
        # Auto-detect format
        detected_format = self.detect_card_format(image_path)
        self.current_card_format = detected_format
        self.format_combo.setCurrentText(detected_format.capitalize())
        
        # Load the image
        if self.image_widget.load_image(image_path):
            self.current_image_path = image_path
            
            # Update UI
            card_info = f"Card {self.current_card_index + 1}/{len(self.available_cards)}: {card['name']} ({detected_format})"
            self.image_label.setText(card_info)
            self.card_info_label.setText(f"Format: {detected_format.title()} | Press Enter to save & go to next card")
            
            print(f"📸 Loaded card {self.current_card_index + 1}: {card['name']} ({detected_format})")
        else:
            QMessageBox.warning(self, "Error", f"Failed to load image: {image_path}")
    
    def load_next_card(self):
        """Load the next card in auto-load mode"""
        if not self.available_cards:
            return
        
        if self.current_card_index < len(self.available_cards) - 1:
            self.current_card_index += 1
            self.load_current_card()
        else:
            QMessageBox.information(self, "Complete", "You've reached the last card!")
            print("🏁 Reached end of card list")
    
    def load_previous_card(self):
        """Load the previous card in auto-load mode"""
        if not self.available_cards:
            return
        
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.load_current_card()
        else:
            QMessageBox.information(self, "Beginning", "You're at the first card!")
            print("🏁 At beginning of card list")
    
    def save_and_next(self):
        """Save current coordinates and move to next card"""
        # Only save if there are coordinates to save
        coordinates = self.image_widget.get_coordinates_data()
        if coordinates:
            self.save_coordinates()
        else:
            print("⏭️ No coordinates to save, moving to next card")
        
        # Move to next card
        self.load_next_card()


def main():
    """Main entry point for the coordinate tool"""
    print("🎯 Starting Riftbound Card Name Coordinate Tool...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Riftbound Card Coordinate Tool")
    app.setApplicationVersion("1.0")
    
    # Create and show the main window
    window = CoordinateToolWindow()
    window.show()
    
    print("✅ Coordinate tool ready!")
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
