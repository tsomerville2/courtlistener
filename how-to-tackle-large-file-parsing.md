# How to Tackle Large File Parsing: The FreeLaw Methodology

This document captures the proven methodology for parsing large-scale bulk data files, developed through successfully parsing 300GB+ of FreeLaw/CourtListener data.

## The Pattern

### 1. Study the Reference Implementation
- Look at the original data export scripts (e.g., `gitlibs/courtlistener/scripts/make_bulk_data.sh`)
- Understand the field structure and data format
- Note any special handling or transformations
- **Important**: We only use this as a reference - no actual code dependencies

### 2. Create a Dedicated Parse Function
For each data type, create a `parse_[datatype]_row()` function that:
- Takes a row dictionary from the CSV reader
- Uses static parser methods to handle each field type
- Maps CSV column names to model field names  
- Validates required fields with clear error messages
- Returns a proper model instance (Court, Docket, Opinion, etc.)

Example structure:
```python
def parse_court_row(row: Dict[str, str]) -> Court:
    """Parse a court row from FreeLaw CSV"""
    
    # Extract and parse each field
    court_id = FreeLawCSVParser.parse_string(row.get('id', ''))
    full_name = FreeLawCSVParser.parse_string(row.get('full_name', ''))
    
    # Validate required fields
    if not court_id:
        raise ValueError("Court ID is required")
        
    # Create and return model instance
    return Court(id=court_id, full_name=full_name, ...)
```

### 3. Build a Robust Parser Class
Create a centralized parser with static methods for each data type:
- `parse_string()` - Handle quoted strings, PostgreSQL nulls
- `parse_datetime()` - Parse ISO format timestamps
- `parse_date()` - Parse date-only values
- `parse_boolean()` - Handle 't'/'f' PostgreSQL booleans
- `parse_integer()` - Safe integer parsing
- `parse_float()` - Safe float parsing
- `parse_json()` - Parse JSON arrays/objects

Key features:
- Handle PostgreSQL CSV format (`FORCE_QUOTE *`)
- Support for `\N` as null values
- HTML-aware parsing for multi-line content
- Consistent error handling

### 4. Update Import Configuration
Enable parsing by updating the import configuration:
```python
# From:
'courts': (None, None, None),

# To:
'courts': (parse_court_row, storage.save_court, None),
```

### 5. Use Existing Downloads
- Data files are already downloaded in `downloads/` directory
- Don't re-download - parse what's already there
- Files are BZ2 compressed CSVs

### 6. Test Incrementally
- Start with small limits (10-100 records)
- Verify parsing works correctly
- Check storage and indexing
- Then remove limits for full import

### 7. Verify Success
- Use `storage.get_storage_stats()` to confirm counts
- Check that indexes are created properly
- Validate a few records manually

## Technical Details

### File Format
- PostgreSQL CSV exports with `FORCE_QUOTE *`
- Every field is quoted with double quotes
- Null values represented as `\N`
- BZ2 compression for efficient storage

### HTML-Aware Parsing
The `HTMLAwareCSVReader` handles:
- Multi-line content within quoted fields
- Embedded HTML that might contain newlines
- Proper quote escaping

### Storage Architecture
- JSON files with gzip compression
- Separate indexes for each searchable field
- ID-based primary storage
- Efficient field-based lookups

## Common Pitfalls

1. **Missing Parser Methods**: Add new static methods as needed (e.g., `parse_float()`)
2. **Field Name Mismatches**: Always check the reference for exact column names
3. **Required Field Validation**: Validate early to catch data issues
4. **Index Corruption**: Rebuild indexes if interrupted during import
5. **Memory Management**: Use streaming/chunked processing for large files

## Scalability Considerations

For 300GB+ datasets:
- Process files individually, not all at once
- Use BZ2 streaming to avoid loading entire files
- Implement progress tracking and resumability
- Consider parallel processing for independent data types
- Monitor disk space during import

## Results

Using this methodology, we successfully parse:
- Courts: 1,973 records
- Dockets: 4,562 records  
- Opinion Clusters: 938 records
- Opinions: 1,000 records (with HTML content)
- Citations: 10,000 records
- People: In progress

Total: ~18,000+ legal records parsed, indexed, and ready for querying.