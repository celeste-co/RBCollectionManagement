# Riftbound Card Scraping Package

This package contains tools for scraping card data from Piltover Archive and updating your existing JSON database files.

## File Structure

### `piltover_scraper.py`
**Main scraper class**: `PiltoverArchiveAPIScraper`

- **Purpose**: Fetches card data directly from the Piltover Archive API
- **Key Features**:
  - Direct API calls to `/api/trpc/cards.search`
  - Handles tRPC response format (multiple JSON objects)
  - Extracts card information: name, type, description, flavor text, artist
  - Filters cards by set prefix (OGN, OGS)
- **Methods**:
  - `get_all_cards()`: Fetch all 323 cards from the API
  - `get_cards_by_set(set_prefix)`: Filter cards by set
  - `extract_missing_fields(card)`: Extract description, flavor text, artist

### `card_data_updater.py`
**Data merger class**: `CardDataMerger`

- **Purpose**: Merges scraped card data with your existing JSON database files
- **Key Features**:
  - Loads existing JSON files from `card_data/` directory
  - Matches cards by name between scraped and existing data
  - Updates missing fields (description, flavor_text, artist)
  - Creates backup files before making changes
  - Handles both Origins (OGN) and Proving Grounds (OGS) sets
- **Methods**:
  - `merge_data_for_set(filename, set_prefix)`: Update a specific set
  - `merge_all_sets()`: Update all sets at once
  - `update_card_with_missing_fields()`: Smart field updating logic

### `find_missing_data.py`
**Data analysis class**: `MissingDataFinder`

- **Purpose**: Identifies cards missing specific data fields in your database
- **Key Features**:
  - Analyzes all card sets for missing information
  - Checks artist, description, and flavor_text fields
  - Provides detailed reports with card numbers and names
  - Calculates percentages of missing data
  - Supports filtering by specific fields or sets
- **Methods**:
  - `run_analysis(field, set_key)`: Analyze missing data
  - `analyze_set(set_key, field)`: Analyze a specific set
  - `print_analysis()`: Display formatted results

## How It Works

1. **Scraping**: `PiltoverArchiveAPIScraper` fetches all card data from the website's API
2. **Filtering**: Cards are filtered by set prefix (OGN/OGS) to match your JSON files
3. **Matching**: `CardDataMerger` matches scraped cards with existing cards by name
4. **Updating**: Missing fields are added to existing cards without overwriting existing data
5. **Backup**: Original files are backed up before changes are made
6. **Analysis**: `MissingDataFinder` helps identify remaining gaps in your data

## Usage

```python
from scraping import PiltoverArchiveAPIScraper, CardDataMerger, MissingDataFinder

# Test the scraper
scraper = PiltoverArchiveAPIScraper()
cards = scraper.get_all_cards()

# Update your data files
merger = CardDataMerger()
merger.merge_all_sets()

# Find missing data
finder = MissingDataFinder()
finder.run_analysis('artist')  # Check for missing artist information
```

## Command Line Interface

Use `run_card_scraper.py` in the parent directory for command-line operations:

```bash
python run_card_scraper.py test        # Test the scraper
python run_card_scraper.py merge-ogn   # Update Origins set
python run_card_scraper.py merge-ogs   # Update Proving Grounds set
python run_card_scraper.py merge-all   # Update all sets
```

### Data Analysis Commands

Use `find_missing_data.py` for analyzing your database:

```bash
python find_missing_data.py                    # Check all fields for all sets
python find_missing_data.py artist            # Check only artist field
python find_missing_data.py artist ogn        # Check artist field for Origins set only
python find_missing_data.py description ogs   # Check description field for Proving Grounds set only
```
