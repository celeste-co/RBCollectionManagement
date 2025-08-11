"""
Data importer utility for loading JSON card data into SQLite database
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from src.models.card_database import CardDatabase

class DataImporter:
    """Utility for importing card data from JSON files"""
    
    def __init__(self, database: CardDatabase):
        self.database = database
    
    def import_all_sets(self, card_data_dir: str = "card_data"):
        """Import all JSON files from the card_data directory"""
        card_data_path = Path(card_data_dir)
        
        if not card_data_path.exists():
            print(f"Card data directory not found: {card_data_path}")
            return
        
        json_files = list(card_data_path.glob("*.json"))
        
        if not json_files:
            print(f"No JSON files found in {card_data_path}")
            return
        
        print(f"Found {len(json_files)} JSON files to import")
        
        for json_file in json_files:
            set_name = json_file.stem.replace("_", " ").title()
            print(f"Importing {set_name} from {json_file.name}...")
            
            try:
                self.database.import_from_json(str(json_file), set_name)
                print(f"✓ Successfully imported {set_name}")
            except Exception as e:
                print(f"✗ Error importing {set_name}: {str(e)}")
        
        print("\nImport completed!")
        self.print_import_summary()
    
    def print_import_summary(self):
        """Print summary of imported data"""
        try:
            stats = self.database.get_collection_stats()
            
            # Get total cards in database
            all_cards = self.database.search_cards()
            total_cards = len(all_cards)
            
            print(f"\n📊 Database Summary:")
            print(f"   Total cards: {total_cards}")
            print(f"   Cards owned: {stats['total_owned']}")
            print(f"   Unique owned: {stats['unique_cards']}")
            print(f"   Total quantity: {stats['total_quantity']}")
            
            if stats['by_set']:
                print(f"\n📦 Cards by Set:")
                for set_name, count in stats['by_set'].items():
                    print(f"   {set_name}: {count}")
            
            if stats['by_domain']:
                print(f"\n🏛️  Cards by Domain:")
                for domain, count in stats['by_domain'].items():
                    print(f"   {domain}: {count}")
                    
        except Exception as e:
            print(f"Error getting summary: {str(e)}")
    
    def validate_json_structure(self, json_file_path: str) -> Dict:
        """Validate JSON file structure and return analysis"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                return {"valid": False, "error": "Data must be a list of cards"}
            
            if not data:
                return {"valid": False, "error": "No cards found in file"}
            
            # Analyze first card structure
            first_card = data[0]
            required_fields = ['id', 'name', 'domain', 'rarity', 'type']
            missing_fields = [field for field in required_fields if field not in first_card]
            
            if missing_fields:
                return {
                    "valid": False, 
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Count cards by domain and rarity
            domain_counts = {}
            rarity_counts = {}
            type_counts = {}
            
            for card in data:
                domain = card.get('domain', 'Unknown')
                rarity = card.get('rarity', 'Unknown')
                card_type = card.get('type', 'Unknown')
                
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
                type_counts[card_type] = type_counts.get(card_type, 0) + 1
            
            return {
                "valid": True,
                "total_cards": len(data),
                "domains": domain_counts,
                "rarities": rarity_counts,
                "types": type_counts,
                "sample_card": first_card
            }
            
        except json.JSONDecodeError as e:
            return {"valid": False, "error": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            return {"valid": False, "error": f"Error reading file: {str(e)}"}
    
    def print_validation_report(self, json_file_path: str):
        """Print detailed validation report for a JSON file"""
        print(f"\n🔍 Validating {json_file_path}...")
        
        validation = self.validate_json_structure(json_file_path)
        
        if not validation["valid"]:
            print(f"❌ Validation failed: {validation['error']}")
            return
        
        print(f"✅ File is valid!")
        print(f"📊 Total cards: {validation['total_cards']}")
        
        print(f"\n🏛️  Domains:")
        for domain, count in validation['domains'].items():
            print(f"   {domain}: {count}")
        
        print(f"\n⭐ Rarities:")
        for rarity, count in validation['rarities'].items():
            print(f"   {rarity}: {count}")
        
        print(f"\n🎴 Card Types:")
        for card_type, count in validation['types'].items():
            print(f"   {card_type}: {count}")
        
        print(f"\n📝 Sample card structure:")
        sample = validation['sample_card']
        for key, value in sample.items():
            print(f"   {key}: {type(value).__name__} = {value}")

def main():
    """Main function for command-line usage"""
    print("🃏 Riftbound TCG Data Importer")
    print("=" * 40)
    
    # Initialize database
    db = CardDatabase()
    importer = DataImporter(db)
    
    # Validate existing JSON files
    card_data_dir = "card_data"
    if os.path.exists(card_data_dir):
        print(f"\nValidating existing JSON files in {card_data_dir}...")
        
        for json_file in Path(card_data_dir).glob("*.json"):
            importer.print_validation_report(str(json_file))
    
    # Ask user if they want to import
    print(f"\n" + "=" * 40)
    response = input("Do you want to import all JSON files into the database? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        importer.import_all_sets()
    else:
        print("Import skipped. You can run this utility later.")

if __name__ == "__main__":
    main()
