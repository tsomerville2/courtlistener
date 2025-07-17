# Domain Model - CourtFinder CLI

## Bounded Context
Legal Data Processing - A CLI tool for downloading, parsing, and querying freelaw.org bulk court data

## Aggregates

### BulkDataSet
- **Root Entity**: BulkDataSet
- **Value Objects**: 
  - DataFile (path, size, status)
  - DataRange (start_column, end_column)
  - QueryParams (field, value, operator)
- **Business Rules**: 
  - Sample size must be manageable (< 1GB portions)
  - Columns 12-18 require special parsing logic
  - Downloaded data must be validated before processing

### CourtRecord
- **Root Entity**: CourtRecord
- **Value Objects**:
  - CourtIdentifier (jurisdiction, court_name)
  - CaseMetadata (case_number, filing_date, parties)
- **Business Rules**:
  - Each record must have valid court identifier
  - Column data must map to known fields

## Domain Events
- DataDownloadRequested
- DataParsingCompleted
- QueryExecuted
- DataValidationFailed

## Ubiquitous Language
- **Bulk Data**: The complete 300GB dataset from freelaw.org
- **Sample**: A manageable subset downloaded for processing
- **Columns 12-18**: The problematic data columns requiring special handling
- **Parse**: Extract structured data from bulk format
- **Query**: Search through processed court records
- **CLI**: Command-line interface for user interaction