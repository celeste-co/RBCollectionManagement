import json
import os
from typing import Dict, List, Optional
from .piltover_scraper import PiltoverArchiveAPIScraper


class CardDataMerger:
    """
    Utility to merge scraped card data with existing JSON database files.
    """
    
    def __init__(self, card_data_dir: str = "card_data"):
        # Get the project root directory (parent of src)
        import os
        # Since we're in src/utils/, go up two levels to get to project root
        current_file = os.path.abspath(__file__)
        utils_dir = os.path.dirname(current_file)
        src_dir = os.path.dirname(utils_dir)
        project_root = os.path.dirname(src_dir)
        self.card_data_dir = os.path.join(project_root, card_data_dir)
        self.scraper = PiltoverArchiveAPIScraper()
    
    def load_existing_data(self, filename: str) -> List[Dict]:
        """
        Load existing card data from JSON file.
        
        Args:
            filename: Name of the JSON file to load
            
        Returns:
            List of existing card dictionaries
        """
        filepath = os.path.join(self.card_data_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Loaded {len(data)} cards from {filename}")
            return data
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return []
    
    def save_updated_data(self, data: List[Dict], filename: str, backup: bool = True):
        """
        Save updated card data to JSON file with optional backup.
        
        Args:
            data: Updated card data to save
            filename: Name of the JSON file to save
            backup: Whether to create a backup of the original file
        """
        filepath = os.path.join(self.card_data_dir, filename)
        
        # Create backup if requested
        if backup and os.path.exists(filepath):
            backup_path = filepath.replace('.json', '_backup.json')
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    backup_data = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(backup_data)
                print(f"Created backup: {backup_path}")
            except Exception as e:
                print(f"Warning: Could not create backup: {e}")
        
        # Save updated data
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved {len(data)} cards to {filename}")
        except Exception as e:
            print(f"Error saving {filename}: {e}")
    
    def find_matching_card(self, card_name: str, scraped_cards: List[Dict]) -> Optional[Dict]:
        """
        Find a matching card in the scraped data by name.
        
        Args:
            card_name: Name of the card to find
            scraped_cards: List of scraped card dictionaries
            
        Returns:
            Matching scraped card or None
        """
        for card in scraped_cards:
            if card.get('name') == card_name:
                return card
        return None
    
    def update_card_with_missing_fields(self, existing_card: Dict, scraped_card: Dict) -> Dict:
        """
        Update an existing card with missing fields from scraped data.
        
        Args:
            existing_card: Existing card data
            scraped_card: Scraped card data with missing fields
            
        Returns:
            Updated card dictionary
        """
        updated_card = existing_card.copy()
        
        # Add missing fields if they don't exist or are empty
        if not existing_card.get('description') and scraped_card.get('description'):
            updated_card['description'] = scraped_card['description']
        
        # Extract flavor text and artist from variants
        if 'cardVariants' in scraped_card and scraped_card['cardVariants']:
            # Find the matching variant by card number
            card_number = existing_card.get('card_number', '')
            matching_variant = None
            
            for variant in scraped_card['cardVariants']:
                if variant.get('variantNumber') == card_number:
                    matching_variant = variant
                    break
            
            # If no exact match, use the first variant
            if not matching_variant and scraped_card['cardVariants']:
                matching_variant = scraped_card['cardVariants'][0]
            
            if matching_variant:
                if not existing_card.get('flavor_text') and matching_variant.get('flavorText'):
                    updated_card['flavor_text'] = matching_variant['flavorText']
                
                if not existing_card.get('artist') and matching_variant.get('artist'):
                    updated_card['artist'] = matching_variant['artist']
        
        return updated_card
    
    def merge_data_for_set(self, filename: str, set_prefix: str) -> bool:
        """
        Merge scraped data for a specific card set.
        
        Args:
            filename: JSON filename to update
            set_prefix: Set prefix to filter scraped cards (e.g., 'OGN', 'OGS')
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n=== Merging data for {filename} (set: {set_prefix}) ===")
        
        # Load existing data
        existing_cards = self.load_existing_data(filename)
        if not existing_cards:
            return False
        
        # Get scraped cards for this set
        scraped_cards = self.scraper.get_cards_by_set(set_prefix)
        if not scraped_cards:
            print(f"No scraped cards found for set {set_prefix}")
            return False
        
        # Create a lookup dictionary for scraped cards
        scraped_lookup = {card['name']: card for card in scraped_cards}
        
        # Update existing cards
        updated_count = 0
        updated_cards = []
        
        for existing_card in existing_cards:
            card_name = existing_card.get('name', '')
            scraped_card = scraped_lookup.get(card_name)
            
            if scraped_card:
                updated_card = self.update_card_with_missing_fields(existing_card, scraped_card)
                updated_cards.append(updated_card)
                
                # Check if any fields were actually updated
                if (updated_card.get('description') != existing_card.get('description') or
                    updated_card.get('flavor_text') != existing_card.get('flavor_text') or
                    updated_card.get('artist') != existing_card.get('artist')):
                    updated_count += 1
                    print(f"Updated: {card_name}")
            else:
                updated_cards.append(existing_card)
                print(f"No match found: {card_name}")
        
        # Save updated data
        self.save_updated_data(updated_cards, filename)
        print(f"Updated {updated_count} cards with new information")
        
        return True
    
    def merge_all_sets(self):
        """
        Merge data for all card sets.
        """
        print("Starting data merge for all card sets...")
        
        # Define the sets to process
        sets_to_process = [
            ("riftbound_origins.json", "OGN"),
            ("riftbound_proving_grounds.json", "OGS")
        ]
        
        success_count = 0
        for filename, set_prefix in sets_to_process:
            if self.merge_data_for_set(filename, set_prefix):
                success_count += 1
        
        print(f"\nData merge completed. Successfully processed {success_count}/{len(sets_to_process)} sets.")


def main():
    """Test the data merger"""
    merger = CardDataMerger()
    
    # Test merging for a single set first
    print("Testing data merger...")
    
    # Test with Origins set
    success = merger.merge_data_for_set("riftbound_origins.json", "OGN")
    
    if success:
        print("\nTest successful! You can now run merge_all_sets() to update all files.")
    else:
        print("\nTest failed. Check the error messages above.")


if __name__ == "__main__":
    main()
