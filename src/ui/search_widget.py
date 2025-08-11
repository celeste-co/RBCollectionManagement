"""
Search widget for finding cards based on multiple criteria
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFrame, QGroupBox, QToolTip)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QEvent, QRect, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QMouseEvent
from typing import List, Optional
from pathlib import Path
import os
from src.models.card_database import CardDatabase, Card

class RangeSliderWidget(QWidget):
    """Custom range slider widget that looks like one slider with two handles"""
    
    valueChanged = pyqtSignal(tuple)
    
    def __init__(self, min_val: int, max_val: int, parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.low_value = min_val
        self.high_value = max_val
        self.is_snapped = False
        self.snap_threshold = 0
        
        # Handle dimensions and positioning
        self.handle_width = 16
        self.handle_height = 20
        self.groove_height = 8
        self.groove_margin = 10
        
        # Mouse interaction state
        self.dragging_handle = None  # 'low', 'high', or None
        self.drag_start_pos = None
        self.drag_start_value = None
        self.original_snapped_position = None  # Store original position when unsnapping
        
        # Visual styling
        self.setMinimumHeight(40)
        self.setMinimumWidth(200)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        
        # Groove (the track)
        groove_rect = QRect(
            self.groove_margin, 
            (height - self.groove_height) // 2,
            width - 2 * self.groove_margin, 
            self.groove_height
        )
        
        # Draw groove
        painter.setPen(QPen(QColor("#999999"), 1))
        painter.setBrush(QBrush(QColor("#f0f0f0")))
        painter.drawRoundedRect(groove_rect, 4, 4)
        
        # Calculate handle positions
        low_pos = self._value_to_position(self.low_value)
        high_pos = self._value_to_position(self.high_value)
        
        # Draw selection range (between handles)
        if not self.is_snapped:
            selection_rect = QRect(
                low_pos + self.handle_width // 2,
                (height - self.groove_height) // 2,
                high_pos - low_pos,
                self.groove_height
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#0078d4")))
            painter.drawRoundedRect(selection_rect, 2, 2)
        
        # Draw handles
        self._draw_handle(painter, low_pos, height, "low")
        self._draw_handle(painter, high_pos, height, "high")
        
    def _draw_handle(self, painter: QPainter, x_pos: int, height: int, handle_type: str):
        """Draw a single handle"""
        handle_rect = QRect(
            x_pos,
            (height - self.handle_height) // 2,
            self.handle_width,
            self.handle_height
        )
        
        # Choose color based on handle type and snapped state
        if self.is_snapped:
            color = QColor("#107c10")  # Green when snapped
            border_color = QColor("#0e6e0e")
        elif handle_type == "low":
            color = QColor("#0078d4")  # Blue for low handle
            border_color = QColor("#5c2d91")
        else:  # high handle
            color = QColor("#d83b01")  # Orange for high handle
            border_color = QColor("#a92d01")
        
        # Draw handle
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(handle_rect, 8, 8)
        
        # Draw handle indicator (small line in center)
        indicator_rect = QRect(
            x_pos + self.handle_width // 2 - 1,
            (height - self.handle_height) // 2 + 4,
            2,
            self.handle_height - 8
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("white")))
        painter.drawRect(indicator_rect)
    
    def _value_to_position(self, value: int) -> int:
        """Convert a value to x position"""
        available_width = self.width() - 2 * self.groove_margin - self.handle_width
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        return self.groove_margin + int(ratio * available_width)
    
    def _position_to_value(self, x_pos: int) -> int:
        """Convert x position to value"""
        available_width = self.width() - 2 * self.groove_margin - self.handle_width
        ratio = (x_pos - self.groove_margin) / available_width
        ratio = max(0, min(1, ratio))  # Clamp to [0, 1]
        return int(self.min_val + ratio * (self.max_val - self.min_val))
    
    def _get_handle_at_position(self, pos: QPoint) -> Optional[str]:
        """Determine which handle (if any) is at the given position"""
        x = pos.x()
        y = pos.y()
        
        # Check if click is within handle height
        height = self.height()
        if y < (height - self.handle_height) // 2 or y > (height + self.handle_height) // 2:
            return None
        
        # Check low handle
        low_pos = self._value_to_position(self.low_value)
        if low_pos <= x <= low_pos + self.handle_width:
            return "low"
        
        # Check high handle
        high_pos = self._value_to_position(self.high_value)
        if high_pos <= x <= high_pos + self.handle_width:
            return "high"
        
        return None
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self._get_handle_at_position(event.pos())
            if handle:
                self.dragging_handle = handle
                self.drag_start_pos = event.pos()
                self.drag_start_value = self.low_value if handle == "low" else self.high_value
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                # Click on groove - move both handles to that position
                new_value = self._position_to_value(event.pos().x())
                self._set_values(new_value, new_value)
                self.is_snapped = True
                self.update()
                self.valueChanged.emit((new_value, new_value))
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging_handle:
            # Handle dragging
            new_value = self._position_to_value(event.pos().x())
            new_value = max(self.min_val, min(self.max_val, new_value))
            
            # If we're currently snapped, determine which handle to control based on direction
            just_unsnapped = False
            if self.is_snapped:
                self.is_snapped = False
                just_unsnapped = True
                # Store the snapped position (only set once when first unsnapping)
                if self.original_snapped_position is None:
                    self.original_snapped_position = self.low_value  # Both are equal when snapped
                snapped_position = self.original_snapped_position
                
                # Determine which handle to control based on drag direction
                if self.dragging_handle == "low":
                    # If dragging low handle, determine direction
                    if new_value > snapped_position:
                        # Moving right - control the high handle, low stays at snapped position
                        self.dragging_handle = "high"
                        self.low_value = snapped_position
                        # Set high handle to follow the drag exactly
                        self.high_value = new_value
                    else:
                        # Moving left - control the low handle, high stays at snapped position
                        # Set low handle to follow the drag exactly
                        self.low_value = new_value
                        self.high_value = snapped_position
                else:  # dragging high handle
                    # If dragging high handle, determine direction
                    if new_value < snapped_position:
                        # Moving left - control the low handle, high stays at snapped position
                        self.dragging_handle = "low"
                        # Set low handle to follow the drag exactly
                        self.low_value = new_value
                        self.high_value = snapped_position
                    else:
                        # Moving right - control the high handle, low stays at snapped position
                        self.low_value = snapped_position
                        # Set high handle to follow the drag exactly
                        self.high_value = new_value
            
            # Only check for handle crossing if we didn't just unsnap
            if not just_unsnapped:
                # Check if we should switch handles BEFORE setting values (when crossing over the other handle)
                if self.dragging_handle == "low" and new_value > self.high_value:
                    # Low handle crossed over high handle - switch to controlling high handle
                    self.dragging_handle = "high"
                    self.low_value = self.high_value
                    self.high_value = new_value
                elif self.dragging_handle == "high" and new_value < self.low_value:
                    # High handle crossed over low handle - switch to controlling low handle
                    self.dragging_handle = "low"
                    self.high_value = self.low_value
                    self.low_value = new_value
                else:
                    # Normal dragging logic (no crossing) - only if we didn't just unsnap
                    if not just_unsnapped:
                        if self.dragging_handle == "low":
                            self.low_value = new_value
                        else:  # high handle
                            self.high_value = new_value
            
            # Check for snapping (only when not already snapped and handles are at exact same position)
            if not self.is_snapped and self.low_value == self.high_value:
                self.is_snapped = True
                # Snap to the value of the handle we're NOT dragging (the target)
                if self.dragging_handle == "low":
                    # Dragging low handle towards high - snap to high handle's value
                    snapped_value = self.high_value
                else:
                    # Dragging high handle towards low - snap to low handle's value  
                    snapped_value = self.low_value
                self._set_values(snapped_value, snapped_value)
            
            self.update()
            self.valueChanged.emit((self.low_value, self.high_value))
        else:
            # Check for hover effects
            handle = self._get_handle_at_position(event.pos())
            if handle:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_handle = None
            self.drag_start_pos = None
            self.drag_start_value = None
            self.original_snapped_position = None  # Reset when drag ends
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def _set_values(self, low: int, high: int):
        """Set both values, ensuring low <= high"""
        self.low_value = min(low, high)
        self.high_value = max(low, high)
    
    def setValue(self, value_tuple):
        low, high = value_tuple
        self._set_values(low, high)
        self.is_snapped = (low == high)
        self.update()
        self.valueChanged.emit((self.low_value, self.high_value))
    
    def getValue(self):
        return (self.low_value, self.high_value)
    
    def unsnap(self):
        """Force unsnap by moving handles apart"""
        if self.is_snapped:
            # Move high handle to max if we're at the low end, otherwise move low to min
            if self.low_value <= (self.min_val + self.max_val) // 2:
                self.high_value = self.max_val
            else:
                self.low_value = self.min_val
            self.is_snapped = False
            self.update()
            self.valueChanged.emit((self.low_value, self.high_value))

class SearchWorker(QThread):
    """Background worker for search operations"""
    results_ready = pyqtSignal(list)
    
    def __init__(self, database: CardDatabase, search_params: dict):
        super().__init__()
        self.database = database
        self.search_params = search_params
    
    def run(self):
        """Execute search in background thread"""
        results = self.database.search_cards(**self.search_params)
        self.results_ready.emit(results)

class SearchWidget(QWidget):
    """Advanced library (card browser) widget with filters"""
    
    card_selected = pyqtSignal(Card)
    
    def __init__(self, database: CardDatabase):
        super().__init__()
        self.database = database
        self.search_worker = None
        self._current_cards: List[Card] = []
        self.init_ui()
        
        # Populate dropdowns and load all cards by default
        self.populate_dropdowns()
        self.perform_search()  # show entire library by default
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Filters section
        criteria_group = QGroupBox("Filters")
        
        # Create two-column layout: left for filters, right for sliders
        criteria_layout = QHBoxLayout(criteria_group)
        
        # Left column: All filters
        left_column = QVBoxLayout()
        
        # Row 1: Name and Set
        name_set_layout = QHBoxLayout()
        name_set_layout.addWidget(QLabel("Card Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Search by name...")
        name_set_layout.addWidget(self.name_input)
        name_set_layout.addWidget(QLabel("Set:"))
        self.set_combo = QComboBox()
        self.set_combo.addItem("All Sets")
        name_set_layout.addWidget(self.set_combo)
        left_column.addLayout(name_set_layout)
        
        # Row 2: Domains (checkboxes)
        left_column.addWidget(QLabel("Domains:"))
        domains_box = QHBoxLayout()
        self.domain_checks = []
        for d in ["Fury", "Calm", "Mind", "Body", "Order", "Chaos"]:
            cb = QCheckBox(d)
            self.domain_checks.append(cb)
            domains_box.addWidget(cb)
        domains_box.addStretch()
        left_column.addLayout(domains_box)
        
        # Row 3: Rarity and Type
        rarity_type_layout = QHBoxLayout()
        rarity_type_layout.addWidget(QLabel("Rarity:"))
        self.rarity_combo = QComboBox()
        self.rarity_combo.addItem("All Rarities")
        rarity_type_layout.addWidget(self.rarity_combo)
        rarity_type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types")
        rarity_type_layout.addWidget(self.type_combo)
        left_column.addLayout(rarity_type_layout)
        
        # Row 4: Tags
        left_column.addWidget(QLabel("Tags:"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g., Noxus, Dragon")
        left_column.addWidget(self.tags_input)
        
        # Row 5: Options and Search Button
        options_layout = QHBoxLayout()
        self.owned_only_check = QCheckBox("Show only owned")
        options_layout.addWidget(self.owned_only_check)
        options_layout.addStretch()
        
        search_button = QPushButton("Apply Filters")
        search_button.clicked.connect(self.perform_search)
        search_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        options_layout.addWidget(search_button)
        left_column.addLayout(options_layout)
        
        # Right column: Only the three sliders
        right_column = QVBoxLayout()
        right_column.addWidget(QLabel("Range Filters"))
        
        # Might slider
        might_layout = QHBoxLayout()
        might_layout.addWidget(QLabel("Might:"))
        self.might_slider = RangeSliderWidget(0, 10)
        self.might_label = QLabel("0 - 10")
        self.might_label.setFixedWidth(60)
        def on_might_changed(v):
            lo, hi = v
            self.might_label.setText(f"{lo} - {hi}")
        self.might_slider.valueChanged.connect(on_might_changed)
        might_layout.addWidget(self.might_slider)
        might_layout.addWidget(self.might_label)
        right_column.addLayout(might_layout)

        # Energy slider
        energy_layout = QHBoxLayout()
        energy_layout.addWidget(QLabel("Energy:"))
        self.energy_slider = RangeSliderWidget(0, 12)
        self.energy_label = QLabel("0 - 12")
        self.energy_label.setFixedWidth(60)
        def on_energy_changed(v):
            lo, hi = v
            self.energy_label.setText(f"{lo} - {hi}")
        self.energy_slider.valueChanged.connect(on_energy_changed)
        energy_layout.addWidget(self.energy_slider)
        energy_layout.addWidget(self.energy_label)
        right_column.addLayout(energy_layout)

        # Power slider
        power_layout = QHBoxLayout()
        power_layout.addWidget(QLabel("Power:"))
        self.power_total_slider = RangeSliderWidget(0, 4)
        self.power_label = QLabel("0 - 4")
        self.power_label.setFixedWidth(60)
        def on_power_changed(v):
            lo, hi = v
            self.power_label.setText(f"{lo} - {hi}")
        self.power_total_slider.valueChanged.connect(on_power_changed)
        power_layout.addWidget(self.power_total_slider)
        power_layout.addWidget(self.power_label)
        right_column.addLayout(power_layout)
        
        # Add both columns to the main criteria layout with equal sizing
        criteria_layout.addLayout(left_column, 1)  # stretch factor 1
        criteria_layout.addLayout(right_column, 1)  # stretch factor 1
        
        layout.addWidget(criteria_group)
        
        # Results section
        results_group = QGroupBox("Library")
        results_layout = QVBoxLayout(results_group)
        
        # Results table (no inline images)
        self.results_table = QTableWidget()
        self.results_table.setMouseTracking(True)
        # Install event filter on viewport to get correct coordinates (exclude header)
        self.results_table.viewport().setMouseTracking(True)
        self.results_table.viewport().installEventFilter(self)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "ID", "Name", "Set", "Domain", "Rarity", "Type", "Energy", "Power"
        ])
        
        # Set table properties
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Set
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Domain
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Rarity
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Energy
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Power
        
        # Connect table selection
        self.results_table.itemSelectionChanged.connect(self.on_card_selected)
        
        results_layout.addWidget(self.results_table)
        
        # Status label
        self.status_label = QLabel("Showing all cards")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        results_layout.addWidget(self.status_label)
        
        layout.addWidget(results_group)

    def eventFilter(self, obj, event):
        # Listen on the viewport for precise row/column mapping
        if obj is self.results_table.viewport():
            if event.type() == QEvent.Type.MouseMove:
                index = self.results_table.indexAt(event.pos())
                if index.isValid() and index.column() == 1:
                    row = index.row()
                    item = self.results_table.item(row, 1)  # name column stores the card
                    if item is not None:
                        card = item.data(Qt.ItemDataRole.UserRole)
                        if card:
                            uri = self._card_image_uri(card)
                            if uri:
                                QToolTip.showText(self.results_table.viewport().mapToGlobal(event.pos()), f"<img src='{uri}' width='240'>", self.results_table.viewport())
                                return True
                # Not on name column or invalid index → hide tooltip
                QToolTip.hideText()
            elif event.type() in (QEvent.Type.Leave,):
                QToolTip.hideText()
        return super().eventFilter(obj, event)

    def _card_image_uri(self, card: Card) -> Optional[str]:
        try:
            base = Path(__file__).resolve().parents[2] / "card_img"
            raw_id = (card.id or "").strip()
            if not raw_id:
                return None
            # Folder by set prefix (e.g., OGN, OGS)
            prefix = raw_id.split('-')[0]
            # Map star-suffixed IDs to 's' images (e.g., OGN-300* -> OGN-300s.webp)
            file_id = raw_id.replace('*', 's')
            candidate = base / prefix / f"{file_id}.webp"
            if not candidate.exists():
                fallback = base / "Cardback.webp"
                return fallback.as_uri() if fallback.exists() else None
            return candidate.as_uri()
        except Exception:
            return None

    def populate_dropdowns(self):
        """Populate dropdown menus with available values"""
        try:
            # Get all cards to extract unique values
            all_cards = self.database.search_cards()
            print(f"Found {len(all_cards)} total cards for dropdown population")
            
            # Extract unique sets
            sets = sorted(list(set(card.set_name for card in all_cards)))
            print(f"Unique sets: {sets}")
            for set_name in sets:
                self.set_combo.addItem(set_name)
            
            # Domains now fixed via checkboxes; no dropdown to populate
            
            # Extract unique rarities
            rarities = sorted(list(set(card.rarity for card in all_cards)))
            print(f"Unique rarities: {rarities}")
            for rarity in rarities:
                self.rarity_combo.addItem(rarity)
            
            # Extract unique card types
            types = sorted(list(set(card.card_type for card in all_cards)))
            print(f"Unique card types: {types}")
            for card_type in types:
                self.type_combo.addItem(card_type)
                
        except Exception as e:
            print(f"Error in populate_dropdowns: {e}")
            self.status_label.setText(f"Error loading card data: {str(e)}")
    
    def perform_search(self):
        """Execute search with current criteria"""
        # Build search parameters
        search_params = {}
        
        name_text = self.name_input.text().strip()
        if name_text:
            search_params['name'] = name_text
        
        set_text = self.set_combo.currentText()
        if set_text and set_text != "All Sets":
            search_params['set_name'] = set_text
        
        # Gather selected domains
        selected_domains = [cb.text() for cb in self.domain_checks if cb.isChecked()]
        if selected_domains:
            search_params['domain'] = selected_domains
        
        rarity_text = self.rarity_combo.currentText()
        if rarity_text and rarity_text != "All Rarities":
            search_params['rarity'] = rarity_text
        
        type_text = self.type_combo.currentText()
        if type_text and type_text != "All Types":
            search_params['card_type'] = type_text
        
        emin, emax = self.energy_slider.getValue()
        if emin > 0:
            search_params['min_cost'] = emin
        if emax < 20:
            search_params['max_cost'] = emax
        
        mmin, mmax = self.might_slider.getValue()
        if mmin > 0:
            search_params['min_power'] = mmin
        if mmax < 20:
            search_params['max_power'] = mmax

        pmin, pmax = self.power_total_slider.getValue()
        if pmin > 0:
            search_params['min_power_cost_total'] = pmin
        if pmax < 10:
            search_params['max_power_cost_total'] = pmax
        
        tags_text = self.tags_input.text().strip()
        if tags_text:
            search_params['tags'] = tags_text
        
        if self.owned_only_check.isChecked():
            search_params['owned_only'] = True
        
        # Update status
        self.status_label.setText("Loading library...")
        
        # Execute search in background
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()
        
        self.search_worker = SearchWorker(self.database, search_params)
        self.search_worker.results_ready.connect(self.display_results)
        self.search_worker.start()
    
    def display_results(self, cards: List[Card]):
        """Display search results in the table"""
        self._current_cards = cards
        self.results_table.setRowCount(len(cards))
        
        for row, card in enumerate(cards):
            # Card data (no inline image)
            id_item = QTableWidgetItem(card.id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(card.name)
            name_item.setData(Qt.ItemDataRole.UserRole, card)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 1, name_item)

            self.results_table.setItem(row, 2, QTableWidgetItem(card.set_name))
            self.results_table.setItem(row, 3, QTableWidgetItem(card.domains))
            self.results_table.setItem(row, 4, QTableWidgetItem(card.rarity))
            self.results_table.setItem(row, 5, QTableWidgetItem(card.card_type))
            energy_text = str(card.energy_cost) if card.energy_cost is not None else "-"
            self.results_table.setItem(row, 6, QTableWidgetItem(energy_text))
            self.results_table.setItem(row, 7, QTableWidgetItem(card.power_shorthand or "-"))
        
        # Update status
        if cards:
            self.status_label.setText(f"Showing {len(cards)} cards")
        else:
            self.status_label.setText("No cards found")
    
    def on_card_selected(self):
        """Handle card selection from table"""
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            item = self.results_table.item(current_row, 1)  # name column shifted by 1 due to ID
            if item:
                card = item.data(Qt.ItemDataRole.UserRole)
                if card:
                    self.card_selected.emit(card)
