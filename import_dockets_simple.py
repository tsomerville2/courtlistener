#!/usr/bin/env python3
"""
Simple script to import dockets only from the bz2 file
Uses the same approach that worked for courts
"""

import sys
import csv
import bz2
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.csv_parser import BulkCSVParser
from courtfinder.storage import CourtFinderStorage

def import_dockets_simple():
    """Simple dockets import"""
    
    print("📥 IMPORTING DOCKETS ONLY")
    print("=" * 40)
    
    # Setup
    downloads_dir = Path("downloads")
    data_dir = Path("real_data")
    
    # File to import
    dockets_file = downloads_dir / "dockets-2024-12-31.csv.bz2"
    
    if not dockets_file.exists():
        print(f"❌ Dockets file not found: {dockets_file}")
        return False
    
    # Create parser and storage
    parser = BulkCSVParser()
    storage = CourtFinderStorage(str(data_dir))
    
    print(f"📦 Processing {dockets_file.name}...")
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        
        # Decompress bz2 to temporary CSV file
        with bz2.open(dockets_file, 'rt', encoding='utf-8') as bz2_file:
            temp_file.write(bz2_file.read())
    
    print(f"📄 Decompressed to temporary file")
    
    # Parse and import
    imported_count = 0
    error_count = 0
    limit = 100  # Start with small limit
    
    try:
        for docket in parser.parse_file(temp_path, 'dockets', limit=limit):
            try:
                storage.save_docket(docket)
                imported_count += 1
                
                if imported_count % 10 == 0:
                    print(f"  📊 Imported {imported_count} dockets...")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 3:
                    print(f"  ❌ Error saving docket: {e}")
                continue
    
    except Exception as e:
        print(f"❌ Error parsing dockets: {e}")
        return False
    
    finally:
        # Clean up
        temp_path.unlink()
    
    print(f"✅ Successfully imported {imported_count} dockets ({error_count} errors)")
    
    # Test search
    print(f"\n🔍 TESTING DOCKET SEARCH")
    print("-" * 30)
    
    # Check storage stats
    stats = storage.get_storage_stats()
    print(f"Total dockets in storage: {stats.get('dockets', {}).get('total_items', 0)}")
    
    return True

if __name__ == "__main__":
    success = import_dockets_simple()
    if success:
        print("\n🎉 Dockets import completed!")
    else:
        print("\n❌ Dockets import failed!")