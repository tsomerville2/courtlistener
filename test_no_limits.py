#!/usr/bin/env python3
"""
Test the import with no limits to see how much data we actually have
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage

# Import the fixed functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def test_data_volume():
    """Test to see how much data we actually have in each file"""
    
    downloads_dir = Path("downloads")
    
    files_to_check = [
        "dockets-2024-12-31.csv.bz2",
        "opinion-clusters-2024-12-31.csv.bz2", 
        "opinions-2024-12-31.csv.bz2",
        "citation-map-2025-07-02.csv.bz2"
    ]
    
    print("🔍 CHECKING DATA VOLUME IN EACH FILE")
    print("=" * 50)
    
    for filename in files_to_check:
        file_path = downloads_dir / filename
        
        if not file_path.exists():
            print(f"❌ {filename}: File not found")
            continue
            
        print(f"\n📁 {filename}")
        print("-" * 30)
        
        try:
            # Count total lines in the file (excluding header)
            import bz2
            with bz2.open(file_path, 'rt', encoding='utf-8') as f:
                header = f.readline()  # Skip header
                line_count = sum(1 for line in f)
                
            print(f"   📊 Total data lines: {line_count:,}")
            
            # For opinions, also check valid records
            if "opinions" in filename:
                print(f"   🔍 Checking valid opinion records...")
                valid_rows = OpinionCSVParser.parse_opinion_csv(file_path, limit=1000)  # Sample first 1000
                print(f"   ✅ Valid records in first 1000: {len(valid_rows)}")
                
                if len(valid_rows) > 0:
                    # Estimate total valid records
                    ratio = len(valid_rows) / 1000
                    estimated_total = int(line_count * ratio)
                    print(f"   📈 Estimated total valid opinions: {estimated_total:,}")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

def test_small_unlimited_import():
    """Test importing a small amount with no limits to verify it works"""
    
    print(f"\n🧪 TESTING SMALL UNLIMITED IMPORT")
    print("=" * 50)
    
    storage = CourtFinderStorage("test_data")
    
    # Test with citations first (should be fastest)
    file_path = Path("downloads/citation-map-2025-07-02.csv.bz2")
    
    if file_path.exists():
        print(f"📥 Testing citation import with no limits...")
        
        # Import first 5000 citations to test
        result = import_data_type(storage, file_path, "citations", parse_citation_row, storage.save_citation, 5000)
        
        if result['success']:
            print(f"✅ Successfully imported {result['imported_count']} citations")
            print(f"⚠️  {result['error_count']} errors")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    else:
        print("❌ Citation file not found")

if __name__ == "__main__":
    test_data_volume()
    test_small_unlimited_import()