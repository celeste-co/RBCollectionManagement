# Riftbound TCG Collection Management

A desktop application for managing your Riftbound Trading Card Game collection. Built with Python and PyQt6 to provide a clean, professional interface for organizing and tracking your cards.

## What it does

- **Card Library**: Browse your entire card collection in a spreadsheet-style view
- **Smart Filtering**: Find specific cards using filters for name, set, domains, rarity, type, and more
- **Range Sliders**: Filter cards by might, energy, and power costs using intuitive dual-handle sliders
- **Collection Tracking**: Keep track of which cards you own, their condition, and when you acquired them
- **Card Previews**: Hover over card names to see card images
- **Flexible Organization**: Create custom categories and tags for your collection

## Getting started

**Requirements:**
- Python 3.8 or newer
- Windows 10/11 (primary platform)
- Internet connection for future Cardmarket API features

**Installation:**
1. Clone the repository:
   ```bash
   git clone https://github.com/celeste-co/RBCollectionManagement.git
   cd RBCollectionManagement
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the app

Start the application with:
```bash
python src/main.py
```

The first time you run it, you'll be prompted to import your card data from JSON files. The app will automatically populate the library with all available cards.

## How it works

The application uses a hybrid data storage approach:
- **JSON files**: Store the static card catalog (names, stats, images)
- **SQLite database**: Tracks your personal collection data and enables fast searching

The interface is split into two main sections:
- **Filters panel**: Configure search criteria and filter options
- **Library table**: View filtered results with card details

## Project structure

```
RBCollectionManagement/
├── src/                    # Main application code
│   ├── main.py            # App entry point and main window
│   ├── ui/                # Interface components
│   ├── models/            # Data models and database logic
│   └── utils/             # Helper functions and configuration
├── card_data/             # JSON card catalog files
├── card_img/              # Card image files
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Built with

- **PyQt6**: Modern UI framework for desktop applications
- **SQLite**: Local database for collection data
- **Custom range sliders**: Dual-handle sliders with snapping behavior for precise filtering

## Contributing

Feel free to contribute improvements:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Issues and feedback

Found a bug or have a feature request? Use the GitHub Issues page to let us know.
