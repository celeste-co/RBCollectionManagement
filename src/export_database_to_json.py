#!/usr/bin/env python3
"""
Export Database to JSON
Exports the current SQLite database back to cards.json
"""

import json
import os
from pathlib import Path
from src.models.piltover_card_database import PiltoverCardDatabase


class DatabaseExporter:
    """Exports the SQLite database to cards.json"""
    
    def __init__(self):
        self.database = PiltoverCardDatabase()
        self.cards_json_path = Path(__file__).resolve().parents[1] / "card_data" / "cards.json"
    
    def export_database(self):
        """Export the database to cards.json"""
        try:
            print("📤 Starting database export...")
            
            # Get all variants from database
            print("📖 Reading variants from database...")
            variants = self.database.get_all_variants()
            print(f"📊 Found {len(variants)} variants in database")
            
            if not variants:
                print("❌ No variants found in database")
                return False
            
            # Convert to JSON-serializable format
            variants_data = []
            for variant in variants:
                variant_dict = {
                    "id": variant.id,
                    "name": variant.name,
                    "type": variant.type,
                    "super": variant.super,
                    "description": variant.description,
                    "energy": variant.energy,
                    "might": variant.might,
                    "power": variant.power,
                    "tags": variant.tags,
                    "cardColors": variant.colors,
                    "createdAt": "2025-06-21T18:27:21.701Z",  # Default value
                    "updatedAt": "2025-06-21T18:27:21.701Z",  # Default value
                    "variantId": variant.variant_id,
                    "variantNumber": variant.variant_number,
                    "imageUrl": variant.image_url,
                    "rarity": variant.rarity,
                    "flavorText": variant.flavor_text,
                    "artist": variant.artist,
                    "releaseDate": variant.release_date,
                    "variantType": variant.variant_type,
                    "set": {
                        "id": variant.set_id,
                        "name": variant.set_name,
                        "prefix": variant.set_prefix,
                        "releaseDate": variant.release_date
                    }
                }
                variants_data.append(variant_dict)
            
            # Create the full JSON structure
            json_data = {
                "metadata": {
                    "source": "Piltover Archive",
                    "totalVariants": len(variants_data),
                    "lastUpdated": "2025-08-11",
                    "description": "Riftbound cards exported from database"
                },
                "variants": variants_data
            }
            
            # Write to cards.json
            print(f"💾 Writing {len(variants_data)} variants to {self.cards_json_path}")
            with open(self.cards_json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print("✅ Database export completed successfully!")
            return True
                
        except Exception as e:
            print(f"❌ Error exporting database: {e}")
            return False


def main():
    """Main function for command line usage"""
    exporter = DatabaseExporter()
    success = exporter.export_database()
    
    if success:
        print("🎉 Database export completed successfully!")
    else:
        print("💥 Database export failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
