#!/usr/bin/env python3
"""
Database Updater for Piltover Archive

This program:
1. Downloads fresh card data from Piltover Archive
2. Compares it with the current local data
3. Updates the database if there are differences
4. Cleans up temporary files
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the src directory to the path so we can import our modules
current_file = Path(__file__).resolve()
src_dir = current_file.parent
sys.path.insert(0, str(src_dir))

from scraping.piltover_scraper import PiltoverArchiveAPIScraper
from models.piltover_card_database import PiltoverCardDatabase


class DatabaseUpdater:
    """Handles updating the database from Piltover Archive"""
    
    def __init__(self):
        self.card_data_dir = os.path.join(src_dir.parent, "card_data")
        self.current_cards_file = os.path.join(self.card_data_dir, "cards.json")
        self.temp_cards_file = os.path.join(self.card_data_dir, "temp_cards.json")
        self.scraper = PiltoverArchiveAPIScraper()
        self.database = PiltoverCardDatabase()
    
    def download_fresh_data(self) -> bool:
        """Download fresh data from Piltover Archive"""
        print("📡 Downloading fresh data from Piltover Archive...")
        
        try:
            cards = self.scraper.get_all_cards()
            print(f"✅ Successfully downloaded {len(cards)} cards")
            
            # Save to temporary file
            self.scraper.save_cards_to_file(cards, self.temp_cards_file)
            print(f"💾 Temporary data saved to: {self.temp_cards_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error downloading data: {e}")
            return False
    
    def reorganize_temp_data(self) -> bool:
        """Reorganize the temporary downloaded data"""
        print("🔄 Reorganizing temporary data...")
        
        try:
            # Create a temporary reorganizer that works with the temp file
            temp_reorganizer = TempDataReorganizer(
                input_file=self.temp_cards_file,
                output_file=os.path.join(self.card_data_dir, "temp_cards_sorted.json")
            )
            
            success = temp_reorganizer.reorganize()
            if success:
                print("✅ Temporary data reorganized successfully")
                return True
            else:
                print("❌ Failed to reorganize temporary data")
                return False
                
        except Exception as e:
            print(f"❌ Error reorganizing temporary data: {e}")
            return False
    
    def compare_data(self) -> bool:
        """Compare current data with fresh data"""
        print("🔍 Comparing current data with fresh data...")
        
        try:
            # Load current data
            with open(self.current_cards_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            
            # Load fresh data
            temp_sorted_file = os.path.join(self.card_data_dir, "temp_cards_sorted.json")
            with open(temp_sorted_file, 'r', encoding='utf-8') as f:
                fresh_data = json.load(f)
            
            # Compare metadata
            current_hash = hashlib.md5(json.dumps(current_data, sort_keys=True).encode()).hexdigest()
            fresh_hash = hashlib.md5(json.dumps(fresh_data, sort_keys=True).encode()).hexdigest()
            
            print(f"📊 Current data hash: {current_hash[:8]}...")
            print(f"📊 Fresh data hash: {fresh_hash[:8]}...")
            
            if current_hash == fresh_hash:
                print("✅ Data is up to date - no changes detected")
                return False
            else:
                print("🔄 Changes detected - update needed")
                return True
                
        except Exception as e:
            print(f"❌ Error comparing data: {e}")
            return False
    
    def update_database(self) -> bool:
        """Update the database with fresh data"""
        print("💾 Updating database...")
        
        try:
            # Move fresh data to current location
            temp_sorted_file = os.path.join(self.card_data_dir, "temp_cards_sorted.json")
            os.replace(temp_sorted_file, self.current_cards_file)
            print("✅ Fresh data moved to current location")
            
            # Import to database
            success = self.database.import_from_sorted_json(self.current_cards_file)
            if success:
                print("✅ Database updated successfully")
                return True
            else:
                print("❌ Failed to update database")
                return False
                
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        print("🧹 Cleaning up temporary files...")
        
        temp_files = [
            self.temp_cards_file,
            os.path.join(self.card_data_dir, "temp_cards_sorted.json")
        ]
        
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"🗑️  Removed: {temp_file}")
                except Exception as e:
                    print(f"⚠️  Could not remove {temp_file}: {e}")
    
    def update(self) -> bool:
        """Main update process"""
        print("🚀 Starting database update process...")
        print("=" * 50)
        
        try:
            # Step 1: Download fresh data
            if not self.download_fresh_data():
                return False
            
            # Step 2: Reorganize temporary data
            if not self.reorganize_temp_data():
                self.cleanup_temp_files()
                return False
            
            # Step 3: Compare data
            if not self.compare_data():
                print("🎉 No update needed - database is current")
                self.cleanup_temp_files()
                return True
            
            # Step 4: Update database
            if not self.update_database():
                self.cleanup_temp_files()
                return False
            
            # Step 5: Cleanup
            self.cleanup_temp_files()
            
            print("\n🎉 Database update completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Unexpected error during update: {e}")
            self.cleanup_temp_files()
            return False


class TempDataReorganizer:
    """Temporary reorganizer for downloaded data"""
    
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
    
    def reorganize(self) -> bool:
        """Reorganize the temporary data"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract the actual card data from the nested structure
            cards = data['json'][2][0][0]
            
            # Extract variants
            all_variants = []
            for card in cards:
                card_base = {
                    'id': card['id'],
                    'name': card['name'],
                    'type': card['type'],
                    'super': card['super'],
                    'description': card['description'],
                    'energy': card['energy'],
                    'might': card['might'],
                    'power': card['power'],
                    'tags': card['tags'],
                    'cardColors': card['cardColors'],
                    'createdAt': card['createdAt'],
                    'updatedAt': card['updatedAt']
                }
                
                # Extract each variant
                for variant in card.get('cardVariants', []):
                    variant_entry = card_base.copy()
                    variant_entry.update({
                        'variantId': variant['id'],
                        'variantNumber': variant['variantNumber'],
                        'imageUrl': variant['imageUrl'],
                        'rarity': variant['rarity'],
                        'flavorText': variant['flavorText'],
                        'artist': variant['artist'],
                        'releaseDate': variant['releaseDate'],
                        'variantType': variant['variantType'],
                        'set': variant['set']
                    })
                    all_variants.append(variant_entry)
            
            # Sort variants
            def extract_sort_key(variant):
                variant_num = variant['variantNumber']
                parts = variant_num.split('-')
                if len(parts) != 2:
                    return (variant_num, 0)
                
                set_prefix = parts[0]
                number_part = parts[1]
                
                numeric = ''
                letter = ''
                for char in number_part:
                    if char.isdigit():
                        numeric += char
                    else:
                        letter += char
                
                numeric_val = int(numeric) if numeric else 0
                letter_val = ord(letter) if letter else 0
                
                return (set_prefix, numeric_val, letter_val)
            
            sorted_variants = sorted(all_variants, key=extract_sort_key)
            
            # Save sorted data
            output_data = {
                "metadata": {
                    "source": "Piltover Archive",
                    "totalVariants": len(sorted_variants),
                    "lastUpdated": "2025-08-11",
                    "description": "Riftbound cards sorted by variant number"
                },
                "variants": sorted_variants
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Error reorganizing temporary data: {e}")
            return False


def main():
    """Main function"""
    updater = DatabaseUpdater()
    success = updater.update()
    
    if success:
        print("\n✅ Update process completed successfully!")
    else:
        print("\n❌ Update process failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
