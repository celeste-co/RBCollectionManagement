# Riftbound TCG Collection Management

A comprehensive collection management application for the Riftbound Trading Card Game, featuring automated data collection from [Piltover Archive](https://piltoverarchive.com/cards).

## 🚀 Key Features

- **Automated Data Collection**: Fetches card data directly from [Piltover Archive](https://piltoverarchive.com/cards)
- **Modern Database**: Uses SQLite with a comprehensive card schema including variants, artists, and metadata
- **Smart Updates**: Automatically detects changes and updates only when necessary
- **Rich Search Interface**: Advanced filtering by set, rarity, type, domains, and more
- **Image Support**: Displays card images with hover tooltips
- **Collection Tracking**: Track owned cards, quantities, and conditions

## 🏗️ Project Structure

```
RBCollectionManagement/
├── card_data/
│   └── cards.json              # Consolidated card database
├── card_img/                   # Card images organized by set
├── src/
│   ├── models/
│   │   └── piltover_card_database.py  # Database model and operations
│   ├── scraping/
│   │   └── piltover_scraper.py        # API scraper for Piltover Archive
│   ├── ui/
│   │   ├── content_area.py            # Main content area
│   │   ├── search_widget.py           # Advanced search interface
│   │   └── sidebar.py                 # Navigation sidebar
│   ├── main_piltover.py              # Main application entry point
│   └── update_database.py            # Database updater utility
├── collection.db                      # SQLite database
└── requirements.txt                   # Python dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Update Card Database
```bash
python src/update_database.py
```

### 3. Launch Application
```bash
python src/main_piltover.py
```

## 🔄 Database Updates

The `update_database.py` script automatically:
1. Downloads fresh data from Piltover Archive
2. Compares with local data using MD5 hashing
3. Updates the database only when changes are detected
4. Cleans up temporary files

Run this script whenever you want to check for new cards or updates.

## 🎯 Main Application

The main application (`main_piltover.py`) provides:
- **Card Browser**: Search and filter through all cards
- **Advanced Filters**: Filter by set, rarity, type, domains, energy, might, and power
- **Image Previews**: Hover over card names to see images
- **Collection Management**: Track owned cards and quantities

## 🗄️ Database Schema

The application uses a modern SQLite schema that stores:
- **Card Information**: Name, type, description, flavor text, artist
- **Game Mechanics**: Energy cost, might, power, tags
- **Variants**: Multiple printings of the same card
- **Set Information**: Origin (OGN) and Proving Grounds (OGS)
- **Collection Data**: Ownership status, quantities, conditions

## 🔧 Development

### Adding New Features
- **UI Components**: Add to `src/ui/` directory
- **Database Operations**: Extend `PiltoverCardDatabase` class
- **Data Sources**: Extend `PiltoverArchiveAPIScraper` class

### Testing
```bash
# Test database updater
python src/update_database.py

# Test scraper directly
python src/scraping/piltover_scraper.py
```

## 📝 License

This project is open source and available under the MIT License.
