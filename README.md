# Riftbound TCG Collection Management

A professional desktop application for managing your Riftbound Trading Card Game collection. Built with Python and PyQt6 for a sleek, modern interface.

## Features

- **Collection Management**: Spreadsheet-style view of all cards with detailed information
- **Multi-Category Organization**: Organize cards into custom categories and collections
- **Card Information Tracking**: Set, condition, acquisition date, personal tags, and more
- **Collection Valuation**: Track collection value using Cardmarket API integration
- **Professional UI**: Modern, intuitive interface designed for ease of use
- **Future-Proof Architecture**: Built to easily accommodate new features and complexity

## Requirements

- Python 3.8+
- Windows 10/11 (primary target)
- Internet connection for Cardmarket API features

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/celeste-co/RBCollectionManagement.git
   cd RBCollectionManagement
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python src/main.py
```

## Project Structure

```
RBCollectionManagement/
├── src/                    # Source code
│   ├── main.py            # Application entry point
│   ├── ui/                # User interface components
│   ├── models/            # Data models and database
│   ├── services/          # Business logic and API integration
│   └── utils/             # Utility functions
├── data/                   # Card data and images
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Development

This application is built with:
- **PyQt6**: Modern UI framework for professional desktop applications
- **SQLite**: Local database for collection data
- **Cardmarket API**: Integration for card pricing and market data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and feature requests, please use the GitHub Issues page.
