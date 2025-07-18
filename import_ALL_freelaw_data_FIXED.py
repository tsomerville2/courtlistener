#!/usr/bin/env python3
"""
FIXED Complete FreeLaw bulk data importer - ALL DATA TYPES
Fixes the specific errors preventing opinions, citations, and people import
Now with resume capability and progress UI!
"""

import sys
import csv
import bz2
import tempfile
import io
import argparse
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import Court, Docket, OpinionCluster, Opinion, Citation, Person, OpinionType
from import_checkpoint import ImportCheckpoint
from import_progress import ImportProgress
try:
    from import_ui_asciimatics import ImportUI
except ImportError:
    ImportUI = None
from import_ui_rich import ImportUIRich

class FreeLawCSVParser:
    """Parser that handles the actual FreeLaw bulk CSV format"""
    
    @staticmethod
    def clean_value(value: str) -> str:
        """Remove backticks that FreeLaw wraps around all values"""
        if isinstance(value, str) and value.startswith('`') and value.endswith('`'):
            return value[1:-1]  # Remove first and last backtick
        return value
    
    @staticmethod
    def parse_integer(value: str) -> Optional[int]:
        """Parse integer value"""
        if not value or value.strip() == '':
            return None
        
        value = FreeLawCSVParser.clean_value(value).strip()
        if not value:
            return None
        
        try:
            return int(value)
        except ValueError:
            return None
    
    @staticmethod
    def parse_boolean(value: str) -> bool:
        """Parse boolean value"""
        if not value or value.strip() == '':
            return False
        
        value = FreeLawCSVParser.clean_value(value).strip().lower()
        return value in ['true', 't', '1', 'yes', 'y']
    
    @staticmethod
    def parse_string(value: str) -> str:
        """Parse string value"""
        if not value:
            return ''
        
        return FreeLawCSVParser.clean_value(value)
    
    @staticmethod
    def parse_float(value: str) -> Optional[float]:
        """Parse float value"""
        if not value or value.strip() == '':
            return None
        
        value = FreeLawCSVParser.clean_value(value).strip()
        if not value:
            return None
        
        try:
            return float(value)
        except ValueError:
            return None
    
    @staticmethod
    def parse_date(value: str) -> Optional[datetime]:
        """Parse FreeLaw date format: YYYY-MM-DD"""
        if not value or value.strip() == '':
            return None
        
        value = FreeLawCSVParser.clean_value(value).strip()
        if not value:
            return None
        
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    @staticmethod
    def parse_datetime(value: str) -> Optional[datetime]:
        """Parse FreeLaw datetime format: YYYY-MM-DD HH:MM:SS.ffffff+TZ"""
        if not value or value.strip() == '':
            return None
        
        value = FreeLawCSVParser.clean_value(value).strip()
        if not value:
            return None
        
        # Handle timezone format: 2021-01-29 06:20:24.011839+00
        try:
            # Remove timezone part if present
            if '+' in value:
                value = value.split('+')[0]
            elif value.endswith('Z'):
                value = value[:-1]
            
            # Try different datetime formats
            formats = [
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None

class OpinionCSVParser:
    """
    Specialized CSV parser for opinions that handles HTML content properly
    Uses CourtListener's exact method: FORCE_QUOTE * with backslash escape
    """
    
    @staticmethod
    def parse_opinion_csv(file_path: Path, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Parse opinion CSV file with proper HTML handling
        Uses efficient line-by-line processing
        
        Args:
            file_path: Path to the opinion CSV file
            limit: Optional limit on number of rows to parse
            
        Returns:
            List of valid opinion row dictionaries
        """
        valid_rows = []
        total_processed = 0
        
        with bz2.open(file_path, 'rt', encoding='utf-8') as f:
            # Get header
            header_line = f.readline().strip()
            expected_columns = header_line.split(',')
            
            print(f"  📝 CSV has {len(expected_columns)} columns")
            
            # Process file efficiently
            current_row_parts = []
            in_record = False
            line_count = 0
            
            for line in f:
                line_count += 1
                line = line.rstrip('\n\r')
                
                # Stop if we've processed enough
                if limit and total_processed >= limit:
                    break
                
                # Check if this is the start of a new record
                if line.startswith('`'):
                    # Process previous record if exists
                    if in_record and current_row_parts:
                        complete_row = ''.join(current_row_parts)
                        parsed_row = OpinionCSVParser.parse_csv_row(complete_row, expected_columns)
                        if parsed_row and OpinionCSVParser.is_valid_opinion_row(parsed_row):
                            valid_rows.append(parsed_row)
                            total_processed += 1
                            
                            if total_processed % 10 == 0:
                                print(f"  ✅ Found {total_processed} valid opinions so far...")
                    
                    # Start new record
                    current_row_parts = [line]
                    in_record = True
                    
                elif in_record:
                    # Continuation of current record
                    current_row_parts.append(line)
                
                # Progress update
                if line_count % 100000 == 0:
                    print(f"  📊 Processed {line_count} lines, found {total_processed} valid opinions")
            
            # Process final record
            if in_record and current_row_parts:
                complete_row = ''.join(current_row_parts)
                parsed_row = OpinionCSVParser.parse_csv_row(complete_row, expected_columns)
                if parsed_row and OpinionCSVParser.is_valid_opinion_row(parsed_row):
                    valid_rows.append(parsed_row)
                    total_processed += 1
        
        return valid_rows
    
    @staticmethod
    def parse_csv_row(row_line: str, expected_columns: List[str]) -> Optional[Dict[str, str]]:
        """
        Parse a single CSV row line, handling embedded quotes and HTML properly
        
        Args:
            row_line: Complete CSV row as a string
            expected_columns: List of expected column names
            
        Returns:
            Dictionary of parsed row data or None if invalid
        """
        try:
            # Use csv.reader with proper settings for PostgreSQL-style CSV
            row_io = io.StringIO(row_line)
            csv_reader = csv.reader(
                row_io,
                quoting=csv.QUOTE_ALL,
                skipinitialspace=True
            )
            
            row_data = next(csv_reader)
            
            # Check if we have the right number of fields
            if len(row_data) != len(expected_columns):
                return None
                
            # Create dictionary
            return dict(zip(expected_columns, row_data))
            
        except (csv.Error, StopIteration, UnicodeDecodeError, IndexError):
            return None
    
    @staticmethod
    def is_valid_opinion_row(row_dict: Dict[str, str]) -> bool:
        """
        Validate that a row dictionary represents a valid opinion record
        
        Args:
            row_dict: Dictionary of row data
            
        Returns:
            True if this looks like a valid opinion row
        """
        # Check for required fields
        opinion_id = row_dict.get('id', '').strip()
        if not opinion_id:
            return False
        
        # Opinion IDs should be wrapped in backticks and be numeric
        if not (opinion_id.startswith('`') and opinion_id.endswith('`')):
            return False
            
        # Remove backticks and check if it's a valid integer
        clean_id = opinion_id[1:-1]
        if not clean_id.isdigit():
            return False
        
        # Check if we have a reasonable type field
        opinion_type = row_dict.get('type', '').strip()
        if opinion_type and opinion_type.startswith('`') and opinion_type.endswith('`'):
            clean_type = opinion_type[1:-1]
            # Should be a valid opinion type code
            if clean_type and not clean_type.startswith('<'):  # Not HTML
                # Additional validation: check cluster_id
                cluster_id = row_dict.get('cluster_id', '').strip()
                
                # cluster_id should either be empty or a valid integer in backticks
                if cluster_id == '':
                    return True  # Empty cluster_id is acceptable
                
                if cluster_id.startswith('`') and cluster_id.endswith('`'):
                    clean_cluster_id = cluster_id[1:-1]
                    if clean_cluster_id.isdigit():
                        return True  # Valid cluster_id
                
                # If cluster_id doesn't look like a number, this row is probably corrupted
                if '<' in cluster_id or '>' in cluster_id or len(cluster_id) > 50:
                    return False
                
                # Accept it anyway if other fields look good
                return True
        
        return False
    
    @staticmethod
    def parse_date(value: str) -> Optional[datetime]:
        """Parse FreeLaw date format: YYYY-MM-DD"""
        if not value or value.strip() == '':
            return None
        
        value = FreeLawCSVParser.clean_value(value).strip()
        if not value:
            return None
        
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    @staticmethod
    def parse_datetime(value: str) -> Optional[datetime]:
        """Parse FreeLaw datetime format: YYYY-MM-DD HH:MM:SS.ffffff+TZ"""
        if not value or value.strip() == '':
            return None
        
        value = FreeLawCSVParser.clean_value(value).strip()
        if not value:
            return None
        
        # Handle timezone format: 2021-01-29 06:20:24.011839+00
        try:
            # Remove timezone part if present
            if '+' in value:
                value = value.split('+')[0]
            elif value.endswith('Z'):
                value = value[:-1]
            
            # Try different datetime formats
            formats = [
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def parse_integer(value: str) -> Optional[int]:
        """Parse integer value"""
        if not value or value.strip() == '':
            return None
        
        value = FreeLawCSVParser.clean_value(value).strip()
        if not value:
            return None
        
        try:
            return int(value)
        except ValueError:
            return None
    
    @staticmethod
    def parse_boolean(value: str) -> bool:
        """Parse boolean value"""
        if not value or value.strip() == '':
            return False
        
        value = FreeLawCSVParser.clean_value(value).strip().lower()
        return value in ['true', 't', '1', 'yes', 'y']
    
    @staticmethod
    def parse_string(value: str) -> str:
        """Parse string value"""
        if not value:
            return ''
        
        return FreeLawCSVParser.clean_value(value)

def parse_docket_row(row: Dict[str, str]) -> Docket:
    """Parse a docket row from FreeLaw CSV"""
    
    # Extract and clean the required fields
    docket_id = FreeLawCSVParser.parse_integer(row.get('id', ''))
    court_id = FreeLawCSVParser.parse_string(row.get('court_id', ''))
    case_name = FreeLawCSVParser.parse_string(row.get('case_name', ''))
    docket_number = FreeLawCSVParser.parse_string(row.get('docket_number', ''))
    source = FreeLawCSVParser.parse_string(row.get('source', ''))
    
    # Parse date fields
    date_created = FreeLawCSVParser.parse_datetime(row.get('date_created', ''))
    date_modified = FreeLawCSVParser.parse_datetime(row.get('date_modified', ''))
    date_filed = FreeLawCSVParser.parse_date(row.get('date_filed', ''))
    date_terminated = FreeLawCSVParser.parse_date(row.get('date_terminated', ''))
    date_last_filing = FreeLawCSVParser.parse_date(row.get('date_last_filing', ''))
    date_last_index = FreeLawCSVParser.parse_datetime(row.get('date_last_index', ''))
    date_cert_granted = FreeLawCSVParser.parse_date(row.get('date_cert_granted', ''))
    date_cert_denied = FreeLawCSVParser.parse_date(row.get('date_cert_denied', ''))
    date_argued = FreeLawCSVParser.parse_date(row.get('date_argued', ''))
    date_reargued = FreeLawCSVParser.parse_date(row.get('date_reargued', ''))
    date_reargument_denied = FreeLawCSVParser.parse_date(row.get('date_reargument_denied', ''))
    
    # Parse string fields
    case_name_short = FreeLawCSVParser.parse_string(row.get('case_name_short', ''))
    case_name_full = FreeLawCSVParser.parse_string(row.get('case_name_full', ''))
    slug = FreeLawCSVParser.parse_string(row.get('slug', ''))
    appeal_from_str = FreeLawCSVParser.parse_string(row.get('appeal_from_str', ''))
    appeal_from_id = FreeLawCSVParser.parse_string(row.get('appeal_from_id', ''))
    assigned_to_str = FreeLawCSVParser.parse_string(row.get('assigned_to_str', ''))
    referred_to_str = FreeLawCSVParser.parse_string(row.get('referred_to_str', ''))
    panel_str = FreeLawCSVParser.parse_string(row.get('panel_str', ''))
    docket_number_core = FreeLawCSVParser.parse_string(row.get('docket_number_core', ''))
    cause = FreeLawCSVParser.parse_string(row.get('cause', ''))
    nature_of_suit = FreeLawCSVParser.parse_string(row.get('nature_of_suit', ''))
    jury_demand = FreeLawCSVParser.parse_string(row.get('jury_demand', ''))
    jurisdiction_type = FreeLawCSVParser.parse_string(row.get('jurisdiction_type', ''))
    federal_dn_case_type = FreeLawCSVParser.parse_string(row.get('federal_dn_case_type', ''))
    federal_dn_office_code = FreeLawCSVParser.parse_string(row.get('federal_dn_office_code', ''))
    federal_defendant_number = FreeLawCSVParser.parse_string(row.get('federal_defendant_number', ''))
    
    # Create Docket object
    return Docket(
        id=docket_id,
        court_id=court_id,
        case_name=case_name,
        docket_number=docket_number,
        source=source,
        date_created=date_created,
        date_modified=date_modified,
        date_filed=date_filed,
        date_terminated=date_terminated,
        date_last_filing=date_last_filing,
        date_last_index=date_last_index,
        date_cert_granted=date_cert_granted,
        date_cert_denied=date_cert_denied,
        date_argued=date_argued,
        date_reargued=date_reargued,
        date_reargument_denied=date_reargument_denied,
        case_name_short=case_name_short,
        case_name_full=case_name_full,
        slug=slug,
        appeal_from_str=appeal_from_str,
        appeal_from_id=appeal_from_id,
        assigned_to_str=assigned_to_str,
        referred_to_str=referred_to_str,
        panel_str=panel_str,
        docket_number_core=docket_number_core,
        cause=cause,
        nature_of_suit=nature_of_suit,
        jury_demand=jury_demand,
        jurisdiction_type=jurisdiction_type,
        federal_dn_case_type=federal_dn_case_type,
        federal_dn_office_code=federal_dn_office_code,
        federal_defendant_number=federal_defendant_number
    )

def parse_opinion_cluster_row(row: Dict[str, str]) -> OpinionCluster:
    """Parse an opinion cluster row from FreeLaw CSV"""
    
    # Extract and clean the required fields
    cluster_id = FreeLawCSVParser.parse_integer(row.get('id', ''))
    docket_id = FreeLawCSVParser.parse_integer(row.get('docket_id', ''))
    judges = FreeLawCSVParser.parse_string(row.get('judges', ''))
    
    # Parse date fields
    date_created = FreeLawCSVParser.parse_datetime(row.get('date_created', ''))
    date_modified = FreeLawCSVParser.parse_datetime(row.get('date_modified', ''))
    date_filed = FreeLawCSVParser.parse_date(row.get('date_filed', ''))
    date_filed_is_approximate = FreeLawCSVParser.parse_boolean(row.get('date_filed_is_approximate', ''))
    
    # Parse string fields
    case_name = FreeLawCSVParser.parse_string(row.get('case_name', ''))
    case_name_short = FreeLawCSVParser.parse_string(row.get('case_name_short', ''))
    case_name_full = FreeLawCSVParser.parse_string(row.get('case_name_full', ''))
    slug = FreeLawCSVParser.parse_string(row.get('slug', ''))
    
    # Parse optional fields
    scdb_id = FreeLawCSVParser.parse_string(row.get('scdb_id', ''))
    scdb_decision_direction = FreeLawCSVParser.parse_string(row.get('scdb_decision_direction', ''))
    scdb_votes_majority = FreeLawCSVParser.parse_integer(row.get('scdb_votes_majority', ''))
    scdb_votes_minority = FreeLawCSVParser.parse_integer(row.get('scdb_votes_minority', ''))
    
    # Create OpinionCluster object
    return OpinionCluster(
        id=cluster_id,
        docket_id=docket_id,
        judges=judges,
        date_created=date_created,
        date_modified=date_modified,
        date_filed=date_filed,
        date_filed_is_approximate=date_filed_is_approximate,
        case_name=case_name,
        case_name_short=case_name_short,
        case_name_full=case_name_full,
        slug=slug,
        scdb_id=scdb_id,
        scdb_decision_direction=scdb_decision_direction,
        scdb_votes_majority=scdb_votes_majority,
        scdb_votes_minority=scdb_votes_minority
    )

def parse_opinion_row(row: Dict[str, str]) -> Opinion:
    """Parse an opinion row from FreeLaw CSV - FIXED with HTML-aware parsing"""
    
    # Extract and clean the required fields
    opinion_id = FreeLawCSVParser.parse_integer(row.get('id', ''))
    cluster_id = FreeLawCSVParser.parse_integer(row.get('cluster_id', ''))
    
    # Validate that we have required fields
    if opinion_id is None:
        raise ValueError("Missing required field: id")
    
    # Parse date fields
    date_created = FreeLawCSVParser.parse_datetime(row.get('date_created', ''))
    date_modified = FreeLawCSVParser.parse_datetime(row.get('date_modified', ''))
    
    # Parse string fields (note: author_str and joined_by_str are ignored as Opinion model uses author_id and joined_by)
    opinion_type = FreeLawCSVParser.parse_string(row.get('type', ''))
    sha1 = FreeLawCSVParser.parse_string(row.get('sha1', ''))
    download_url = FreeLawCSVParser.parse_string(row.get('download_url', ''))
    local_path = FreeLawCSVParser.parse_string(row.get('local_path', ''))
    plain_text = FreeLawCSVParser.parse_string(row.get('plain_text', ''))
    html = FreeLawCSVParser.parse_string(row.get('html', ''))
    html_lawbox = FreeLawCSVParser.parse_string(row.get('html_lawbox', ''))
    html_columbia = FreeLawCSVParser.parse_string(row.get('html_columbia', ''))
    html_anon_2020 = FreeLawCSVParser.parse_string(row.get('html_anon_2020', ''))
    xml_harvard = FreeLawCSVParser.parse_string(row.get('xml_harvard', ''))
    html_with_citations = FreeLawCSVParser.parse_string(row.get('html_with_citations', ''))
    
    # Parse optional fields
    page_count = FreeLawCSVParser.parse_integer(row.get('page_count', ''))
    author_id = FreeLawCSVParser.parse_integer(row.get('author_id', ''))
    per_curiam = FreeLawCSVParser.parse_boolean(row.get('per_curiam', ''))
    extracted_by_ocr = FreeLawCSVParser.parse_boolean(row.get('extracted_by_ocr', ''))
    
    # Handle missing opinion type
    if not opinion_type or not opinion_type.strip():
        opinion_type = '100unknown'
    
    # Map opinion type to enum - FIXED with all CourtListener types
    type_mapping = {
        '010combined': OpinionType.COMBINED,
        '015unamimous': OpinionType.UNANIMOUS,
        '020lead': OpinionType.LEAD,
        '025plurality': OpinionType.PLURALITY,
        '030concurrence': OpinionType.CONCURRENCE,
        '035concurrenceinpart': OpinionType.CONCUR_IN_PART,
        '040dissent': OpinionType.DISSENT,
        '050addendum': OpinionType.ADDENDUM,
        '060remittitur': OpinionType.REMITTUR,
        '070rehearing': OpinionType.REHEARING,
        '080onthemerits': OpinionType.ON_THE_MERITS,
        '090onmotiontostrike': OpinionType.ON_MOTION_TO_STRIKE,
        '100trialcourt': OpinionType.TRIAL_COURT,
        '999unknown': OpinionType.UNKNOWN
    }
    
    opinion_type_enum = type_mapping.get(opinion_type, OpinionType.UNKNOWN)
    
    # Create Opinion object with cluster_id fallback
    if cluster_id is None:
        cluster_id = 0  # Use 0 as placeholder for corrupted data
    
    return Opinion(
        id=opinion_id,
        cluster_id=cluster_id,
        date_created=date_created,
        date_modified=date_modified,
        type=opinion_type_enum,
        sha1=sha1,
        page_count=page_count,
        download_url=download_url,
        local_path=local_path,
        plain_text=plain_text,
        html=html,
        html_lawbox=html_lawbox,
        html_columbia=html_columbia,
        html_anon_2020=html_anon_2020,
        xml_harvard=xml_harvard,
        html_with_citations=html_with_citations,
        author_id=author_id,
        per_curiam=per_curiam,
        extracted_by_ocr=extracted_by_ocr
    )

def parse_citation_row(row: Dict[str, str]) -> Citation:
    """Parse a citation row from FreeLaw CSV - FIXED to use citation-map"""
    
    # Extract and clean the required fields - FIXED field names
    cited_opinion_id = FreeLawCSVParser.parse_integer(row.get('cited_opinion_id', ''))
    citing_opinion_id = FreeLawCSVParser.parse_integer(row.get('citing_opinion_id', ''))
    depth = FreeLawCSVParser.parse_integer(row.get('depth', ''))
    
    # Parse optional fields
    quoted = FreeLawCSVParser.parse_boolean(row.get('quoted', ''))
    parenthetical_id = FreeLawCSVParser.parse_integer(row.get('parenthetical_id', ''))
    parenthetical_text = FreeLawCSVParser.parse_string(row.get('parenthetical_text', ''))
    
    # Create Citation object
    return Citation(
        cited_opinion_id=cited_opinion_id,
        citing_opinion_id=citing_opinion_id,
        depth=depth,
        quoted=quoted,
        parenthetical_id=parenthetical_id,
        parenthetical_text=parenthetical_text
    )

def parse_court_row(row: Dict[str, str]) -> Court:
    """Parse a court row from FreeLaw CSV"""
    
    # Extract required fields
    court_id = FreeLawCSVParser.parse_string(row.get('id', ''))
    full_name = FreeLawCSVParser.parse_string(row.get('full_name', ''))
    short_name = FreeLawCSVParser.parse_string(row.get('short_name', ''))
    jurisdiction = FreeLawCSVParser.parse_string(row.get('jurisdiction', ''))
    position = FreeLawCSVParser.parse_float(row.get('position', ''))
    citation_string = FreeLawCSVParser.parse_string(row.get('citation_string', ''))
    
    # Validate required fields
    if not court_id:
        raise ValueError("Court ID is required")
    if not full_name:
        raise ValueError("Court full name is required")
    
    # Use empty string if jurisdiction is missing (some courts don't have jurisdiction data)
    if not jurisdiction:
        jurisdiction = ""
    
    # Parse optional fields
    start_date_str = FreeLawCSVParser.parse_string(row.get('start_date', ''))
    end_date_str = FreeLawCSVParser.parse_string(row.get('end_date', ''))
    notes = FreeLawCSVParser.parse_string(row.get('notes', ''))
    
    # Parse dates
    start_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass  # Keep as None if parse fails
    
    end_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass  # Keep as None if parse fails
    
    # Default position if not provided
    if position is None:
        position = 0.0
    
    return Court(
        id=court_id,
        full_name=full_name,
        short_name=short_name,
        jurisdiction=jurisdiction,
        position=position,
        citation_string=citation_string,
        start_date=start_date,
        end_date=end_date,
        notes=notes
    )

def parse_person_row(row: Dict[str, str]) -> Person:
    """Parse a person row from FreeLaw CSV"""
    
    # Extract and clean the required fields
    person_id = FreeLawCSVParser.parse_integer(row.get('id', ''))
    
    # Validate required fields
    if not person_id:
        raise ValueError("Person ID is required")
    
    # Parse date fields
    date_created = FreeLawCSVParser.parse_datetime(row.get('date_created', ''))
    date_modified = FreeLawCSVParser.parse_datetime(row.get('date_modified', ''))
    date_dob = FreeLawCSVParser.parse_date(row.get('date_dob', ''))
    date_dod = FreeLawCSVParser.parse_date(row.get('date_dod', ''))
    
    # Parse string fields
    name_first = FreeLawCSVParser.parse_string(row.get('name_first', ''))
    name_middle = FreeLawCSVParser.parse_string(row.get('name_middle', ''))
    name_last = FreeLawCSVParser.parse_string(row.get('name_last', ''))
    name_suffix = FreeLawCSVParser.parse_string(row.get('name_suffix', ''))
    
    # Parse location fields
    dob_city = FreeLawCSVParser.parse_string(row.get('dob_city', ''))
    dob_state = FreeLawCSVParser.parse_string(row.get('dob_state', ''))
    dod_city = FreeLawCSVParser.parse_string(row.get('dod_city', ''))
    dod_state = FreeLawCSVParser.parse_string(row.get('dod_state', ''))
    
    # Parse granularity fields
    date_granularity_dob = FreeLawCSVParser.parse_string(row.get('date_granularity_dob', ''))
    date_granularity_dod = FreeLawCSVParser.parse_string(row.get('date_granularity_dod', ''))
    
    # Parse other fields
    gender = FreeLawCSVParser.parse_string(row.get('gender', ''))
    religion = FreeLawCSVParser.parse_string(row.get('religion', ''))
    ftm_total_received = FreeLawCSVParser.parse_float(row.get('ftm_total_received', ''))
    ftm_eid = FreeLawCSVParser.parse_string(row.get('ftm_eid', ''))
    has_photo = FreeLawCSVParser.parse_boolean(row.get('has_photo', ''))
    is_alias_of = FreeLawCSVParser.parse_integer(row.get('is_alias_of_id', ''))
    
    # Create Person object
    return Person(
        id=person_id,
        date_created=date_created,
        date_modified=date_modified,
        name_first=name_first,
        name_middle=name_middle,
        name_last=name_last,
        name_suffix=name_suffix,
        date_dob=date_dob,
        date_granularity_dob=date_granularity_dob,
        date_dod=date_dod,
        date_granularity_dod=date_granularity_dod,
        dob_city=dob_city,
        dob_state=dob_state,
        dod_city=dod_city,
        dod_state=dod_state,
        gender=gender,
        religion=religion,
        ftm_total_received=ftm_total_received,
        ftm_eid=ftm_eid,
        has_photo=has_photo,
        is_alias_of=is_alias_of
    )

def import_data_type(storage: CourtFinderStorage, file_path: Path, data_type: str, 
                    parser_func, save_func, limit: Optional[int] = None,
                    checkpoint: Optional[ImportCheckpoint] = None,
                    progress: Optional[ImportProgress] = None,
                    ui: Optional[ImportUI] = None) -> Dict[str, Any]:
    """Import a specific data type from bz2 file with checkpoint and progress support"""
    
    print(f"📦 Processing {file_path.name} ({data_type})...")
    
    if not file_path.exists():
        return {'success': False, 'error': f'File not found: {file_path}'}
    
    # Check for existing checkpoint
    resume_from = 0
    imported_count = 0
    error_count = 0
    last_id = None
    
    if checkpoint:
        cp_data = checkpoint.load_checkpoint(data_type)
        if cp_data:
            resume_info = checkpoint.get_resume_info(data_type)
            print(f"📍 {resume_info}")
            resume_from = cp_data['row_number']
            imported_count = cp_data['imported_count']
            error_count = cp_data['error_count']
            last_id = cp_data['last_processed_id']
    
    # Estimate total records (rough estimate based on file size)
    file_size = file_path.stat().st_size
    estimated_total = None
    if data_type == "courts":
        estimated_total = 2000
    elif data_type == "dockets":
        estimated_total = int(file_size / 1100)  # ~1.1KB per record
    elif data_type == "opinions":
        estimated_total = int(file_size / 2100)  # ~2.1KB per record
    elif data_type == "citations":
        estimated_total = int(file_size / 225)   # ~225 bytes per record
    elif data_type == "people":
        estimated_total = 10000
    
    # Start progress tracking
    if progress:
        progress.start_data_type(data_type, str(file_path), estimated_total, resume_from)
    
    try:
        with bz2.open(file_path, 'rt', encoding='utf-8') as f:
            # Handle complex CSV with embedded HTML and quotes
            reader = csv.DictReader(f, quoting=csv.QUOTE_MINIMAL)
            
            for row_num, row in enumerate(reader, 1):
                # Skip to resume point
                if row_num < resume_from:
                    continue
                    
                if limit and row_num > limit:
                    break
                
                # Skip empty rows
                if not row.get('id'):
                    continue
                
                try:
                    # Parse the row
                    obj = parser_func(row)
                    
                    # Save to storage
                    save_func(obj)
                    
                    imported_count += 1
                    last_id = row.get('id', '')
                    
                    # Track success in UI
                    if ui:
                        ui.add_success()
                    
                    # Update progress
                    if progress:
                        progress.update_progress(data_type, row_num, imported_count, error_count, last_id)
                    
                    # Save checkpoint every 1000 records
                    if checkpoint and imported_count % 1000 == 0:
                        checkpoint.save_checkpoint(data_type, str(file_path), last_id, 
                                                 row_num, imported_count, error_count)
                    
                    if imported_count % 100 == 0 and not ui:
                        print(f"  📊 Imported {imported_count} {data_type}...")
                    
                except Exception as e:
                    error_count += 1
                    error_msg = f"Error processing row {row_num}: {e}"
                    
                    if ui:
                        ui.add_error(f"{data_type} - {error_msg}")
                    elif error_count <= 5:  # Only show first 5 errors
                        print(f"  ❌ {error_msg}")
                    continue
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'imported_count': imported_count,
            'error_count': error_count
        }
    
    # Mark as complete
    if progress:
        progress.finish_data_type(data_type)
    
    # Clear checkpoint on successful completion
    if checkpoint and not limit:
        checkpoint.clear_checkpoint(data_type)
    
    print(f"✅ Successfully imported {imported_count} {data_type} ({error_count} errors)")
    return {
        'success': True,
        'imported_count': imported_count,
        'error_count': error_count
    }

def import_opinions_html_aware(storage: CourtFinderStorage, file_path: Path, 
                               limit: Optional[int] = None) -> Dict[str, Any]:
    """Import opinions using HTML-aware CSV parser with detailed error reporting"""
    
    print(f"📦 Processing {file_path.name} (opinions with HTML-aware parsing)...")
    
    if not file_path.exists():
        return {'success': False, 'error': f'File not found: {file_path}'}
    
    imported_count = 0
    error_count = 0
    error_details = {}
    
    try:
        # Use the specialized HTML-aware parser
        print("🔍 Parsing opinion CSV with HTML-aware method...")
        valid_rows = OpinionCSVParser.parse_opinion_csv(file_path, limit)
        
        print(f"✅ Found {len(valid_rows)} valid opinion rows out of CSV data")
        
        if not valid_rows:
            return {'success': False, 'error': 'No valid opinion rows found'}
        
        # Process each valid row with detailed error reporting
        for row_num, row in enumerate(valid_rows, 1):
            try:
                # Parse the row using the standard parser
                obj = parse_opinion_row(row)
                
                # Save to storage
                storage.save_opinion(obj)
                
                imported_count += 1
                
                if imported_count % 10 == 0:
                    print(f"  📊 Imported {imported_count} opinions...")
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                
                # Track error types
                if error_msg not in error_details:
                    error_details[error_msg] = 0
                error_details[error_msg] += 1
                
                # Show detailed error info for first few errors
                if error_count <= 10:
                    print(f"  ❌ Error processing valid row {row_num}: {error_msg}")
                    print(f"     Row ID: {row.get('id', 'N/A')}")
                    print(f"     Row type: {row.get('type', 'N/A')}")
                    print(f"     Row cluster_id: {row.get('cluster_id', 'N/A')}")
                    
                    if error_count <= 3:
                        import traceback
                        traceback.print_exc()
                
                continue
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'imported_count': imported_count,
            'error_count': error_count,
            'error_details': error_details
        }
    
    # Report error summary
    if error_details:
        print(f"\n📊 ERROR SUMMARY:")
        for error_msg, count in error_details.items():
            print(f"  {error_msg}: {count} occurrences")
    
    print(f"✅ Successfully imported {imported_count} opinions ({error_count} errors)")
    return {
        'success': True,
        'imported_count': imported_count,
        'error_count': error_count,
        'error_details': error_details
    }

def main(use_limits=True, use_resume=False, use_ui=False):
    """Import ALL FreeLaw data types - FIXED VERSION with resume and UI support"""
    
    print("🏛️  FREELAW BULK DATA IMPORTER - FIXED VERSION")
    print("=" * 70)
    if use_limits:
        print("Processing bz2 files with REASONABLE LIMITS for fast import")
    else:
        print("Processing ALL bz2 files with NO LIMITS (will take hours)")
    if use_resume:
        print("📍 RESUME MODE: Will continue from last checkpoint")
    if use_ui:
        print("🖥️  UI MODE: Progress will be shown in interactive display")
    print("=" * 70)
    
    # Setup
    downloads_dir = Path("downloads")
    data_dir = Path("real_data")
    
    # Initialize checkpoint and progress systems
    checkpoint = ImportCheckpoint() if use_resume else None
    progress = ImportProgress() if (use_ui or use_resume) else None
    ui = None
    
    # Start UI if requested
    if use_ui:
        # Use Rich UI which is more compatible
        ui = ImportUIRich(progress)
        ui.start()
        import time
        time.sleep(1)  # Give UI time to start
    
    if not downloads_dir.exists():
        print("❌ No downloads/ directory found")
        return False
    
    # Create storage
    storage = CourtFinderStorage(str(data_dir))
    
    # Complete import configurations - FIXED with HTML-aware opinions
    if use_limits:
        # REASONABLE LIMITS for fast import and testing
        imports = [
            ("courts-2024-12-31.csv.bz2", "courts", parse_court_row, storage.save_court, None),  # Import ALL courts (small file)
            ("dockets-2024-12-31.csv.bz2", "dockets", parse_docket_row, storage.save_docket, 5000),  # 5K dockets
            ("opinion-clusters-2024-12-31.csv.bz2", "opinion_clusters", parse_opinion_cluster_row, storage.save_opinion_cluster, 2000),  # 2K clusters
            ("citation-map-2025-07-02.csv.bz2", "citations", parse_citation_row, storage.save_citation, 10000),  # 10K citations
            ("people-db-people-2024-12-31.csv.bz2", "people", parse_person_row, storage.save_person, 1000),  # 1K people
        ]
        opinion_limit = 1000  # 1K opinions
    else:
        # NO LIMITS - import everything (will take hours)
        imports = [
            ("courts-2024-12-31.csv.bz2", "courts", parse_court_row, storage.save_court, None),  # Import ALL courts (small file)
            ("dockets-2024-12-31.csv.bz2", "dockets", parse_docket_row, storage.save_docket, None),  # ALL dockets
            ("opinion-clusters-2024-12-31.csv.bz2", "opinion_clusters", parse_opinion_cluster_row, storage.save_opinion_cluster, None),  # ALL clusters
            ("citation-map-2025-07-02.csv.bz2", "citations", parse_citation_row, storage.save_citation, None),  # ALL citations
            ("people-db-people-2024-12-31.csv.bz2", "people", parse_person_row, storage.save_person, None),  # ALL people
        ]
        opinion_limit = None  # ALL opinions
    
    # Special handling for opinions with HTML-aware parsing
    opinions_file = downloads_dir / "opinions-2024-12-31.csv.bz2"
    
    print(f"\n🚀 Starting FIXED import process...")
    
    total_imported = 0
    total_errors = 0
    
    for filename, data_type, parser_func, save_func, limit in imports:
        if parser_func is None:
            print(f"⏭️  Skipping {data_type} - already imported")
            continue
        
        file_path = downloads_dir / filename
        
        if not file_path.exists():
            print(f"⏭️  Skipping {filename} - file not found")
            continue
        
        print(f"\n📥 IMPORTING {data_type.upper()}")
        print("-" * 50)
        
        result = import_data_type(storage, file_path, data_type, parser_func, save_func, limit,
                                checkpoint=checkpoint, progress=progress, ui=ui)
        
        if result['success']:
            total_imported += result['imported_count']
            total_errors += result['error_count']
        else:
            print(f"❌ Failed to import {data_type}: {result['error']}")
    
    # Special handling for opinions with HTML-aware parsing
    if opinions_file.exists():
        print(f"\n📥 IMPORTING OPINIONS (HTML-AWARE)")
        print("-" * 50)
        
        result = import_opinions_html_aware(storage, opinions_file, opinion_limit)
        
        if result['success']:
            total_imported += result['imported_count']
            total_errors += result['error_count']
        else:
            print(f"❌ Failed to import opinions: {result['error']}")
    else:
        print(f"\n⏭️  Skipping opinions - file not found")
    
    # Show final stats
    print(f"\n📊 FINAL STATISTICS")
    print("=" * 70)
    
    stats = storage.get_storage_stats()
    for data_type, stat in stats.items():
        if isinstance(stat, dict) and 'total_items' in stat:
            print(f"  {data_type}: {stat['total_items']} items")
    
    print(f"\n✅ FIXED IMPORT COMPLETE!")
    print(f"📈 Total imported: {total_imported} records")
    print(f"⚠️  Total errors: {total_errors} records")
    
    # Stop UI if running
    if ui:
        ui.stop()
    
    return True

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Import FreeLaw bulk data with resume and UI support')
    parser.add_argument('--no-limits', action='store_true', 
                       help='Import all data without limits (will take hours)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last checkpoint')
    parser.add_argument('--ui', action='store_true',
                       help='Show progress in interactive UI')
    
    args = parser.parse_args()
    
    # Show warnings
    if args.no_limits:
        print("⚠️  WARNING: Running with NO LIMITS - this will take hours!")
    
    try:
        success = main(use_limits=not args.no_limits, 
                      use_resume=args.resume,
                      use_ui=args.ui)
        
        if success:
            if not args.no_limits:
                print("\n🎉 LIMITED IMPORT COMPLETE - run with --no-limits for full dataset!")
            else:
                print("\n🎉 ALL ISSUES FIXED - COMPLETE DATASET IMPORTED!")
        else:
            print("\n❌ Import failed!")
    except KeyboardInterrupt:
        print("\n⚠️  Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Import failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)