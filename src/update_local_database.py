#!/usr/bin/env python3
"""
Local Database Updater
Updates the SQLite database from the local cards.json file
"""

import json
import os
from pathlib import Path
from src.models.piltover_card_database import PiltoverCardDatabase
import hashlib


class LocalDatabaseUpdater:
    """Updates the local SQLite database from cards.json"""
    
    def __init__(self):
        self.database = PiltoverCardDatabase()
        self.cards_json_path = Path(__file__).resolve().parents[1] / "card_data" / "cards.json"
    
    def update_database(self):
        """Update the database from the local cards.json file"""
        try:
            print("🔄 Starting local database update...")
            
            # Check if cards.json exists
            if not self.cards_json_path.exists():
                print(f"❌ Cards file not found: {self.cards_json_path}")
                return False
            
            # Load the JSON data
            print("📖 Loading cards.json...")
            with open(self.cards_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            variants = data.get('variants', [])
            print(f"📊 Found {len(variants)} card variants in cards.json")
            
            if not variants:
                print("❌ No variants found in cards.json")
                return False
            
            # Skip if content hash matches last imported
            content_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
            last_hash = self.database.get_metadata('cards_json_hash')
            if last_hash == content_hash:
                print("✅ Local database is already up to date (hash match). Skipping import.")
                return True

            # Clear existing database and import fresh data
            print("🗑️  Clearing existing database...")
            self.database.clear_database()
            
            print("💾 Importing variants to database...")
            success = self.database.import_from_sorted_json(str(self.cards_json_path))
            
            if success:
                print("✅ Database updated successfully!")
                self.database.set_metadata('cards_json_hash', content_hash)
                return True
            else:
                print("❌ Failed to import variants")
                return False
                
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            return False


def main():
    """Main function for command line usage"""
    updater = LocalDatabaseUpdater()
    success = updater.update_database()
    
    if success:
        print("🎉 Local database update completed successfully!")
    else:
        print("💥 Local database update failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
