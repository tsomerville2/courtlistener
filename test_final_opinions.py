#!/usr/bin/env python3
"""
Final test of the opinion import
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage

# Load the main script
exec(open('import_ALL_freelaw_data_FIXED.py').read())

# Test just the opinion import
def test_opinion_import():
    storage = CourtFinderStorage("real_data")
    file_path = Path("downloads/opinions-2024-12-31.csv.bz2")
    
    if file_path.exists():
        print("Testing opinion import...")
        result = import_opinions_html_aware(storage, file_path, limit=50)
        
        if result['success']:
            print(f"✅ Imported {result['imported_count']} opinions")
            print(f"⚠️  {result['error_count']} errors")
            
            # Show final stats
            stats = storage.get_storage_stats()
            print(f"Total opinions in storage: {stats.get('opinions', {}).get('total_items', 0)}")
        else:
            print(f"❌ Import failed: {result['error']}")
    else:
        print("Opinion file not found")

if __name__ == "__main__":
    test_opinion_import()