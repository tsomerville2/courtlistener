#!/usr/bin/env python3
"""
Test individual components to identify the issue
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage

# Test just the basic parsing functions without the exec
import csv
import bz2
from datetime import datetime
from typing import Dict, Optional

def clean_value(value: str) -> str:
    """Remove backticks that FreeLaw wraps around all values"""
    if isinstance(value, str) and value.startswith('`') and value.endswith('`'):
        return value[1:-1]
    return value

def parse_integer(value: str) -> Optional[int]:
    """Parse integer value"""
    if not value or value.strip() == '':
        return None
    
    value = clean_value(value).strip()
    if not value:
        return None
    
    try:
        return int(value)
    except ValueError:
        return None

def parse_string(value: str) -> str:
    """Parse string value"""
    if not value:
        return ''
    return clean_value(value)

def test_basic_docket_parsing():
    """Test basic docket parsing without the complex import system"""
    print("🔍 Testing basic docket parsing...")
    
    file_path = Path("downloads/dockets-2024-12-31.csv.bz2")
    if not file_path.exists():
        print("❌ Dockets file not found")
        return
    
    try:
        with bz2.open(file_path, 'rt', encoding='utf-8') as f:
            reader = csv.DictReader(f, quoting=csv.QUOTE_MINIMAL)
            
            count = 0
            for row in reader:
                count += 1
                if count > 10:  # Just test first 10 rows
                    break
                
                # Try to parse basic fields
                docket_id = parse_integer(row.get('id', ''))
                court_id = parse_string(row.get('court_id', ''))
                case_name = parse_string(row.get('case_name', ''))
                
                print(f"  Row {count}: ID={docket_id}, Court={court_id}, Case={case_name[:50]}...")
                
                if not docket_id:
                    print(f"    ❌ Invalid docket ID")
                    continue
                    
                if not court_id:
                    print(f"    ❌ Missing court ID")
                    continue
                    
                if not case_name:
                    print(f"    ❌ Missing case name")
                    continue
                    
                print(f"    ✅ Valid docket")
        
        print(f"✅ Successfully processed {count} docket rows")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_storage():
    """Test storage system"""
    print("\n🔍 Testing storage system...")
    
    try:
        storage = CourtFinderStorage("real_data")
        stats = storage.get_storage_stats()
        
        print("✅ Storage system working")
        print("Current stats:")
        for data_type, stat in stats.items():
            if isinstance(stat, dict) and 'total_items' in stat:
                print(f"  {data_type}: {stat['total_items']:,} items")
                
    except Exception as e:
        print(f"❌ Storage error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_storage()
    test_basic_docket_parsing()