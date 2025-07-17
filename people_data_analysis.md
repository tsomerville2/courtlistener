# People Data Analysis and Implementation Plan

## Current Situation

### 1. File Status
- **Current file**: `downloads/people-2024-12-31.csv.bz2` (306 bytes)
- **Content**: XML error response (404 Not Found)
- **Error**: "The specified key does not exist" - `bulk-data/people-2024-12-31.csv.bz2`

### 2. CourtListener GitHub Analysis

**From `gitlibs/courtlistener/scripts/make_bulk_data.sh`:**

People data is exported as **multiple files**, not a single `people-2024-12-31.csv.bz2`:

```bash
# people_db_person (main person table)
people_db_person_fields='(
    id, date_created, date_modified, date_completed, fjc_id, slug, name_first,
    name_middle, name_last, name_suffix, date_dob, date_granularity_dob,
    date_dod, date_granularity_dod, dob_city, dob_state, dob_country,
    dod_city, dod_state, dod_country, gender, religion, ftm_total_received,
    ftm_eid, has_photo, is_alias_of_id
)'
people_db_person_csv_filename="people-db-people-$(date -I).csv"

# Additional people-related tables:
- people_db_school_csv_filename="people-db-schools-$(date -I).csv"
- people_db_position_csv_filename="people-db-positions-$(date -I).csv"
- people_db_retentionevent_csv_filename="people-db-retention-events-$(date -I).csv"
- people_db_education_csv_filename="people-db-educations-$(date -I).csv"
- politicalaffiliation_csv_filename="people-db-political-affiliations-$(date -I).csv"
- people_db_race_csv_filename="people_db_race-$(date -I).csv"
- people_db_person_race_csv_filename="people-db-races-$(date -I).csv"
```

**Correct file naming pattern**: `people-db-people-2024-12-31.csv.bz2` (not `people-2024-12-31.csv.bz2`)

### 3. Our Current Model

**From `src/courtfinder/models.py`:**

Our `Person` model matches the CourtListener schema well:
- ✅ All basic fields covered (id, names, dates, locations, gender, etc.)
- ✅ Proper field types and validation
- ✅ Methods for full name, deceased status, dict conversion
- ✅ Matches the actual database schema from CourtListener

## Root Cause Analysis

### The Problem
We tried to download `people-2024-12-31.csv.bz2` but CourtListener actually exports people data as:
- `people-db-people-2024-12-31.csv.bz2` (main person records)
- `people-db-schools-2024-12-31.csv.bz2` (schools)
- `people-db-positions-2024-12-31.csv.bz2` (judicial positions)
- `people-db-educations-2024-12-31.csv.bz2` (education records)
- etc.

### The Fix
We need to update our download script to use the correct file names.

## Implementation Plan

### Phase 1: Fix Download Script ✅
**Goal**: Download the correct people data files

**Action Items**:
1. Update `download_bulk_data.py` to download `people-db-people-2024-12-31.csv.bz2`
2. Optionally download related files (positions, schools, etc.)
3. Test file integrity

### Phase 2: Update Parser ✅
**Goal**: Parse the people data correctly

**Action Items**:
1. Update `parse_person_row()` in `import_ALL_freelaw_data_FIXED.py`
2. Map CSV fields to our Person model
3. Handle date parsing and optional fields
4. Test with sample data

### Phase 3: Integration ✅
**Goal**: Integrate people import into main workflow

**Action Items**:
1. Add people import to main import script
2. Update storage to handle people data
3. Test end-to-end import
4. Verify search functionality

### Phase 4: Advanced Features (Optional) 🔄
**Goal**: Import related people data

**Action Items**:
1. Create models for positions, schools, education
2. Import and link related data
3. Enhanced search by judge names, positions, etc.

## Expected Data Volume

Based on CourtListener being a judicial database:
- **People records**: ~100,000 - 500,000 (judges, lawyers, court personnel)
- **Positions**: ~200,000 - 1,000,000 (judicial appointments, career history)
- **Schools**: ~5,000 - 10,000 (law schools, universities)
- **Education**: ~200,000 - 1,000,000 (education records for people)

## Next Steps

### Immediate Actions:
1. ✅ **Fix download URL**: Change from `people-2024-12-31.csv.bz2` to `people-db-people-2024-12-31.csv.bz2`
2. ✅ **Test download**: Verify we can download the correct file
3. ✅ **Parse sample**: Read first 100 rows to verify format
4. ✅ **Update import script**: Add people import to main workflow

### Implementation Priority:
1. **High**: Main people records (names, dates, basic info)
2. **Medium**: Judicial positions (relates to court cases)
3. **Low**: Education, schools, political affiliations

## Code Changes Required

### 1. Update Download Script
```python
# Change this:
"people-2024-12-31.csv.bz2"
# To this:
"people-db-people-2024-12-31.csv.bz2"
```

### 2. Update Import Script
```python
# Add to imports configuration:
("people-db-people-2024-12-31.csv.bz2", "people", parse_person_row, storage.save_person, 10000)
```

### 3. Parser Function (already exists in models.py)
Our `parse_person_row()` function should work with minimal changes.

## Success Criteria

### Phase 1 Complete:
- ✅ Download `people-db-people-2024-12-31.csv.bz2` successfully
- ✅ File size > 1MB (actual data, not error)
- ✅ Can read and parse CSV header

### Phase 2 Complete:
- ✅ Parse 100 sample records successfully
- ✅ All required fields map correctly
- ✅ Date parsing works for birth/death dates
- ✅ Optional fields handled properly

### Phase 3 Complete:
- ✅ Import 10,000+ people records
- ✅ Storage stats show people count > 0
- ✅ Can search by judge names
- ✅ People data appears in search results

This plan addresses the root cause (wrong file name) and provides a clear path to get people data working.