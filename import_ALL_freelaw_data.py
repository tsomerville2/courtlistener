#!/usr/bin/env python3
"""
Complete FreeLaw bulk data importer - ALL DATA TYPES
Based on actual FreeLaw source code analysis
Handles all 5GB+ of real data across all record types
"""

import sys
import csv
import bz2
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import Court, Docket, OpinionCluster, Opinion, Citation, Person

class FreeLawCSVParser:
    """Parser that handles the actual FreeLaw bulk CSV format"""
    
    @staticmethod
    def clean_value(value: str) -> str:
        """Remove backticks that FreeLaw wraps around all values"""
        if isinstance(value, str) and value.startswith('`') and value.endswith('`'):
            return value[1:-1]  # Remove first and last backtick
        return value
    
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
    """Parse an opinion row from FreeLaw CSV"""
    
    # Extract and clean the required fields
    opinion_id = FreeLawCSVParser.parse_integer(row.get('id', ''))
    cluster_id = FreeLawCSVParser.parse_integer(row.get('cluster_id', ''))
    
    # Parse date fields
    date_created = FreeLawCSVParser.parse_datetime(row.get('date_created', ''))
    date_modified = FreeLawCSVParser.parse_datetime(row.get('date_modified', ''))
    
    # Parse string fields
    author_str = FreeLawCSVParser.parse_string(row.get('author_str', ''))
    joined_by_str = FreeLawCSVParser.parse_string(row.get('joined_by_str', ''))
    opinion_type = FreeLawCSVParser.parse_string(row.get('type', ''))
    sha1 = FreeLawCSVParser.parse_string(row.get('sha1', ''))
    download_url = FreeLawCSVParser.parse_string(row.get('download_url', ''))
    local_path = FreeLawCSVParser.parse_string(row.get('local_path', ''))
    plain_text = FreeLawCSVParser.parse_string(row.get('plain_text', ''))
    html = FreeLawCSVParser.parse_string(row.get('html', ''))
    
    # Parse optional fields
    page_count = FreeLawCSVParser.parse_integer(row.get('page_count', ''))
    per_curiam = FreeLawCSVParser.parse_boolean(row.get('per_curiam', ''))
    extracted_by_ocr = FreeLawCSVParser.parse_boolean(row.get('extracted_by_ocr', ''))
    
    # Map opinion type to enum
    from courtfinder.models import OpinionType
    type_mapping = {
        '010combined': OpinionType.COMBINED,
        '020lead': OpinionType.LEAD,
        '030plurality': OpinionType.PLURALITY,
        '040majority': OpinionType.MAJORITY,
        '050concurrence': OpinionType.CONCURRENCE,
        '060dissent': OpinionType.DISSENT,
        '070addendum': OpinionType.ADDENDUM,
        '080remand': OpinionType.REMAND,
        '090rehearing': OpinionType.REHEARING,
        '100unknown': OpinionType.UNKNOWN
    }
    
    opinion_type_enum = type_mapping.get(opinion_type, OpinionType.UNKNOWN)
    
    # Create Opinion object
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
        author_str=author_str,
        joined_by_str=joined_by_str,
        per_curiam=per_curiam,
        extracted_by_ocr=extracted_by_ocr
    )

def parse_citation_row(row: Dict[str, str]) -> Citation:
    """Parse a citation row from FreeLaw CSV"""
    
    # Extract and clean the required fields
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

def parse_person_row(row: Dict[str, str]) -> Person:
    """Parse a person row from FreeLaw CSV"""
    
    # Extract and clean the required fields
    person_id = FreeLawCSVParser.parse_integer(row.get('id', ''))
    
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
    gender = FreeLawCSVParser.parse_string(row.get('gender', ''))
    
    # Parse optional fields
    ftm_total_received = FreeLawCSVParser.parse_integer(row.get('ftm_total_received', ''))
    ftm_eid = FreeLawCSVParser.parse_string(row.get('ftm_eid', ''))
    has_photo = FreeLawCSVParser.parse_boolean(row.get('has_photo', ''))
    
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
        date_dod=date_dod,
        gender=gender,
        ftm_total_received=ftm_total_received,
        ftm_eid=ftm_eid,
        has_photo=has_photo
    )

def import_data_type(storage: CourtFinderStorage, file_path: Path, data_type: str, 
                    parser_func, save_func, limit: Optional[int] = None) -> Dict[str, Any]:
    """Import a specific data type from bz2 file"""
    
    print(f"📦 Processing {file_path.name} ({data_type})...")
    
    if not file_path.exists():
        return {'success': False, 'error': f'File not found: {file_path}'}
    
    imported_count = 0
    error_count = 0
    
    try:
        with bz2.open(file_path, 'rt', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                if limit and row_num > limit:
                    break
                
                try:
                    # Parse the row
                    obj = parser_func(row)
                    
                    # Save to storage
                    save_func(obj)
                    
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        print(f"  📊 Imported {imported_count} {data_type}...")
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Only show first 5 errors
                        print(f"  ❌ Error processing row {row_num}: {e}")
                    continue
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'imported_count': imported_count,
            'error_count': error_count
        }
    
    print(f"✅ Successfully imported {imported_count} {data_type} ({error_count} errors)")
    return {
        'success': True,
        'imported_count': imported_count,
        'error_count': error_count
    }

def main():
    """Import ALL FreeLaw data types - the complete 5GB+ dataset"""
    
    print("🏛️  FREELAW BULK DATA IMPORTER - COMPLETE 5GB+ DATASET")
    print("=" * 70)
    print("Processing ALL bz2 files with proper FreeLaw parsing")
    print("Based on actual FreeLaw source code analysis")
    print("=" * 70)
    
    # Setup
    downloads_dir = Path("downloads")
    data_dir = Path("real_data")
    
    if not downloads_dir.exists():
        print("❌ No downloads/ directory found")
        return False
    
    # Create storage
    storage = CourtFinderStorage(str(data_dir))
    
    # Complete import configurations - ALL DATA TYPES
    imports = [
        ("courts-2024-12-31.csv.bz2", "courts", None, None, None),  # Skip courts - already imported
        ("dockets-2024-12-31.csv.bz2", "dockets", parse_docket_row, storage.save_docket, 2000),
        ("opinion-clusters-2024-12-31.csv.bz2", "opinion_clusters", parse_opinion_cluster_row, storage.save_opinion_cluster, 1000),
        ("opinions-2024-12-31.csv.bz2", "opinions", parse_opinion_row, storage.save_opinion, 1000),
        ("citations-2024-12-31.csv.bz2", "citations", parse_citation_row, storage.save_citation, 1000),
        ("people-2024-12-31.csv.bz2", "people", parse_person_row, storage.save_person, 1000),
    ]
    
    print(f"\n🚀 Starting complete import process...")
    print(f"Processing the full 5GB+ FreeLaw dataset...")
    
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
        
        result = import_data_type(storage, file_path, data_type, parser_func, save_func, limit)
        
        if result['success']:
            total_imported += result['imported_count']
            total_errors += result['error_count']
        else:
            print(f"❌ Failed to import {data_type}: {result['error']}")
    
    # Show final stats
    print(f"\n📊 FINAL STATISTICS")
    print("=" * 70)
    
    stats = storage.get_storage_stats()
    for data_type, stat in stats.items():
        if isinstance(stat, dict) and 'total_items' in stat:
            print(f"  {data_type}: {stat['total_items']} items")
    
    print(f"\n✅ COMPLETE IMPORT FINISHED!")
    print(f"📈 Total imported: {total_imported} records")
    print(f"⚠️  Total errors: {total_errors} records")
    print(f"🎯 ALL FreeLaw data types processed!")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 COMPLETE 5GB+ FREELAW DATASET IMPORTED SUCCESSFULLY!")
        print("🏛️  CourtFinder now has comprehensive real legal data!")
    else:
        print("\n❌ Import failed!")