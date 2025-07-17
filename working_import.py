#!/usr/bin/env python3
"""
Working import script based on the successful test
"""

import sys
import csv
import bz2
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import Docket, OpinionCluster, Opinion, Citation, OpinionType

class WorkingCSVParser:
    """Simple CSV parser that works"""
    
    @staticmethod
    def clean_value(value: str) -> str:
        """Remove backticks that FreeLaw wraps around all values"""
        if isinstance(value, str) and value.startswith('`') and value.endswith('`'):
            return value[1:-1]
        return value
    
    @staticmethod
    def parse_integer(value: str) -> Optional[int]:
        """Parse integer value"""
        if not value or value.strip() == '':
            return None
        
        value = WorkingCSVParser.clean_value(value).strip()
        if not value:
            return None
        
        try:
            return int(value)
        except ValueError:
            return None
    
    @staticmethod
    def parse_string(value: str) -> str:
        """Parse string value"""
        if not value:
            return ''
        return WorkingCSVParser.clean_value(value)
    
    @staticmethod
    def parse_boolean(value: str) -> bool:
        """Parse boolean value"""
        if not value or value.strip() == '':
            return False
        
        value = WorkingCSVParser.clean_value(value).strip().lower()
        return value in ['true', 't', '1', 'yes', 'y']
    
    @staticmethod
    def parse_datetime(value: str) -> Optional[datetime]:
        """Parse FreeLaw datetime format"""
        if not value or value.strip() == '':
            return None
        
        value = WorkingCSVParser.clean_value(value).strip()
        if not value:
            return None
        
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

def parse_docket_row_working(row: Dict[str, str]) -> Docket:
    """Parse a docket row - working version"""
    
    # Extract required fields
    docket_id = WorkingCSVParser.parse_integer(row.get('id', ''))
    court_id = WorkingCSVParser.parse_string(row.get('court_id', ''))
    case_name = WorkingCSVParser.parse_string(row.get('case_name', ''))
    docket_number = WorkingCSVParser.parse_string(row.get('docket_number', ''))
    source = WorkingCSVParser.parse_string(row.get('source', ''))
    
    # Validate required fields
    if not docket_id:
        raise ValueError("Docket ID is required")
    if not court_id:
        raise ValueError("Court ID is required")
    if not case_name:
        raise ValueError("Case name is required")
    if not docket_number:
        raise ValueError("Docket number is required")
    
    # Parse date fields
    date_created = WorkingCSVParser.parse_datetime(row.get('date_created', ''))
    date_modified = WorkingCSVParser.parse_datetime(row.get('date_modified', ''))
    
    # Create Docket object with minimal fields
    return Docket(
        id=docket_id,
        court_id=court_id,
        case_name=case_name,
        docket_number=docket_number,
        source=source,
        date_created=date_created,
        date_modified=date_modified
    )

def import_dockets_working(storage: CourtFinderStorage, limit: int = 5000) -> Dict[str, Any]:
    """Import dockets - working version"""
    
    print(f"📥 IMPORTING DOCKETS (limit: {limit})")
    print("-" * 40)
    
    file_path = Path("downloads/dockets-2024-12-31.csv.bz2")
    if not file_path.exists():
        return {'success': False, 'error': 'Dockets file not found'}
    
    imported_count = 0
    error_count = 0
    
    try:
        with bz2.open(file_path, 'rt', encoding='utf-8') as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_MINIMAL)
            
            for row_num, row in enumerate(reader, 1):
                if row_num > limit:
                    break
                
                try:
                    # Parse the row
                    docket = parse_docket_row_working(row)
                    
                    # Save to storage
                    storage.save_docket(docket)
                    
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        print(f"  📊 Imported {imported_count} dockets...")
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:
                        print(f"  ❌ Error processing row {row_num}: {e}")
                    continue
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'imported_count': imported_count,
            'error_count': error_count
        }
    
    print(f"✅ Successfully imported {imported_count} dockets ({error_count} errors)")
    return {
        'success': True,
        'imported_count': imported_count,
        'error_count': error_count
    }

def main_working():
    """Main working import function"""
    
    print("🏛️  WORKING FREELAW IMPORTER")
    print("=" * 50)
    
    # Create storage
    storage = CourtFinderStorage("real_data")
    
    # Import dockets
    result = import_dockets_working(storage, limit=5000)
    
    if result['success']:
        print(f"✅ Successfully imported {result['imported_count']} dockets")
    else:
        print(f"❌ Failed to import dockets: {result['error']}")
    
    # Show final stats
    print(f"\n📊 STORAGE STATISTICS:")
    print("-" * 30)
    stats = storage.get_storage_stats()
    for data_type, stat in stats.items():
        if isinstance(stat, dict) and 'total_items' in stat:
            print(f"  {data_type}: {stat['total_items']:,} items")

if __name__ == "__main__":
    main_working()