# CourtFinder CLI 🏛️

Transform 300GB freelaw.org bulk court data into accessible, searchable court records.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the CLI:**
   ```bash
   python menu.py
   ```

3. **Try Quick Start:**
   - Select option `1` from the menu
   - This will set up sample data and demonstrate search capabilities

## Features

### 🚀 Quick Start
- **Purpose**: Get started immediately with sample data
- **What it does**: Sets up sample court data and demonstrates search
- **Perfect for**: First-time users, demos, testing

### 📥 Download Court Data
- **Purpose**: Download bulk data from CourtListener.com
- **Data types**: Courts, dockets, opinion clusters, opinions, citations, people
- **Features**: Automatic extraction, progress tracking
- **Requirements**: Internet connection

### 🔧 Parse Downloaded Data
- **Purpose**: Convert CSV files to searchable format
- **Features**: CSV validation, batch processing, indexing
- **Performance**: Handles large datasets efficiently

### 🔍 Search Court Records
- **Courts**: Search by name or jurisdiction
- **Cases**: Search by case name, filter by court
- **Opinions**: Full-text search across opinion content
- **Judges**: Search by name with fuzzy matching
- **Case Details**: Complete case hierarchy (docket → clusters → opinions)
- **Citation Network**: Explore citation relationships between opinions

### 📊 Statistics
- Storage usage by data type
- Record counts and indexes
- System performance metrics

## Architecture

```
CourtFinder CLI
├── menu.py              # Main CLI entry point
├── src/courtfinder/     # Core modules
│   ├── main.py         # CLI integration
│   ├── models.py       # Domain models
│   ├── storage.py      # File-based storage
│   ├── search.py       # Search engine
│   ├── api_client.py   # CourtListener API
│   └── csv_parser.py   # CSV parsing
├── data/               # Main data storage
├── test_data/          # Sample data for testing
└── requirements.txt    # Python dependencies
```

## Data Flow

1. **Download** → CSV files from CourtListener.com
2. **Parse** → Convert CSV to domain models
3. **Store** → JSON files with indexes
4. **Search** → Fast querying across all data

## Sample Data

The CLI includes sample court data for testing:
- Supreme Court of the United States
- US Court of Appeals for the 9th Circuit
- US District Court for Northern California

## Error Handling

- Graceful error recovery
- User-friendly error messages
- Progress indicators for long operations
- Keyboard interrupt support (Ctrl+C)

## Performance

- Compressed JSON storage (gzip)
- Multi-threaded operations
- Efficient indexing system
- Paginated results

## Dependencies

- **Rich**: Beautiful terminal interface
- **Questionary**: Interactive prompts
- **Requests**: HTTP client for API calls
- **Pathlib**: Modern path handling

## Getting Help

- Use option `6` in the menu for detailed help
- Check the source code for API documentation
- Report issues on GitHub

## Development

To modify or extend the CLI:

1. **Domain Models**: Edit `src/courtfinder/models.py`
2. **Search Logic**: Edit `src/courtfinder/search.py`
3. **Storage**: Edit `src/courtfinder/storage.py`
4. **UI**: Edit `menu.py`

## License

This project processes data from CourtListener.com under their terms of service.