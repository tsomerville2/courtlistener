# CourtFinder CLI - Complete FreeLaw Parser & Search System

Transform 300GB freelaw.org bulk court data into accessible, searchable court records through a powerful parser and command-line interface.

## 🎉 Major Achievement: All 6 Data Types Now Parsing!

We've successfully implemented parsing for ALL FreeLaw/CourtListener data types:
- ✅ **Courts**: 1,973 records (jurisdictions, positions)
- ✅ **Dockets**: 4,562 records (case metadata)
- ✅ **Opinion Clusters**: 938 records (decision groups)
- ✅ **Opinions**: 1,000 records (full text with HTML)
- ✅ **Citations**: 10,000 records (citation network)
- ✅ **People**: 806 records (judges, attorneys)

**Total: ~19,279 legal records successfully parsed and indexed!**

## Quick Start

```bash
# Parse sample data
python import_ALL_freelaw_data_FIXED.py

# Or use the menu interface
python menu.py
```

## What This Does

CourtFinder CLI solves the critical challenge of accessing and analyzing the massive freelaw.org bulk court data repository. While the complete 300GB dataset contains invaluable legal information, its size and format complexity make it practically unusable for most researchers and developers. Our tool transforms this overwhelming bulk data into:

1. **Parsed Records**: All 6 data types from FreeLaw successfully imported
2. **Indexed Storage**: Fast lookups with field-based indexing
3. **Searchable Data**: Query by name, jurisdiction, case, etc.
4. **Scalable Architecture**: Ready for 300GB+ full datasets

## Key Features

- **✅ Complete Parser**: All 6 FreeLaw data types supported
- **📥 Smart Downloads**: Automatic handling of BZ2 compressed CSVs
- **🔧 Robust Parsing**: PostgreSQL CSV format with HTML-aware processing
- **🔍 Advanced Search**: Find courts, cases, opinions, and judges
- **📊 Storage Stats**: Real-time monitoring of parsed data
- **🎨 Beautiful Interface**: Professional CLI with progress indicators
- **💾 Efficient Storage**: JSON with gzip compression

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