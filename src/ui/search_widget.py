"""
Search widget for finding cards based on multiple criteria
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFrame, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap
from typing import List, Optional
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
    """Advanced search widget with multiple criteria"""
    
    card_selected = pyqtSignal(Card)
    
    def __init__(self, database: CardDatabase):
        super().__init__()
        self.database = database
        self.search_worker = None
        self.init_ui()
        
        # Get available values for dropdowns
        self.populate_dropdowns()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Search criteria section
        criteria_group = QGroupBox("Search Criteria")
        criteria_layout = QGridLayout(criteria_group)
        
        # Row 1: Name and Set
        criteria_layout.addWidget(QLabel("Card Name:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter card name...")
        criteria_layout.addWidget(self.name_input, 0, 1)
        
        criteria_layout.addWidget(QLabel("Set:"), 0, 2)
        self.set_combo = QComboBox()
        self.set_combo.addItem("All Sets")
        criteria_layout.addWidget(self.set_combo, 0, 3)
        
        # Row 2: Domain and Rarity
        criteria_layout.addWidget(QLabel("Domain:"), 1, 0)
        self.domain_combo = QComboBox()
        self.domain_combo.addItem("All Domains")
        criteria_layout.addWidget(self.domain_combo, 1, 1)
        
        criteria_layout.addWidget(QLabel("Rarity:"), 1, 2)
        self.rarity_combo = QComboBox()
        self.rarity_combo.addItem("All Rarities")
        criteria_layout.addWidget(self.rarity_combo, 1, 3)
        
        # Row 3: Card Type and Cost Range
        criteria_layout.addWidget(QLabel("Card Type:"), 2, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types")
        criteria_layout.addWidget(self.type_combo, 2, 1)
        
        criteria_layout.addWidget(QLabel("Cost Range:"), 2, 2)
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
        criteria_layout.addWidget(QLabel("Power Range:"), 3, 0)
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
        self.tags_input.setPlaceholderText("Enter tags...")
        criteria_layout.addWidget(self.tags_input, 3, 3)
        
        # Row 5: Options and Search Button
        self.owned_only_check = QCheckBox("Show only owned cards")
        criteria_layout.addWidget(self.owned_only_check, 4, 0, 1, 2)
        
        search_button = QPushButton("Search")
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
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout(results_group)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Image", "Name", "Set", "Domain", "Rarity", "Type", "Cost"
        ])
        
        # Set table properties
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Image
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Set
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Domain
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Rarity
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Cost
        
        self.results_table.setColumnWidth(0, 60)  # Image column width
        
        # Connect table selection
        self.results_table.itemSelectionChanged.connect(self.on_card_selected)
        
        results_layout.addWidget(self.results_table)
        
        # Status label
        self.status_label = QLabel("Ready to search")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        results_layout.addWidget(self.status_label)
        
        layout.addWidget(results_group)
    
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
            
            # Extract unique domains
            domains = sorted(list(set(card.domains for card in all_cards)))
            print(f"Unique domains: {domains}")
            for domain in domains:
                self.domain_combo.addItem(domain)
            
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
        
        if self.name_input.text().strip():
            search_params['name'] = self.name_input.text().strip()
        
        if self.set_combo.currentText() != "All Sets":
            search_params['set_name'] = self.set_combo.currentText()
        
        if self.domain_combo.currentText() != "All Domains":
            search_params['domain'] = self.domain_combo.currentText()
        
        if self.rarity_combo.currentText() != "All Rarities":
            search_params['rarity'] = self.rarity_combo.currentText()
        
        if self.type_combo.currentText() != "All Types":
            search_params['card_type'] = self.type_combo.currentText()
        
        if self.min_cost_spin.value() > 0:
            search_params['min_cost'] = self.min_cost_spin.value()
        
        if self.max_cost_spin.value() > 0:
            search_params['max_cost'] = self.max_cost_spin.value()
        
        if self.min_power_spin.value() > 0:
            search_params['min_power'] = self.min_power_spin.value()
        
        if self.max_power_spin.value() > 0:
            search_params['max_power'] = self.max_power_spin.value()
        
        if self.tags_input.text().strip():
            search_params['tags'] = self.tags_input.text().strip()
        
        if self.owned_only_check.isChecked():
            search_params['owned_only'] = True
        
        # Update status
        self.status_label.setText("Searching...")
        
        # Execute search in background
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()
        
        self.search_worker = SearchWorker(self.database, search_params)
        self.search_worker.results_ready.connect(self.display_results)
        self.search_worker.start()
    
    def display_results(self, cards: List[Card]):
        """Display search results in the table"""
        self.results_table.setRowCount(len(cards))
        
        for row, card in enumerate(cards):
            # Image (placeholder for now)
            image_label = QLabel()
            image_label.setFixedSize(50, 70)
            image_label.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setText("IMG")
            self.results_table.setCellWidget(row, 0, image_label)
            
            # Card data
            self.results_table.setItem(row, 1, QTableWidgetItem(card.name))
            self.results_table.setItem(row, 2, QTableWidgetItem(card.set_name))
            self.results_table.setItem(row, 3, QTableWidgetItem(card.domains))
            self.results_table.setItem(row, 4, QTableWidgetItem(card.rarity))
            self.results_table.setItem(row, 5, QTableWidgetItem(card.card_type))
            
            cost_text = str(card.energy_cost) if card.energy_cost is not None else "-"
            self.results_table.setItem(row, 6, QTableWidgetItem(cost_text))
            
            # Store card data in the name column for selection (since image column has a widget)
            self.results_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, card)
        
        # Update status
        if cards:
            self.status_label.setText(f"Found {len(cards)} cards")
        else:
            self.status_label.setText("No cards found")
    
    def on_card_selected(self):
        """Handle card selection from table"""
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            item = self.results_table.item(current_row, 1)  # Look in name column
            if item:
                card = item.data(Qt.ItemDataRole.UserRole)
                if card:
                    self.card_selected.emit(card)
