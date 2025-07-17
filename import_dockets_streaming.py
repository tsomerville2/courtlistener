#!/usr/bin/env python3
"""
Streaming import of dockets from bz2 file
Processes the file in chunks to avoid memory issues
"""

import sys
import csv
import bz2
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.csv_parser import DocketCSVParser
from courtfinder.storage import CourtFinderStorage

def import_dockets_streaming():
    """Stream dockets import directly from bz2 file"""
    
    print("📥 STREAMING DOCKETS IMPORT")
    print("=" * 40)
    
    # Setup
    downloads_dir = Path("downloads")
    data_dir = Path("real_data")
    
    # File to import
    dockets_file = downloads_dir / "dockets-2024-12-31.csv.bz2"
    
    if not dockets_file.exists():
        print(f"❌ Dockets file not found: {dockets_file}")
        return False
    
    # Create storage
    storage = CourtFinderStorage(str(data_dir))
    
    print(f"📦 Processing {dockets_file.name} (streaming)...")
    
    # Stream directly from bz2 file
    imported_count = 0
    error_count = 0
    limit = 100  # Start with small limit
    
    try:
        with bz2.open(dockets_file, 'rt', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                if row_num > limit:
                    break
                    
                try:
                    # Clean up backticks
                    cleaned_row = {}
                    for key, value in row.items():
                        if isinstance(value, str) and value.startswith('`') and value.endswith('`'):
                            cleaned_value = value[1:-1]  # Remove backticks
                        else:
                            cleaned_value = value
                        cleaned_row[key] = cleaned_value
                    
                    # Parse row directly
                    docket = DocketCSVParser.parse_row(cleaned_row)
                    storage.save_docket(docket)
                    imported_count += 1
                    
                    if imported_count % 10 == 0:
                        print(f"  📊 Imported {imported_count} dockets...")
                        
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:
                        print(f"  ❌ Error processing row {row_num}: {e}")
                    continue
    
    except Exception as e:
        print(f"❌ Error reading dockets file: {e}")
        return False
    
    print(f"✅ Successfully imported {imported_count} dockets ({error_count} errors)")
    
    # Test search
    print(f"\n🔍 TESTING DOCKET SEARCH")
    print("-" * 30)
    
    # Check storage stats
    stats = storage.get_storage_stats()
    print(f"Total dockets in storage: {stats.get('dockets', {}).get('total_items', 0)}")
    
    return True

if __name__ == "__main__":
    success = import_dockets_streaming()
    if success:
        print("\n🎉 Dockets import completed!")
    else:
        print("\n❌ Dockets import failed!")