#!/usr/bin/env python3
"""
Riftbound Card Scraper - Command Line Interface
===============================================

This script provides a command-line interface for scraping card data from
Piltover Archive and updating your existing JSON database files.

Usage:
    python run_card_scraper.py [command] [options]

Commands:
    test           - Test the scraper and show sample data
    scrape         - Fetch all cards from the API
    merge-ogn      - Update Origins (OGN) set with scraped data
    merge-ogs      - Update Proving Grounds (OGS) set with scraped data
    merge-all      - Update all sets with scraped data
    help           - Show this help message
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraping.piltover_scraper import PiltoverArchiveAPIScraper
from scraping.card_data_updater import CardDataMerger


def print_banner():
    """Print a nice banner for the application."""
    print("=" * 60)
    print("    PILTOVER ARCHIVE CARD SCRAPER")
    print("    Fetching missing card information...")
    print("=" * 60)
    print()


def print_help():
    """Print help information."""
    print("Usage: python run_card_scraper.py [command]")
    print()
    print("Commands:")
    print("  test          - Test the scraper with a sample request")
    print("  scrape        - Fetch all card data from the API")
    print("  merge-ogn     - Update Origins (OGN) card data")
    print("  merge-ogs     - Update Proving Grounds (OGS) card data")
    print("  merge-all     - Update all card sets")
    print("  help          - Show this help message")
    print()
    print("Examples:")
    print("  python run_card_scraper.py test")
    print("  python run_card_scraper.py merge-all")


def test_scraper():
    """Test the scraper functionality."""
    print("Testing the card scraper...")
    print()
    
    scraper = PiltoverArchiveAPIScraper()
    
    try:
        # Test fetching all cards
        print("1. Testing API connection...")
        cards = scraper.get_all_cards()
        
        if not cards:
            print("❌ Failed to fetch cards from API")
            return False
        
        print(f"✅ Successfully fetched {len(cards)} cards!")
        
        # Test set filtering
        print("\n2. Testing set filtering...")
        ogn_cards = scraper.get_cards_by_set('OGN')
        ogs_cards = scraper.get_cards_by_set('OGS')
        
        print(f"✅ Origins (OGN): {len(ogn_cards)} cards")
        print(f"✅ Proving Grounds (OGS): {len(ogs_cards)} cards")
        
        # Show sample data
        if cards:
            print("\n3. Sample card data:")
            sample_card = cards[0]
            print(f"   Name: {sample_card.get('name', 'N/A')}")
            print(f"   Type: {sample_card.get('type', 'N/A')}")
            print(f"   Description: {sample_card.get('description', 'N/A')[:80]}...")
            
            if 'cardVariants' in sample_card and sample_card['cardVariants']:
                variant = sample_card['cardVariants'][0]
                print(f"   Variant: {variant.get('variantNumber', 'N/A')}")
                print(f"   Flavor Text: {variant.get('flavorText', 'N/A')}")
                print(f"   Artist: {variant.get('artist', 'N/A')}")
        
        print("\n✅ All tests passed! The scraper is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


def scrape_cards():
    """Fetch all card data from the API."""
    print("Fetching all card data from Piltover Archive...")
    print()
    
    scraper = PiltoverArchiveAPIScraper()
    
    try:
        cards = scraper.get_all_cards()
        
        if not cards:
            print("❌ Failed to fetch cards")
            return False
        
        print(f"✅ Successfully fetched {len(cards)} cards!")
        
        # Show summary by set
        ogn_cards = scraper.get_cards_by_set('OGN')
        ogs_cards = scraper.get_cards_by_set('OGS')
        
        print(f"\n📊 Summary:")
        print(f"   Total cards: {len(cards)}")
        print(f"   Origins (OGN): {len(ogn_cards)}")
        print(f"   Proving Grounds (OGS): {len(ogs_cards)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return False


def merge_data(set_name: str):
    """Merge data for a specific set."""
    print(f"Merging data for {set_name}...")
    print()
    
    merger = CardDataMerger()
    
    try:
        if set_name == "OGN":
            success = merger.merge_data_for_set("riftbound_origins.json", "OGN")
        elif set_name == "OGS":
            success = merger.merge_data_for_set("riftbound_proving_grounds.json", "OGS")
        else:
            print(f"❌ Unknown set: {set_name}")
            return False
        
        if success:
            print(f"✅ Successfully updated {set_name} data!")
        else:
            print(f"❌ Failed to update {set_name} data")
        
        return success
        
    except Exception as e:
        print(f"❌ Merge failed: {e}")
        return False


def merge_all_data():
    """Merge data for all card sets."""
    print("Merging data for all card sets...")
    print()
    
    merger = CardDataMerger()
    
    try:
        merger.merge_all_sets()
        print("\n✅ All data merged successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Merge failed: {e}")
        return False


def main():
    """Main function to handle command-line arguments."""
    print_banner()
    
    if len(sys.argv) < 2:
        print("No command specified. Use 'help' to see available commands.")
        print()
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "test":
        success = test_scraper()
        sys.exit(0 if success else 1)
        
    elif command == "scrape":
        success = scrape_cards()
        sys.exit(0 if success else 1)
        
    elif command == "merge-ogn":
        success = merge_data("OGN")
        sys.exit(0 if success else 1)
        
    elif command == "merge-ogs":
        success = merge_data("OGS")
        sys.exit(0 if success else 1)
        
    elif command == "merge-all":
        success = merge_all_data()
        sys.exit(0 if success else 1)
        
    elif command == "help":
        print_help()
        
    else:
        print(f"Unknown command: {command}")
        print()
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
