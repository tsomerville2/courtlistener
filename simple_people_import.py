#!/usr/bin/env python3
"""Simple people import without exec"""

import sys
import bz2
import csv
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Optional

sys.path.insert(0, str(Path.cwd() / 'src'))
from courtfinder.storage import CourtFinderStorage
from courtfinder.models import Person

class FreeLawCSVParser:
    @staticmethod
    def clean_value(value: str) -> str:
        """Remove backticks that FreeLaw wraps around all values"""
        if isinstance(value, str) and value.startswith('`') and value.endswith('`'):
            return value[1:-1]
        return value
    
    @staticmethod
    def parse_string(value: str) -> str:
        if not value:
            return ''
        return FreeLawCSVParser.clean_value(value)
    
    @staticmethod
    def parse_integer(value: str) -> Optional[int]:
        if not value or value.strip() == '':
            return None
        cleaned = FreeLawCSVParser.clean_value(value)
        if cleaned == '\\N' or cleaned == '':
            return None
        try:
            return int(cleaned)
        except ValueError:
            return None
    
    @staticmethod
    def parse_datetime(value: str) -> Optional[datetime]:
        if not value:
            return None
        cleaned = FreeLawCSVParser.clean_value(value)
        if cleaned == '\\N' or cleaned == '':
            return None
        try:
            return datetime.fromisoformat(cleaned.replace('+00', '+00:00'))
        except:
            return None
    
    @staticmethod
    def parse_date(value: str) -> Optional[date]:
        if not value:
            return None
        cleaned = FreeLawCSVParser.clean_value(value)
        if cleaned == '\\N' or cleaned == '':
            return None
        try:
            return date.fromisoformat(cleaned)
        except:
            return None
    
    @staticmethod
    def parse_boolean(value: str) -> bool:
        if not value:
            return False
        cleaned = FreeLawCSVParser.clean_value(value)
        return cleaned.lower() in ('t', 'true', '1', 'yes')
    
    @staticmethod
    def parse_float(value: str) -> Optional[float]:
        if not value or value.strip() == '':
            return None
        cleaned = FreeLawCSVParser.clean_value(value)
        if cleaned == '\\N' or cleaned == '':
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

def parse_person_row(row: Dict[str, str]) -> Person:
    """Parse a person row from FreeLaw CSV"""
    person_id = FreeLawCSVParser.parse_integer(row.get('id', ''))
    if not person_id:
        raise ValueError("Person ID is required")
    
    return Person(
        id=person_id,
        date_created=FreeLawCSVParser.parse_datetime(row.get('date_created', '')),
        date_modified=FreeLawCSVParser.parse_datetime(row.get('date_modified', '')),
        name_first=FreeLawCSVParser.parse_string(row.get('name_first', '')),
        name_middle=FreeLawCSVParser.parse_string(row.get('name_middle', '')),
        name_last=FreeLawCSVParser.parse_string(row.get('name_last', '')),
        name_suffix=FreeLawCSVParser.parse_string(row.get('name_suffix', '')),
        date_dob=FreeLawCSVParser.parse_date(row.get('date_dob', '')),
        date_granularity_dob=FreeLawCSVParser.parse_string(row.get('date_granularity_dob', '')),
        date_dod=FreeLawCSVParser.parse_date(row.get('date_dod', '')),
        date_granularity_dod=FreeLawCSVParser.parse_string(row.get('date_granularity_dod', '')),
        dob_city=FreeLawCSVParser.parse_string(row.get('dob_city', '')),
        dob_state=FreeLawCSVParser.parse_string(row.get('dob_state', '')),
        dod_city=FreeLawCSVParser.parse_string(row.get('dod_city', '')),
        dod_state=FreeLawCSVParser.parse_string(row.get('dod_state', '')),
        gender=FreeLawCSVParser.parse_string(row.get('gender', '')),
        religion=FreeLawCSVParser.parse_string(row.get('religion', '')),
        ftm_total_received=FreeLawCSVParser.parse_float(row.get('ftm_total_received', '')),
        ftm_eid=FreeLawCSVParser.parse_string(row.get('ftm_eid', '')),
        has_photo=FreeLawCSVParser.parse_boolean(row.get('has_photo', '')),
        is_alias_of=FreeLawCSVParser.parse_integer(row.get('is_alias_of_id', ''))
    )

# Main import
storage = CourtFinderStorage('real_data')
file_path = Path('downloads/people-db-people-2024-12-31.csv.bz2')

print(f"📥 Importing people from {file_path.name}...")
imported_count = 0
error_count = 0

try:
    with bz2.open(file_path, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, 1):
            if row_num > 1000:  # Limit to 1000
                break
            
            try:
                person = parse_person_row(row)
                storage.save_person(person)
                imported_count += 1
                
                if imported_count % 100 == 0:
                    print(f"  📊 Imported {imported_count} people...")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"  ❌ Error on row {row_num}: {e}")

    print(f"✅ Successfully imported {imported_count} people ({error_count} errors)")
    
    # Check final stats
    stats = storage.get_storage_stats()
    people_info = stats.get('people', {})
    if isinstance(people_info, dict):
        print(f"Final people count: {people_info.get('total_items', 0)}")
        
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()