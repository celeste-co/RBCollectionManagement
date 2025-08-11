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
│   └── cards.json                    # Consolidated card database (377 variants)
├── card_img/                         # Card images organized by set
├── src/
│   ├── models/
│   │   └── piltover_card_database.py # SQLite database model
│   ├── ui/
│   │   ├── content_area.py           # Main content management
│   │   ├── search_widget.py          # Advanced search interface
│   │   └── sidebar.py                # Navigation sidebar
│   ├── main.py                       # Main application entry point
│   ├── update_local_database.py      # Local database updater (from cards.json)
│   ├── update_piltover_archive.py    # Piltover Archive updater (from API)
│   └── export_database_to_json.py    # Database export utility
├── collection.db                      # SQLite database
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup
The application automatically updates the database from `cards.json` on startup.

### 3. Launch Application
```bash
python src/main.py
```

## 🎯 Main Application

The main application (`main.py`) provides:
- **Card Browser**: Search and filter through all cards
- **Advanced Filters**: Filter by set, rarity, type, domains, energy, might, and power
- **Automatic Updates**: Database automatically syncs with `cards.json` on startup
- **Image Hover**: Hover over card names to see card images

## 🔄 Database Management

### Local Database Updater (`update_local_database.py`)
- **Purpose**: Updates SQLite database from local `cards.json` file
- **Usage**: Automatically runs on application startup
- **Process**: Clears existing database and imports fresh data from `cards.json`

### Piltover Archive Updater (`update_piltover_archive.py`)
- **Purpose**: Fetches fresh data from Piltover Archive API
- **Usage**: Manual updates when new cards are released
- **Process**: Downloads, reorganizes, and updates both `cards.json` and database

### Database Export (`export_database_to_json.py`)
- **Purpose**: Exports current database back to `cards.json`
- **Usage**: Backup/restore or sync database with JSON file
- **Process**: Reads all variants and creates formatted JSON output

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
