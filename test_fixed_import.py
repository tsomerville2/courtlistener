#!/usr/bin/env python3
"""
Test the fixed import process
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage

# Import the fixed functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def test_fixed_import():
    """Test the fixed import process"""
    print("🔍 Testing fixed import process...")
    
    storage = CourtFinderStorage("real_data")
    file_path = Path("downloads/opinions-2024-12-31.csv.bz2")
    
    if not file_path.exists():
        print("❌ Opinion file not found")
        return
    
    try:
        # Test importing 20 opinions
        print("Testing import of 20 opinions...")
        result = import_opinions_html_aware(storage, file_path, limit=20)
        
        print(f"\n📊 IMPORT RESULTS:")
        print(f"Success: {result['success']}")
        print(f"Imported: {result['imported_count']}")
        print(f"Errors: {result['error_count']}")
        
        if result.get('error_details'):
            print("\nError details:")
            for error, count in result['error_details'].items():
                print(f"  {error}: {count}")
        
        # Show storage stats
        stats = storage.get_storage_stats()
        print(f"\n📈 Storage stats:")
        for data_type, stat in stats.items():
            if isinstance(stat, dict) and 'total_items' in stat:
                print(f"  {data_type}: {stat['total_items']} items")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_import()