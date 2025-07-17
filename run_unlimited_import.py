#!/usr/bin/env python3
"""
Run the unlimited import with better progress reporting
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage

def run_unlimited_import():
    """Run the unlimited import"""
    
    print("🚀 RUNNING UNLIMITED IMPORT")
    print("=" * 50)
    print("This will import ALL data from the FreeLaw bulk files")
    print("Expected data volumes:")
    print("  - Citations: ~70 million records")
    print("  - Dockets: ~8 million records") 
    print("  - Opinion Clusters: ~2+ million records")
    print("  - Opinions: ~1+ million records")
    print("=" * 50)
    
    # Ask user to confirm
    response = input("\nThis will take several hours. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Import cancelled.")
        return
    
    print("\n🏁 Starting unlimited import...")
    start_time = time.time()
    
    # Import the main function
    exec(open('import_ALL_freelaw_data_FIXED.py').read())
    
    # Run the main import
    success = main()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n⏱️  Total import time: {duration:.2f} seconds ({duration/60:.1f} minutes)")
    
    if success:
        print("🎉 UNLIMITED IMPORT COMPLETE!")
        
        # Show final storage stats
        storage = CourtFinderStorage("real_data")
        stats = storage.get_storage_stats()
        
        print(f"\n📊 FINAL STORAGE STATISTICS:")
        print("-" * 40)
        for data_type, stat in stats.items():
            if isinstance(stat, dict) and 'total_items' in stat:
                print(f"  {data_type}: {stat['total_items']:,} items")
        
    else:
        print("❌ Import failed!")

if __name__ == "__main__":
    run_unlimited_import()