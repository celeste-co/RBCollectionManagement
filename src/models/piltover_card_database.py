"""
Piltover Archive Card Database Model

This model is designed to work with the reorganized Piltover Archive data structure,
where each variant is a separate entry with all card information included.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class PiltoverCard:
    """Piltover Archive card data structure"""
    # Core card information
    id: str
    name: str
    type: str
    super: Optional[str]
    description: str
    energy: int
    might: int
    power: int
    tags: List[str]
    
    # Variant-specific information
    variant_id: str
    variant_number: str
    image_url: str
    rarity: str
    flavor_text: Optional[str]
    artist: str
    release_date: Optional[str]
    variant_type: str
    
    # Set information
    set_id: str
    set_name: str
    set_prefix: str
    
    # Color information
    colors: List[Dict[str, str]]
    
    # Collection-specific fields
    quantity: int = 0
    condition: str = "NM"  # NM, LP, MP, HP, DMG
    acquisition_date: Optional[str] = None
    personal_notes: Optional[str] = None


class PiltoverCardDatabase:
    """SQLite database for Piltover Archive card management and search"""
    
    def __init__(self, db_path: str = "collection.db"):
        self.db_path = db_path
        self.init_database()
    
    def _connect(self) -> sqlite3.Connection:
        """Create a SQLite connection with sane defaults for concurrency."""
        # Increase timeout to wait for writers, reduce lock contention at startup
        conn = sqlite3.connect(self.db_path, timeout=10)
        # Busy timeout as an extra safeguard (milliseconds)
        try:
            conn.execute("PRAGMA busy_timeout=10000")
        except Exception:
            pass
        return conn
    
    def _connect_ro(self) -> sqlite3.Connection:
        """Create a read-only SQLite connection for queries to reduce contention."""
        uri = f"file:{self.db_path}?mode=ro&cache=shared"
        conn = sqlite3.connect(uri, uri=True, timeout=2)
        try:
            conn.execute("PRAGMA busy_timeout=2000")
        except Exception:
            pass
        return conn
    
    def init_database(self):
        """Initialize the database with required tables"""
        with self._connect() as conn:
            cursor = conn.cursor()
            # Enable WAL so reads are not blocked by writes
            try:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass
            
            # Create metadata table for storing small key/value settings (e.g., last import hash)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

            # Create cards table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    super TEXT,
                    description TEXT NOT NULL,
                    energy INTEGER NOT NULL,
                    might INTEGER NOT NULL,
                    power INTEGER NOT NULL,
                    tags TEXT NOT NULL,
                    variant_id TEXT PRIMARY KEY,
                    variant_number TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    rarity TEXT NOT NULL,
                    flavor_text TEXT,
                    artist TEXT NOT NULL,
                    release_date TEXT,
                    variant_type TEXT NOT NULL,
                    set_id TEXT NOT NULL,
                    set_name TEXT NOT NULL,
                    set_prefix TEXT NOT NULL,
                    colors TEXT NOT NULL,
                    quantity INTEGER DEFAULT 0,
                    condition TEXT DEFAULT 'NM',
                    acquisition_date TEXT,
                    personal_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Ensure new columns for efficient variant ordering exist
            cursor.execute("PRAGMA table_info(cards)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            if 'variant_order_num' not in existing_cols:
                try:
                    cursor.execute("ALTER TABLE cards ADD COLUMN variant_order_num INTEGER DEFAULT 0")
                except Exception:
                    pass
            if 'variant_order_suffix' not in existing_cols:
                try:
                    cursor.execute("ALTER TABLE cards ADD COLUMN variant_order_suffix TEXT DEFAULT ''")
                except Exception:
                    pass
            
            # Create indexes for fast searching
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON cards(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_set_prefix ON cards(set_prefix)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON cards(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_super ON cards(super)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rarity ON cards(rarity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_artist ON cards(artist)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_variant_number ON cards(variant_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_energy ON cards(energy)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_might ON cards(might)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_power ON cards(power)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_variant_order ON cards(set_prefix, variant_order_num, variant_order_suffix)")
            
            conn.commit()
    
    def clear_database(self):
        """Clear all data from the cards table"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cards")
            conn.commit()
            print(f"🗑️  Cleared all data from database: {self.db_path}")
    
    def import_from_sorted_json(self, json_file_path: str):
        """Import cards from the sorted Piltover Archive JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            variants = data.get('variants', [])
            print(f"Importing {len(variants)} variants from Piltover Archive")
            
            with self._connect() as conn:
                cursor = conn.cursor()
                
                rows = []
                def parse_variant_order(vn: str) -> tuple:
                    try:
                        num_part = vn.split('-')[1]
                    except Exception:
                        return (0, '')
                    digits = ''.join(ch for ch in num_part if ch.isdigit())
                    suffix = ''.join(ch for ch in num_part if not ch.isdigit())
                    return (int(digits) if digits else 0, suffix)

                for variant in variants:
                    # Validate required fields
                    if not variant.get('variantId') or not variant.get('variantNumber'):
                        print(f"⚠️  Skipping variant with missing required fields: {variant.get('name', 'Unknown')}")
                        continue
                    
                    # Convert arrays to JSON strings for storage
                    tags_json = json.dumps(variant.get('tags', []))
                    colors_json = json.dumps(variant.get('cardColors', []))
                    
                    # Handle potentially null fields
                    release_date = variant.get('releaseDate') or variant.get('set', {}).get('releaseDate')
                    artist = variant.get('artist') or 'Unknown Artist'
                    order_num, order_suffix = parse_variant_order(variant['variantNumber'])
                    
                    rows.append((
                        variant['id'],
                        variant['name'],
                        variant['type'],
                        variant['super'],
                        variant['description'],
                        variant['energy'],
                        variant['might'],
                        variant['power'],
                        tags_json,
                        variant['variantId'],
                        variant['variantNumber'],
                        variant['imageUrl'],
                        variant['rarity'],
                        variant['flavorText'],
                        artist,
                        release_date,
                        variant['variantType'],
                        variant['set']['id'],
                        variant['set']['name'],
                        variant['set']['prefix'],
                        colors_json,
                        0,
                        'NM',
                        None,
                        None,
                        order_num,
                        order_suffix
                    ))

                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO cards (
                        id, name, type, super, description, energy, might, power, tags,
                        variant_id, variant_number, image_url, rarity, flavor_text, artist,
                        release_date, variant_type, set_id, set_name, set_prefix, colors,
                        quantity, condition, acquisition_date, personal_notes,
                        variant_order_num, variant_order_suffix
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?
                    )
                    """,
                    rows
                )
                print(f"Successfully imported {len(rows)} variants")
                conn.commit()
                
        except Exception as e:
            print(f"❌ Error importing data: {e}")
            return False
        
        return True
    
    def search_cards(self, 
                    name: Optional[str] = None,
                    set_prefix: Optional[str] = None,
                    card_type: Optional[str] = None,
                    super_type: Optional[str] = None,
                    rarity: Optional[str] = None,
                    artist: Optional[str] = None,
                    min_energy: Optional[int] = None,
                    max_energy: Optional[int] = None,
                    min_might: Optional[int] = None,
                    max_might: Optional[int] = None,
                    min_power: Optional[int] = None,
                    max_power: Optional[int] = None,
                    tags: Optional[List[str]] = None,
                    colors: Optional[List[str]] = None,
                    variant_type: Optional[str] = None,
                    owned_only: bool = False) -> List[PiltoverCard]:
        """Search for cards based on multiple criteria"""
        
        query = "SELECT * FROM cards WHERE 1=1"
        params = []
        
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        
        if set_prefix:
            query += " AND set_prefix = ?"
            params.append(set_prefix)
        
        if card_type:
            query += " AND type = ?"
            params.append(card_type)
        
        if super_type:
            query += " AND super = ?"
            params.append(super_type)
        
        if rarity:
            query += " AND rarity = ?"
            params.append(rarity)
        
        if artist:
            query += " AND artist LIKE ?"
            params.append(f"%{artist}%")
        
        if min_energy is not None:
            query += " AND energy >= ?"
            params.append(min_energy)
        
        if max_energy is not None:
            query += " AND energy <= ?"
            params.append(max_energy)
        
        if min_might is not None:
            query += " AND might >= ?"
            params.append(min_might)
        
        if max_might is not None:
            query += " AND might <= ?"
            params.append(max_might)
        
        if min_power is not None:
            query += " AND power >= ?"
            params.append(min_power)
        
        if max_power is not None:
            query += " AND power <= ?"
            params.append(max_power)
        
        if tags:
            # Search for any of the specified tags
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
            query += f" AND ({' OR '.join(tag_conditions)})"
        
        if colors:
            # Search for any of the specified colors
            color_conditions = []
            for color in colors:
                color_conditions.append("colors LIKE ?")
                params.append(f"%{color}%")
            query += f" AND ({' OR '.join(color_conditions)})"
        
        if variant_type:
            query += " AND variant_type = ?"
            params.append(variant_type)
        
        if owned_only:
            query += " AND quantity > 0"
        
        # Order by precomputed variant order for consistent results
        query += " ORDER BY set_prefix, variant_order_num, variant_order_suffix"
        
        print(f"Search query: {query}")
        print(f"Search params: {params}")
        
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            cards = []
            for row in cursor.fetchall():
                card = PiltoverCard(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    super=row[3],
                    description=row[4],
                    energy=row[5],
                    might=row[6],
                    power=row[7],
                    tags=json.loads(row[8]),
                    variant_id=row[9],
                    variant_number=row[10],
                    image_url=row[11],
                    rarity=row[12],
                    flavor_text=row[13],
                    artist=row[14],
                    release_date=row[15],
                    variant_type=row[16],
                    set_id=row[17],
                    set_name=row[18],
                    set_prefix=row[19],
                    colors=json.loads(row[20]),
                    quantity=row[21],
                    condition=row[22],
                    acquisition_date=row[23],
                    personal_notes=row[24]
                )
                cards.append(card)
            
            print(f"Search returned {len(cards)} cards")
            return cards
    
    def get_card_by_variant_id(self, variant_id: str) -> Optional[PiltoverCard]:
        """Get a specific card variant by variant ID"""
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cards WHERE variant_id = ?", (variant_id,))
            row = cursor.fetchone()
            
            if row:
                return PiltoverCard(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    super=row[3],
                    description=row[4],
                    energy=row[5],
                    might=row[6],
                    power=row[7],
                    tags=json.loads(row[8]),
                    variant_id=row[9],
                    variant_number=row[10],
                    image_url=row[11],
                    rarity=row[12],
                    flavor_text=row[13],
                    artist=row[14],
                    release_date=row[15],
                    variant_type=row[16],
                    set_id=row[17],
                    set_name=row[18],
                    set_prefix=row[19],
                    colors=json.loads(row[20]),
                    quantity=row[21],
                    condition=row[22],
                    acquisition_date=row[23],
                    personal_notes=row[24]
                )
            return None
    
    def get_card_by_variant_number(self, variant_number: str) -> Optional[PiltoverCard]:
        """Get a specific card variant by variant number (e.g., 'OGN-066')"""
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cards WHERE variant_number = ?", (variant_number,))
            row = cursor.fetchone()
            
            if row:
                return PiltoverCard(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    super=row[3],
                    description=row[4],
                    energy=row[5],
                    might=row[6],
                    power=row[7],
                    tags=json.loads(row[8]),
                    variant_id=row[9],
                    variant_number=row[10],
                    image_url=row[11],
                    rarity=row[12],
                    flavor_text=row[13],
                    artist=row[14],
                    release_date=row[15],
                    variant_type=row[16],
                    set_id=row[17],
                    set_name=row[18],
                    set_prefix=row[19],
                    colors=json.loads(row[20]),
                    quantity=row[21],
                    condition=row[22],
                    acquisition_date=row[23],
                    personal_notes=row[24]
                )
            return None
    
    def update_collection_data(self, variant_id: str, **kwargs):
        """Update collection-specific data for a card variant"""
        allowed_fields = ['quantity', 'condition', 'acquisition_date', 'personal_notes']
        
        updates = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return
        
        params.append(variant_id)
        query = f"UPDATE cards SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE variant_id = ?"
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            
            # Total variants owned
            cursor.execute("SELECT COUNT(*) FROM cards WHERE quantity > 0")
            total_owned = cursor.fetchone()[0]
            
            # Total unique cards owned
            cursor.execute("SELECT COUNT(DISTINCT id) FROM cards WHERE quantity > 0")
            unique_cards = cursor.fetchone()[0]
            
            # Total quantity
            cursor.execute("SELECT SUM(quantity) FROM cards WHERE quantity > 0")
            total_quantity = cursor.fetchone()[0] or 0
            
            # Variants by set
            cursor.execute("""
                SELECT set_prefix, COUNT(*) as count 
                FROM cards 
                WHERE quantity > 0 
                GROUP BY set_prefix
            """)
            by_set = dict(cursor.fetchall())
            
            # Variants by rarity
            cursor.execute("""
                SELECT rarity, COUNT(*) as count 
                FROM cards 
                WHERE quantity > 0 
                GROUP BY rarity
            """)
            by_rarity = dict(cursor.fetchall())
            
            # Variants by artist
            cursor.execute("""
                SELECT artist, COUNT(*) as count 
                FROM cards 
                WHERE quantity > 0 
                GROUP BY artist
                ORDER BY count DESC
                LIMIT 10
            """)
            by_artist = dict(cursor.fetchall())
            
            return {
                'total_owned': total_owned,
                'unique_cards': unique_cards,
                'total_quantity': total_quantity,
                'by_set': by_set,
                'by_rarity': by_rarity,
                'by_artist': by_artist
            }
    
    def get_all_variants(self, limit: Optional[int] = None) -> List[PiltoverCard]:
        """Get all variants, optionally limited"""
        query = "SELECT * FROM cards ORDER BY set_prefix, variant_order_num, variant_order_suffix"
        if limit:
            query += f" LIMIT {limit}"
        
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            cards = []
            for row in cursor.fetchall():
                card = PiltoverCard(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    super=row[3],
                    description=row[4],
                    energy=row[5],
                    might=row[6],
                    power=row[7],
                    tags=json.loads(row[8]),
                    variant_id=row[9],
                    variant_number=row[10],
                    image_url=row[11],
                    rarity=row[12],
                    flavor_text=row[13],
                    artist=row[14],
                    release_date=row[15],
                    variant_type=row[16],
                    set_id=row[17],
                    set_name=row[18],
                    set_prefix=row[19],
                    colors=json.loads(row[20]),
                    quantity=row[21],
                    condition=row[22],
                    acquisition_date=row[23],
                    personal_notes=row[24]
                )
                cards.append(card)
            
            return cards

    # Metadata helpers
    def get_metadata(self, key: str) -> Optional[str]:
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM meta WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)", (key, value))
            conn.commit()

    # Distinct queries for UI dropdowns
    def get_distinct_set_names(self) -> List[str]:
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT set_name FROM cards ORDER BY set_name")
            return [row[0] for row in cursor.fetchall()]

    def get_distinct_rarities(self) -> List[str]:
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT rarity FROM cards ORDER BY rarity")
            return [row[0] for row in cursor.fetchall()]

    def get_distinct_supertypes(self) -> List[str]:
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT super FROM cards WHERE TRIM(COALESCE(super, '')) <> '' ORDER BY super")
            return [row[0] for row in cursor.fetchall()]

    def get_distinct_types(self) -> List[str]:
        with self._connect_ro() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT type FROM cards ORDER BY type")
            return [row[0] for row in cursor.fetchall()]
