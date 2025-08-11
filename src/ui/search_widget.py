"""
Search widget for finding cards based on multiple criteria
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFrame, QGroupBox, QToolTip)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QEvent
from PyQt6.QtGui import QFont
from typing import List, Optional
from pathlib import Path
import os
from src.models.card_database import CardDatabase, Card

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
        criteria_layout = QGridLayout(criteria_group)
        
        # Row 1: Name and Set
        criteria_layout.addWidget(QLabel("Card Name:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Search by name...")
        criteria_layout.addWidget(self.name_input, 0, 1)
        
        criteria_layout.addWidget(QLabel("Set:"), 0, 2)
        self.set_combo = QComboBox()
        self.set_combo.addItem("All Sets")
        criteria_layout.addWidget(self.set_combo, 0, 3)
        
        # Row 2: Domains (checkboxes) and Rarity
        criteria_layout.addWidget(QLabel("Domains:"), 1, 0)
        domains_box = QHBoxLayout()
        self.domain_checks = []
        for d in ["Fury", "Calm", "Mind", "Body", "Order", "Chaos"]:
            cb = QCheckBox(d)
            self.domain_checks.append(cb)
            domains_box.addWidget(cb)
        domains_box.addStretch()
        criteria_layout.addLayout(domains_box, 1, 1)
        
        criteria_layout.addWidget(QLabel("Rarity:"), 1, 2)
        self.rarity_combo = QComboBox()
        self.rarity_combo.addItem("All Rarities")
        criteria_layout.addWidget(self.rarity_combo, 1, 3)
        
        # Row 3: Card Type and Cost Range
        criteria_layout.addWidget(QLabel("Type:"), 2, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types")
        criteria_layout.addWidget(self.type_combo, 2, 1)
        
        criteria_layout.addWidget(QLabel("Energy Cost:"), 2, 2)
        cost_layout = QHBoxLayout()
        self.min_cost_spin = QSpinBox()
        self.min_cost_spin.setRange(0, 20)
        self.min_cost_spin.setSpecialValueText("Min")
        cost_layout.addWidget(self.min_cost_spin)
        cost_layout.addWidget(QLabel("-"))
        self.max_cost_spin = QSpinBox()
        self.max_cost_spin.setRange(0, 20)
        self.max_cost_spin.setSpecialValueText("Max")
        cost_layout.addWidget(self.max_cost_spin)
        criteria_layout.addLayout(cost_layout, 2, 3)
        
        # Row 4: Power Range and Tags
        criteria_layout.addWidget(QLabel("Might:"), 3, 0)
        power_layout = QHBoxLayout()
        self.min_power_spin = QSpinBox()
        self.min_power_spin.setRange(0, 20)
        self.min_power_spin.setSpecialValueText("Min")
        power_layout.addWidget(self.min_power_spin)
        power_layout.addWidget(QLabel("-"))
        self.max_power_spin = QSpinBox()
        self.max_power_spin.setRange(0, 20)
        self.max_power_spin.setSpecialValueText("Max")
        power_layout.addWidget(self.max_power_spin)
        criteria_layout.addLayout(power_layout, 3, 1)
        
        criteria_layout.addWidget(QLabel("Tags:"), 3, 2)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g., Noxus, Dragon")
        criteria_layout.addWidget(self.tags_input, 3, 3)
        
        # Row 5: Options and Search Button
        self.owned_only_check = QCheckBox("Show only owned")
        criteria_layout.addWidget(self.owned_only_check, 4, 0, 1, 2)
        
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
        criteria_layout.addWidget(search_button, 4, 2, 1, 2)
        
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
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "ID", "Name", "Set", "Domain", "Rarity", "Type", "Energy"
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
        
        if self.min_cost_spin.value() > 0:
            search_params['min_cost'] = self.min_cost_spin.value()
        
        if self.max_cost_spin.value() > 0:
            search_params['max_cost'] = self.max_cost_spin.value()
        
        if self.min_power_spin.value() > 0:
            search_params['min_power'] = self.min_power_spin.value()
        
        if self.max_power_spin.value() > 0:
            search_params['max_power'] = self.max_power_spin.value()
        
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
