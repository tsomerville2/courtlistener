# State Flow - CourtFinder CLI

## Business State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Downloading: download command
    Downloading --> Downloaded: download complete
    Downloaded --> Parsing: parse command
    Parsing --> Parsed: parse complete
    Parsed --> Querying: lookup command
    Querying --> Results: query complete
    Results --> [*]
    Downloaded --> Downloading: download more
    Parsed --> Parsing: parse more
    Results --> Querying: new query
```

## State Definitions
- **Idle**: CLI ready to accept commands
- **Downloading**: Fetching bulk data samples from freelaw.org
- **Downloaded**: Data files available locally for processing
- **Parsing**: Extracting structured records from bulk data
- **Parsed**: Records available in searchable format
- **Querying**: Processing search/lookup requests
- **Results**: Query results ready for display

## Transitions
- **download command**: User requests data download with size limits
- **download complete**: Sample data successfully downloaded and validated
- **parse command**: User initiates parsing of downloaded data
- **parse complete**: All records extracted and columns 12-18 handled
- **lookup command**: User performs search query
- **query complete**: Search results formatted for display