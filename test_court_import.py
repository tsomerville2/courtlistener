#!/usr/bin/env python3
"""
Test court import specifically
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage

# Import the parsing functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def test_court_import():
    """Test court import"""
    print("🔍 Testing court import...")
    
    storage = CourtFinderStorage("real_data")
    
    # Check current court count
    stats = storage.get_storage_stats()
    print(f"Current courts: {stats.get('courts', {}).get('total_items', 0)}")
    
    # Test importing courts
    file_path = Path("downloads/courts-2024-12-31.csv.bz2")
    if not file_path.exists():
        print("❌ Court file not found")
        return
    
    print("\n📥 Importing courts...")
    result = import_data_type(storage, file_path, "courts", parse_court_row, storage.save_court, limit=10)
    
    if result['success']:
        print(f"✅ Successfully imported {result['imported_count']} courts")
        print(f"⚠️  {result['error_count']} errors")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Check final court count
    stats = storage.get_storage_stats()
    print(f"\nFinal courts: {stats.get('courts', {}).get('total_items', 0)}")

if __name__ == "__main__":
    test_court_import()