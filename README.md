# CourtFinder CLI

Transform 300GB freelaw.org bulk court data into accessible, searchable court records through a simple command-line interface.

## Quick Start

```bash
python menu.py
```

That's it! CourtFinder CLI will start automatically with a beautiful interface and test data ready to explore.

## What This Does

CourtFinder CLI solves the critical challenge of accessing and analyzing the massive freelaw.org bulk court data repository. While the complete 300GB dataset contains invaluable legal information, its size and format complexity make it practically unusable for most researchers and developers. Our CLI tool transforms overwhelming bulk data into accessible, searchable court records in just a few clicks.

## Key Features

- **🚀 Quick Start**: Get searching immediately with one command
- **📥 Smart Downloads**: Intelligent sampling and size limiting for manageable data sets
- **🔧 Robust Parsing**: Handles complex CSV formats and data validation
- **🔍 Advanced Search**: Find courts, cases, opinions, and judges with powerful search tools
- **📊 Rich Statistics**: Monitor data storage and processing performance
- **🎨 Beautiful Interface**: Professional CLI with colors, tables, and progress indicators

## Requirements

- Python 3.7+
- Internet connection (for downloading court data)

Dependencies are automatically installed when you run the application.

## Usage Examples

### Search for Supreme Court Records
```bash
python menu.py
# Select: 1. Quick Start
# Search: "Supreme Court"
```

### Download Fresh Court Data
```bash
python menu.py
# Select: 2. Download Court Data
# Choose data types and size limits
```

### Parse Your Own Data Files
```bash
python menu.py
# Select: 3. Parse Downloaded Data
# Select CSV files to process
```

## Data Sources

CourtFinder CLI uses the official **CourtListener.com** API from the Free Law Project, providing access to:
- Federal and state court records
- Judicial opinions and decisions
- Case metadata and citations
- Judge information and biographies
- Legal precedent networks

## Screenshots

See the `screenshots/` directory for examples of the CLI interface in action, including:
- Main menu and Quick Start workflow
- Search functionality and results
- Data download and parsing processes
- Advanced search capabilities
- Error handling and help system

## Technical Details

For developers and advanced users:
- **API Integration**: Real CourtListener.com API with authentication
- **Data Storage**: Efficient JSON-based storage with compression
- **Search Engine**: Full-text search with multiple operators
- **CSV Processing**: Handles complex bulk data formats
- **BDD Testing**: Comprehensive test suite with behave

## Support

- **Documentation**: Complete API guide in `docs/API-and-Data-guide.md`
- **Help System**: Built-in help available in the CLI (option 6)
- **BDD Tests**: Run `behave` to verify functionality
- **GitHub Issues**: Report problems or request features

## License

This project is designed to make legal data more accessible to researchers, journalists, and developers working to improve the legal system.

---

*Making the legal ecosystem more equitable and accessible, one search at a time.*