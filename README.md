# Riftbound Collection Management

A comprehensive tool for managing your Riftbound card collection, including automated data scraping from Piltover Archive.

## 🎯 Project Overview

This project helps you maintain a complete database of Riftbound cards with rich information including:
- **Card Details**: Name, type, energy cost, might, power, rarity, etc.
- **Game Mechanics**: Description text and abilities
- **Art Information**: Artist names and flavor text
- **Set Organization**: Origins (OGN) and Proving Grounds (OGS) sets

## 📁 Project Structure

```
RBCollectionManagement/
├── card_data/                          # Your card database files
│   ├── riftbound_origins.json         # Origins set (OGN) - 351 cards
│   └── riftbound_proving_grounds.json # Proving Grounds set (OGS) - 24 cards
├── card_img/                           # Card images organized by set
│   ├── OGN/                           # Origins card images
│   └── OGS/                           # Proving Grounds card images
├── src/                                # Source code
│   ├── scraping/                       # 🆕 Card scraping package
│   │   ├── __init__.py                # Package initialization
│   │   ├── piltover_scraper.py        # Main API scraper
│   │   ├── card_data_updater.py       # Data merger utility
│   │   └── README.md                  # Scraping package documentation
│   ├── models/                         # Data models
│   │   └── card_database.py           # Card database models
│   ├── ui/                            # User interface components
│   │   ├── content_area.py            # Main content display
│   │   ├── search_widget.py           # Search functionality
│   │   └── sidebar.py                 # Navigation sidebar
│   ├── utils/                          # Utility functions
│   │   ├── config.py                  # Configuration settings
│   │   ├── data_importer.py           # Data import utilities
│   │   └── set_dual_domain_power_any.py # Special card logic
│   ├── run_card_scraper.py            # 🆕 Command-line scraper interface
│   ├── main.py                         # Main application entry point
│   └── __init__.py                    # Package initialization
├── requirements.txt                    # Python dependencies
└── README.md                          # This file
```

## 🚀 Key Features

### 🔍 **Automated Data Scraping**
- **Direct API Integration**: Fetches data from Piltover Archive's official API
- **Smart Data Merging**: Updates your existing database without losing data
- **Automatic Backups**: Creates backup files before making changes
- **Set Filtering**: Handles both Origins (OGN) and Proving Grounds (OGS) sets

### 📊 **Rich Card Information**
- **Game Mechanics**: Complete card descriptions and abilities
- **Art Details**: Artist names and thematic flavor text
- **Set Organization**: Proper categorization by expansion sets
- **Metadata**: Rarity, energy costs, power requirements, etc.

### 🛠️ **Easy to Use**
- **Command Line Interface**: Simple commands for all operations
- **Python API**: Programmatic access to all functionality
- **Automatic Updates**: Keep your database current with new information

## 🎮 Card Sets Supported

### Origins (OGN) - 351 Cards
The core set featuring fundamental cards and mechanics.

### Proving Grounds (OGS) - 24 Cards
A focused expansion set with specialized cards.

## 🚀 Quick Start

### 1. **Test the Scraper**
```bash
python src/run_card_scraper.py test
```

### 2. **Update Your Card Database**
```bash
# Update Origins set
python src/run_card_scraper.py merge-ogn

# Update Proving Grounds set
python src/run_card_scraper.py merge-ogs

# Update both sets at once
python src/run_card_scraper.py merge-all
```

### 3. **Run the Main Application**
```bash
python src/main.py
```

## 📚 Detailed Usage

### Command Line Interface

The `run_card_scraper.py` script provides several commands:

- **`test`**: Verify the scraper is working and show sample data
- **`scrape`**: Fetch all cards from the API (for inspection)
- **`merge-ogn`**: Update your Origins set with new information
- **`merge-ogs`**: Update your Proving Grounds set with new information
- **`merge-all`**: Update both sets at once
- **`help`**: Show available commands

### Python API

```python
from src.scraping import PiltoverArchiveAPIScraper, CardDataMerger

# Fetch all cards
scraper = PiltoverArchiveAPIScraper()
cards = scraper.get_all_cards()

# Update your database
merger = CardDataMerger()
merger.merge_all_sets()
```

## 🔧 Technical Details

### **Scraping Technology**
- **API-Based**: Direct calls to Piltover Archive's tRPC endpoint
- **Reliable**: No HTML parsing or browser automation
- **Efficient**: Single request fetches all 323 cards
- **Respectful**: Mimics legitimate browser requests

### **Data Processing**
- **Smart Matching**: Links scraped data to existing cards by name
- **Field Preservation**: Never overwrites existing data
- **Backup System**: Automatic backup creation before updates
- **Error Handling**: Graceful handling of missing or mismatched data

## 📦 Dependencies

- **Python 3.7+**
- **requests**: HTTP library for API calls
- **Standard library**: json, os, typing, urllib

## 🤝 Contributing

This project is designed to be easily extensible:
- Add new card sets by extending the scraping logic
- Implement new data fields in the merger
- Create additional UI components for the main application

## 📄 License

This project is for personal use and card collection management.

---

**Happy collecting!** 🃏✨
