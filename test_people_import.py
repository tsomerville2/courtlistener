#!/usr/bin/env python3
"""
Test people import specifically
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage

# Import the parsing functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def test_people_import():
    """Test people import"""
    print("🔍 Testing people import...")
    
    storage = CourtFinderStorage("real_data")
    
    # Check current people count
    stats = storage.get_storage_stats()
    print(f"Current people: {stats.get('people', {}).get('total_items', 0)}")
    
    # Test importing people
    file_path = Path("downloads/people-db-people-2024-12-31.csv.bz2")
    if not file_path.exists():
        print("❌ People file not found")
        return
    
    print("\n📥 Importing people...")
    result = import_data_type(storage, file_path, "people", parse_person_row, storage.save_person, limit=10)
    
    if result['success']:
        print(f"✅ Successfully imported {result['imported_count']} people")
        print(f"⚠️  {result['error_count']} errors")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Check final people count
    stats = storage.get_storage_stats()
    print(f"\nFinal people: {stats.get('people', {}).get('total_items', 0)}")

if __name__ == "__main__":
    test_people_import()