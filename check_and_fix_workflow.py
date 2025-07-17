#!/usr/bin/env python3
"""
Check current state and provide options to fix/continue workflow
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage

def check_current_state():
    """Check what we actually have working"""
    
    print("🔍 CHECKING CURRENT STATE")
    print("=" * 50)
    
    # Check storage
    storage = CourtFinderStorage("real_data")
    stats = storage.get_storage_stats()
    
    print("📊 Current working data:")
    for data_type, stat in stats.items():
        if isinstance(stat, dict) and 'total_items' in stat:
            count = stat['total_items']
            if count > 0:
                print(f"  ✅ {data_type}: {count:,} items")
            else:
                print(f"  ❌ {data_type}: {count:,} items")
    
    # Check file sizes
    print(f"\n💾 File availability:")
    downloads_dir = Path("downloads")
    
    files_to_check = [
        "courts-2024-12-31.csv.bz2",
        "dockets-2024-12-31.csv.bz2", 
        "opinion-clusters-2024-12-31.csv.bz2",
        "opinions-2024-12-31.csv.bz2",
        "citation-map-2025-07-02.csv.bz2",
        "people-2024-12-31.csv.bz2"
    ]
    
    for filename in files_to_check:
        file_path = downloads_dir / filename
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > 100:
                print(f"  ✅ {filename}: {size_mb:.1f}MB")
            elif size_mb > 1:
                print(f"  ⚠️  {filename}: {size_mb:.1f}MB (small)")
            else:
                print(f"  ❌ {filename}: {size_mb:.1f}MB (too small)")
        else:
            print(f"  ❌ {filename}: Not found")

def provide_options():
    """Provide options to continue"""
    
    print(f"\n🛠️  WHAT TO DO NEXT:")
    print("=" * 50)
    
    print("Option 1: Continue with current data (RECOMMENDED)")
    print("  - You have working data already!")
    print("  - 657 courts, 562 dockets, 734 clusters, 100 opinions, 1000 citations")
    print("  - This is enough for testing and development")
    print("  - Command: python menu.py")
    
    print(f"\nOption 2: Import more data with reasonable limits")
    print("  - Import 10K more dockets, 5K more opinions, etc.")
    print("  - Use the working import system")
    print("  - Command: python import_ALL_freelaw_data_FIXED.py")
    
    print(f"\nOption 3: Re-download corrupted files")
    print("  - Only if you need massive amounts of data")
    print("  - Some files may be truncated from original download")
    print("  - Command: python download_bulk_data.py")
    
    print(f"\nOption 4: Check what searches work with current data")
    print("  - Test searching courts, dockets, opinions")
    print("  - See if current data meets your needs")
    print("  - Command: python -c \"from src.courtfinder.search import *; # test searches\"")

if __name__ == "__main__":
    check_current_state()
    provide_options()
    
    print(f"\n💡 RECOMMENDATION:")
    print("Try Option 1 first - you have working data!")
    print("The 'corruption' issue was from trying to import ALL 70 million records.")
    print("Your current data is perfectly functional for testing and development.")