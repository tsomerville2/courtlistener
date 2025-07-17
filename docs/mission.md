# Mission - CourtFinder CLI

## Vision
CourtFinder CLI solves the critical challenge of accessing and analyzing the massive freelaw.org bulk court data repository. While the complete 300GB dataset contains invaluable legal information, its size and format complexity make it practically unusable for most researchers and developers. Our CLI tool bridges this gap by providing intelligent sampling, robust parsing (especially for the problematic columns 12-18), and intuitive querying capabilities. The tool transforms overwhelming bulk data into accessible, searchable court records through a simple command-line interface.

## Success Criteria
1. Successfully download manageable samples (< 1GB) from the 300GB freelaw.org dataset
2. Parse downloaded data including previously problematic columns 12-18 without errors
3. Provide fast, accurate lookup and search functionality across processed court records

## In Scope
- Download command with size limiting and sample selection
- Unzip functionality for compressed bulk data files
- Parse command with special handling for columns 12-18
- Interactive CLI with questionary/rich for user-friendly querying
- Search and lookup commands for processed court records

## Out of Scope
- Processing the entire 300GB dataset in one operation
- Real-time data updates from freelaw.org
- Web interface or API endpoints
- Data visualization or reporting features
- Multi-user or concurrent access support

## App Name Rationale
**Chosen Name**: CourtFinder CLI
**Reasoning**: The name clearly communicates the tool's purpose (finding court data) and interface (CLI), while being memorable and descriptive. It emphasizes the discovery aspect of searching through court records rather than the technical complexity of bulk data processing.