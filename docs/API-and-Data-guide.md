# CourtListener API and Bulk Data Guide

## Overview

This guide documents the **actual** Free Law Project CourtListener API and bulk data system based on real documentation and source code analysis. CourtListener provides comprehensive legal data through both REST APIs and bulk CSV downloads.

## Organization

**Free Law Project** (501(c)(3) nonprofit) maintains:
- **CourtListener.com** - Search interface and API
- **GitHub**: https://github.com/freelawproject/courtlistener
- **Documentation**: https://www.courtlistener.com/help/api/

## API Access

### Authentication & Rate Limits
- **Authenticated users**: 5,000 queries per hour
- **Unauthenticated users**: 100 queries per day
- **Base URL**: https://www.courtlistener.com/api/rest/v4/
- **Authentication**: Token-based (register for account)

### Key API Endpoints

```
GET /api/rest/v4/courts/           # Court metadata
GET /api/rest/v4/dockets/          # Case/docket information
GET /api/rest/v4/clusters/         # Opinion clusters
GET /api/rest/v4/opinions/         # Individual opinions
GET /api/rest/v4/people/           # Judges and attorneys
GET /api/rest/v4/citations/        # Citation relationships
```

### API Query Examples

```bash
# Get Supreme Court opinions
curl "https://www.courtlistener.com/api/rest/v4/opinions/?cluster__docket__court=scotus"

# Get specific docket
curl "https://www.courtlistener.com/api/rest/v4/dockets/12345/"

# Get field definitions
curl -X OPTIONS "https://www.courtlistener.com/api/rest/v4/opinions/"
```

## Bulk Data System

### Download Information
- **Location**: https://www.courtlistener.com/help/api/bulk-data/
- **Update Schedule**: Monthly (last day of month, 3AM PST)
- **Format**: CSV with UTF-8 encoding, header row included
- **Generation**: PostgreSQL COPY TO command

### Recent Improvements (January 2025)
- Fixed CSV parsing issues with double-quote handling
- Added ESCAPE option for embedded quotes
- Changed from backticks to double quotes for better parsing
- Added FORCE_QUOTE * option to distinguish null vs blank values

### Available Bulk Data Files

#### 1. Courts CSV
```
id, full_name, short_name, jurisdiction, position, 
citation_string, start_date, end_date, notes
```

#### 2. Dockets CSV
```
id, date_created, date_modified, source, court_id, 
appeal_from_id, case_name, case_name_short, 
case_name_full, slug, docket_number, date_filed, 
date_filed_is_approximate, date_terminated, 
date_terminated_is_approximate, federal_dn_case_type, 
federal_dn_office_code, federal_defendant_number
```

#### 3. Opinion Clusters CSV
```
id, date_created, date_modified, judges, date_filed, 
date_filed_is_approximate, slug, case_name, 
case_name_short, case_name_full, scdb_id, 
scdb_decision_direction, scdb_votes_majority, 
scdb_votes_minority, source, procedural_history, 
attorneys, nature_of_suit, posture, syllabus, 
headnotes, summary, disposition, history, 
other_dates, cross_reference, correction, 
citation_count, precedential_status, 
date_blocked, blocked, docket_id, sub_opinions
```

#### 4. Opinions CSV
```
id, date_created, date_modified, type, sha1, 
page_count, download_url, local_path, plain_text, 
html, html_lawbox, html_columbia, html_anon_2020, 
xml_harvard, html_with_citations, extracted_by_ocr, 
author_id, per_curiam, joined_by, cluster_id
```

#### 5. Citation Map CSV
```
cited_opinion_id, citing_opinion_id, depth, 
quoted, parenthetical_id, parenthetical_text
```

#### 6. People CSV (Judges/Attorneys)
```
id, date_created, date_modified, name_first, 
name_middle, name_last, name_suffix, date_dob, 
date_granularity_dob, date_dod, date_granularity_dod, 
dob_city, dob_state, dod_city, dod_state, 
gender, religion, ftm_total_received, ftm_eid, 
has_photo, is_alias_of
```

## Data Relationships

### Key Relationships
1. **Dockets** contain multiple **Opinion Clusters**
2. **Opinion Clusters** contain multiple **Opinions**
3. **Opinions** cite other **Opinions** (not clusters)
4. **Courts** are referenced by **Dockets**
5. **People** (judges) are referenced by **Opinion Clusters**

### Data Flow
```
Court → Docket → Opinion Cluster → Opinion
                      ↓
                   Citations → Other Opinions
```

## CSV Parsing Considerations

### Known Issues (Recently Fixed)
1. **Quote Handling**: Now uses double quotes consistently
2. **Null vs Blank**: Nulls appear as `,,` while blanks appear as `,"",`
3. **Embedded Quotes**: Handled with ESCAPE option
4. **Column Alignment**: Some CSV files may not match API 1-to-1

### Import Script Example
```bash
# Download bulk data
wget https://www.courtlistener.com/api/bulk-data/dockets-2024-01-31.csv.bz2

# Extract
bunzip2 dockets-2024-01-31.csv.bz2

# Import to PostgreSQL (example)
psql -c "COPY dockets FROM 'dockets-2024-01-31.csv' WITH (FORMAT CSV, HEADER true, ESCAPE '\"');"
```

## Column Structure Analysis

### Text Format Columns in Opinions
- `plain_text`: Clean text version
- `html`: HTML formatted version
- `html_lawbox`: LawBox-specific HTML
- `html_columbia`: Columbia-specific HTML
- `html_anon_2020`: Anonymized 2020 HTML
- `xml_harvard`: Harvard XML format
- `html_with_citations`: HTML with citation links

### Date Handling
- Most date fields have corresponding `_is_approximate` boolean fields
- `date_filed` vs `date_created` distinction is important
- Cluster date_filed = decision date, Docket date_filed = case filing date

### ID Relationships
- All IDs are integers
- Foreign keys follow Django conventions (e.g., `docket_id`, `cluster_id`)
- Citation relationships use `cited_opinion_id` and `citing_opinion_id`

## Data Quality Notes

### Recent Enhancements
- Manual correction of 10,000+ items from Public.Resource.Org
- Fixed 1+ million items from Harvard's Caselaw Access Project
- Added exact dates for older Supreme Court cases

### Data Coverage
- 32,336 financial disclosure documents
- 1,901,720 investment records
- Largest oral arguments database globally
- Comprehensive federal and state court coverage

## Database Replication

For high-volume users, CourtListener offers PostgreSQL replication:
- Real-time table-based logical replica
- Direct database access for complex queries
- Pricing based on organizational needs

## Development Resources

### Source Code
- **Main repository**: https://github.com/freelawproject/courtlistener
- **Models**: `/cl/search/models.py` (main data models)
- **People Models**: `/cl/people_db/models.py` (judges/attorneys)
- **API Tests**: `/cl/api/tests.py` (usage examples)

### Related Projects
- **Juriscraper**: Python scraping library
- **Eyecite**: Citation finding tool
- **Reporters Database**: Legal reporter information

## Technical Implementation Notes

### For CourtFinder CLI Implementation
1. **No "columns 12-18" issue found**: This appears to be a misunderstanding - the bulk data uses proper CSV formatting
2. **Real parsing challenges**: Quote handling, null/blank distinction, large file sizes
3. **Recommended approach**: Use PostgreSQL COPY commands for import, not custom CSV parsing
4. **Sample data**: Request from Free Law Project for development purposes

### Best Practices
1. Always check for CSV format updates in their documentation
2. Use the provided import scripts as templates
3. Handle both null and blank values appropriately
4. Consider the data relationships when designing queries
5. Respect rate limits when using the API for metadata

## Contact Information

- **Website**: https://www.courtlistener.com/
- **GitHub Issues**: https://github.com/freelawproject/courtlistener/issues
- **API Documentation**: https://www.courtlistener.com/help/api/
- **Bulk Data**: https://www.courtlistener.com/help/api/bulk-data/

This guide reflects the actual CourtListener system as of January 2025, based on official documentation and source code analysis.