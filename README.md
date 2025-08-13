# Riftbound TCG Collection Management

A comprehensive collection management application for the Riftbound Trading Card Game, featuring automated data collection from [Piltover Archive](https://piltoverarchive.com/cards).

## 🚀 Key Features

- **Automated Data Collection**: Fetches card data directly from [Piltover Archive](https://piltoverarchive.com/cards)
- **Modern Database**: Uses SQLite with a comprehensive card schema including variants, artists, and metadata
- **Smart Updates**: Automatically detects changes and updates only when necessary
- **Rich Search Interface**: Advanced filtering by set, rarity, type, domains, and more
- **Image Support**: Displays card images with hover tooltips
- **Collection Tracking**: Track owned cards, quantities, and conditions
- **Interactive Quiz**: Test your card knowledge with name-guessing quiz featuring blanked-out card images
- **Coordinate Tool**: External tool for setting up card name positions for optimal quiz experience

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
│   │   ├── quiz_widget.py            # Interactive card name quiz
│   │   └── sidebar.py                # Navigation sidebar
│   ├── main.py                       # Main application entry point
│   ├── update_local_database.py      # Local database updater (from cards.json)
│   ├── update_piltover_archive.py    # Piltover Archive updater (from API)
│   └── export_database_to_json.py    # Database export utility
├── card_coordinate_tool.py            # External tool for setting card name coordinates
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
- **Interactive Quiz**: 10-question card name guessing game with blanked-out images
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

## 🧠 Quiz Feature

The application includes an interactive quiz feature that tests your knowledge of Riftbound card names:

### How It Works
1. **Start Quiz**: Click the Quiz tab and start a 10-question quiz
2. **View Cards**: Card images are displayed with names blanked out using coordinate data
3. **Guess Names**: Type your guess for each card name
4. **Submit Answer**: Press **Enter** to submit your answer
5. **Next Question**: Press **Enter** again to go to the next question
6. **Get Feedback**: Immediate feedback shows if you're correct, with card details
7. **Review Results**: See your final score and review all questions

**Note**: Battlefield cards are automatically rotated 90° clockwise in the quiz for easier reading.

### Name Matching
- **Word-Based**: Must include all main words from the card name
- **Case Insensitive**: "flame spirit" matches "Flame Spirit"  
- **Comma Optional**: "Yasuo Remorseful" matches "Yasuo, Remorseful"
- **Order Flexible**: "Remorseful Yasuo" matches "Yasuo, Remorseful"
- **Partial Credit**: 80%+ word overlap accepted for close matches

### Setting Up Card Coordinates
To get the best quiz experience with properly blanked card names:

1. **Run Coordinate Tool**:
   ```bash
   python card_coordinate_tool.py
   ```

2. **Configure Card Types**:
   - **Classic Format**: Standard card layout
   - **Battlefield Format**: Vertical cards with rotated text

3. **Auto-Load Mode** (Recommended):
   - Click "Auto-Load Cards from Database" to start batch processing
   - Card format is automatically detected (Classic vs Battlefield)
   - Click and drag to draw rectangles over card name areas
   - Press **Enter** to save coordinates and automatically go to next card
   - Use arrow keys or navigation buttons to move between cards

4. **Manual Mode**:
   - Load individual card images using "Load Card Image"
   - Manually select card format (Classic/Battlefield)
   - Draw coordinates and save manually

5. **Keyboard Shortcuts**:
   - **Enter**: Save current coordinates and go to next card
   - **Escape**: Clear all drawn rectangles

6. **Export Data**: Coordinates are saved to `card_name_coordinates.json`

## 🔧 Development

### Adding New Features
- **UI Components**: Add to `src/ui/` directory
- **Database Operations**: Extend `PiltoverCardDatabase` class
- **Data Sources**: Extend `PiltoverArchiveAPIScraper` class
- **Quiz Extensions**: Modify `QuizWidget` for new question types

### Testing
```bash
# Test main application
python src/main.py

# Test coordinate tool
python card_coordinate_tool.py

# Test database updater
python src/update_local_database.py

# Test scraper directly
python src/scraping/piltover_scraper.py
```

## 📝 License

This project is open source and available under the MIT License.
