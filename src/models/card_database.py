"""
Card database model using SQLite for efficient searching and collection management
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class Card:
    """Card data structure"""
    id: str
    name: str
    set_name: str
    domains: str  # Comma-separated domains
    super_type: str
    card_type: str
    tags: str  # Comma-separated tags
    energy_cost: Optional[int]
    power_cost: Optional[int]
    might: Optional[int]
    rarity: str
    is_alt_art: bool
    is_overnumbered: bool
    is_signed: bool
    power_shorthand: Optional[str] = None
    
    # Collection-specific fields
    quantity: int = 0
    condition: str = "NM"  # NM, LP, MP, HP, DMG
    acquisition_date: Optional[str] = None
    personal_notes: Optional[str] = None

class CardDatabase:
    """SQLite database for card management and search"""
    
    def __init__(self, db_path: str = "collection.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create cards table (only if it doesn't exist)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    set_name TEXT NOT NULL,
                    domains TEXT NOT NULL,
                    super_type TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    energy_cost INTEGER,
                    power_cost INTEGER,
                    power_cost_f INTEGER DEFAULT 0,
                    power_cost_c INTEGER DEFAULT 0,
                    power_cost_m INTEGER DEFAULT 0,
                    power_cost_b INTEGER DEFAULT 0,
                    power_cost_o INTEGER DEFAULT 0,
                    power_cost_h INTEGER DEFAULT 0,
                    power_cost_any INTEGER DEFAULT 0,
                    might INTEGER,
                    rarity TEXT NOT NULL,
                    is_alt_art INTEGER DEFAULT 0,
                    is_overnumbered INTEGER DEFAULT 0,
                    is_signed INTEGER DEFAULT 0,
                    quantity INTEGER DEFAULT 0,
                    condition TEXT DEFAULT 'NM',
                    acquisition_date TEXT,
                    personal_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for fast searching
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON cards(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_set ON cards(set_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_domains ON cards(domains)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_super_type ON cards(super_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rarity ON cards(rarity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_power_cost ON cards(power_cost)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON cards(card_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags ON cards(tags)")
            
            conn.commit()
    
    def import_from_json(self, json_file_path: str, set_name: str):
        """Import cards from JSON file into database"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            cards_data = json.load(f)
        
        print(f"Importing {len(cards_data)} cards from {set_name}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            imported_count = 0
            for card_data in cards_data:
                # Convert arrays to comma-separated strings
                domains_str = ', '.join(card_data.get('domains', []))
                tags_str = ', '.join(card_data.get('tags', []))
                
                # Extract card attributes
                card = Card(
                    id=card_data.get('card_number', ''),  # Use card_number as ID
                    name=card_data.get('name', ''),
                    set_name=set_name,
                    domains=domains_str,
                    super_type=card_data.get('super_type', ''),
                    card_type=card_data.get('type', ''),  # Use 'type' from JSON
                    tags=tags_str,
                    energy_cost=card_data.get('energy_cost'),
                    power_cost=card_data.get('power_cost'),
                    might=card_data.get('might'),
                    rarity=card_data.get('rarity', ''),
                    is_alt_art=card_data.get('is_alt_art', False),
                    is_overnumbered=card_data.get('is_overnumbered', False),
                    is_signed=card_data.get('is_signed', False)
                )

                pcm = card_data.get('power_cost_map') or {}
                pc_f = int(pcm.get('F', 0))
                pc_c = int(pcm.get('C', 0))
                pc_m = int(pcm.get('M', 0))
                pc_b = int(pcm.get('B', 0))
                pc_o = int(pcm.get('O', 0))
                pc_h = int(pcm.get('H', 0))
                pc_any = int(pcm.get('Any', 0))
                
                # Insert or update card
                cursor.execute("""
                    INSERT OR REPLACE INTO cards (
                        id, name, set_name, domains, super_type, card_type, tags,
                        energy_cost, power_cost,
                        power_cost_f, power_cost_c, power_cost_m, power_cost_b, power_cost_o, power_cost_h, power_cost_any,
                        might, rarity, is_alt_art,
                        is_overnumbered, is_signed, quantity, condition, acquisition_date,
                        personal_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    card.id, card.name, card.set_name, card.domains, card.super_type,
                    card.card_type, card.tags, card.energy_cost, card.power_cost,
                    pc_f, pc_c, pc_m, pc_b, pc_o, pc_h, pc_any,
                    card.might, card.rarity, card.is_alt_art, card.is_overnumbered,
                    card.is_signed, card.quantity, card.condition, card.acquisition_date,
                    card.personal_notes
                ))
                imported_count += 1
            
            print(f"Successfully imported {imported_count} cards from {set_name}")
            conn.commit()
    
    def search_cards(self, 
                    name: Optional[str] = None,
                    set_name: Optional[str] = None,
                    domain: Optional[object] = None,
                    rarity: Optional[str] = None,
                    super_type: Optional[str] = None,
                    card_type: Optional[str] = None,
                    min_cost: Optional[int] = None,
                    max_cost: Optional[int] = None,
                    min_power_cost_total: Optional[int] = None,
                    max_power_cost_total: Optional[int] = None,
                    min_power_cost_f: Optional[int] = None,
                    min_power_cost_c: Optional[int] = None,
                    min_power_cost_m: Optional[int] = None,
                    min_power_cost_b: Optional[int] = None,
                    min_power_cost_o: Optional[int] = None,
                    min_power_cost_h: Optional[int] = None,
                    min_power_cost_any: Optional[int] = None,
                    min_power: Optional[int] = None,
                    max_power: Optional[int] = None,
                    tags: Optional[str] = None,
                    owned_only: bool = False) -> List[Card]:
        """Search for cards based on multiple criteria"""
        
        query = "SELECT * FROM cards WHERE 1=1"
        params = []
        
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        
        if set_name:
            query += " AND set_name = ?"
            params.append(set_name)
        
        if domain:
            # Accept a single string or a list of domains
            if isinstance(domain, list) and len(domain) > 0:
                # Require at least one selected domain AND no unselected domains
                all_domains = ["Fury", "Calm", "Mind", "Body", "Order", "Chaos"]
                selected = [d for d in domain if d in all_domains]
                unselected = [d for d in all_domains if d not in selected]
                if selected:
                    like_any = []
                    for d in selected:
                        like_any.append("domains LIKE ?")
                        params.append(f"%{d}%")
                    query += " AND (" + " OR ".join(like_any) + ")"
                # Exclude any domain not selected
                for d in unselected:
                    query += " AND domains NOT LIKE ?"
                    params.append(f"%{d}%")
            elif isinstance(domain, str):
                query += " AND domains LIKE ?"
                params.append(f"%{domain}%")
        
        if rarity:
            query += " AND rarity = ?"
            params.append(rarity)
        
        if super_type:
            query += " AND super_type = ?"
            params.append(super_type)
        
        if card_type:
            query += " AND card_type = ?"
            params.append(card_type)
        
        if min_cost is not None:
            query += " AND energy_cost >= ?"
            params.append(min_cost)
        
        if max_cost is not None:
            query += " AND energy_cost <= ?"
            params.append(max_cost)

        if min_power_cost_total is not None:
            query += " AND power_cost >= ?"
            params.append(min_power_cost_total)

        if max_power_cost_total is not None:
            query += " AND power_cost <= ?"
            params.append(max_power_cost_total)

        # Power cost per-domain filters
        power_filters = [
            ("power_cost_f", min_power_cost_f),
            ("power_cost_c", min_power_cost_c),
            ("power_cost_m", min_power_cost_m),
            ("power_cost_b", min_power_cost_b),
            ("power_cost_o", min_power_cost_o),
            ("power_cost_h", min_power_cost_h),
            ("power_cost_any", min_power_cost_any),
        ]
        for col, val in power_filters:
            if val is not None and val > 0:
                query += f" AND {col} >= ?"
                params.append(val)
        
        if min_power is not None:
            query += " AND might >= ?"
            params.append(min_power)
        
        if max_power is not None:
            query += " AND might <= ?"
            params.append(max_power)
        
        if tags:
            query += " AND tags LIKE ?"
            params.append(f"%{tags}%")
        
        if owned_only:
            query += " AND quantity > 0"
        
        print(f"Search query: {query}")
        print(f"Search params: {params}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            cards = []
            for row in cursor.fetchall():
                # Build power shorthand from per-domain columns
                def build_power_short(f,c,m,b,o,h,a):
                    parts = []
                    if f: parts.append(f"{f}F")
                    if c: parts.append(f"{c}C")
                    if m: parts.append(f"{m}M")
                    if b: parts.append(f"{b}B")
                    if o: parts.append(f"{o}O")
                    if h: parts.append(f"{h}H")
                    if a: parts.append(f"{a}A")
                    return "+".join(parts) if parts else None

                pc_f, pc_c, pc_m, pc_b, pc_o, pc_h, pc_any = row[9], row[10], row[11], row[12], row[13], row[14], row[15]
                card = Card(
                    id=row[0], name=row[1], set_name=row[2], domains=row[3],
                    super_type=row[4], card_type=row[5], tags=row[6],
                    energy_cost=row[7], power_cost=row[8], might=row[16],
                    rarity=row[17], is_alt_art=bool(row[18]), is_overnumbered=bool(row[19]),
                    is_signed=bool(row[20]), quantity=row[21], condition=row[22],
                    acquisition_date=row[23], personal_notes=row[24],
                    power_shorthand=build_power_short(pc_f, pc_c, pc_m, pc_b, pc_o, pc_h, pc_any)
                )
                cards.append(card)
            
            print(f"Search returned {len(cards)} cards")
            return cards
    
    def get_card_by_id(self, card_id: str) -> Optional[Card]:
        """Get a specific card by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
            row = cursor.fetchone()
            
            if row:
                pc_f, pc_c, pc_m, pc_b, pc_o, pc_h, pc_any = row[9], row[10], row[11], row[12], row[13], row[14], row[15]
                def build_power_short(f,c,m,b,o,h,a):
                    parts = []
                    if f: parts.append(f"{f}F")
                    if c: parts.append(f"{c}C")
                    if m: parts.append(f"{m}M")
                    if b: parts.append(f"{b}B")
                    if o: parts.append(f"{o}O")
                    if h: parts.append(f"{h}H")
                    if a: parts.append(f"{a}A")
                    return "+".join(parts) if parts else None
                return Card(
                    id=row[0], name=row[1], set_name=row[2], domains=row[3],
                    super_type=row[4], card_type=row[5], tags=row[6],
                    energy_cost=row[7], power_cost=row[8], might=row[16],
                    rarity=row[17], is_alt_art=bool(row[18]), is_overnumbered=bool(row[19]),
                    is_signed=bool(row[20]), quantity=row[21], condition=row[22],
                    acquisition_date=row[23], personal_notes=row[24],
                    power_shorthand=build_power_short(pc_f, pc_c, pc_m, pc_b, pc_o, pc_h, pc_any)
                )
            return None
    
    def update_collection_data(self, card_id: str, **kwargs):
        """Update collection-specific data for a card"""
        allowed_fields = ['quantity', 'condition', 'acquisition_date', 'personal_notes']
        
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return
        
        params.append(card_id)
        query = f"UPDATE cards SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total cards owned
            cursor.execute("SELECT COUNT(*) FROM cards WHERE quantity > 0")
            total_owned = cursor.fetchone()[0]
            
            # Total unique cards
            cursor.execute("SELECT COUNT(DISTINCT id) FROM cards WHERE quantity > 0")
            unique_cards = cursor.fetchone()[0]
            
            # Total quantity
            cursor.execute("SELECT SUM(quantity) FROM cards WHERE quantity > 0")
            total_quantity = cursor.fetchone()[0] or 0
            
            # Cards by set
            cursor.execute("""
                SELECT set_name, COUNT(*) as count 
                FROM cards 
                WHERE quantity > 0 
                GROUP BY set_name
            """)
            by_set = dict(cursor.fetchall())
            
            # Cards by domain
            cursor.execute("""
                SELECT domains, COUNT(*) as count 
                FROM cards 
                WHERE quantity > 0 
                GROUP BY domains
            """)
            by_domain = dict(cursor.fetchall())
            
            return {
                'total_owned': total_owned,
                'unique_cards': unique_cards,
                'total_quantity': total_quantity,
                'by_set': by_set,
                'by_domain': by_domain
            }
