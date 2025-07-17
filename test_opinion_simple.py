#!/usr/bin/env python3
"""
Simple test for opinion parsing and import
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import OpinionType

# Import the parsing functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def test_opinion_parsing():
    """Test opinion parsing with a small sample"""
    print("🔍 Testing opinion parsing...")
    
    storage = CourtFinderStorage("real_data")
    file_path = Path("downloads/opinions-2024-12-31.csv.bz2")
    
    if not file_path.exists():
        print("❌ Opinion file not found")
        return
    
    try:
        # Test parsing 10 opinions
        print("Parsing 10 opinions...")
        result = import_opinions_html_aware(storage, file_path, limit=10)
        
        print(f"\nResult: {result}")
        
        if result['success']:
            print(f"✅ Successfully imported {result['imported_count']} opinions")
            print(f"⚠️  {result['error_count']} errors")
            
            # Show error details
            if result.get('error_details'):
                print("\nError details:")
                for error, count in result['error_details'].items():
                    print(f"  {error}: {count}")
                    
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_opinion_parsing()