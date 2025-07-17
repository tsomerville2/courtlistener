#!/usr/bin/env python3
"""
Quick test - just import 5 opinions to prove it works
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import OpinionType

# Import just the parsing functions we need
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def quick_test():
    """Quick test - just try to import 5 opinions"""
    storage = CourtFinderStorage("real_data")
    file_path = Path("downloads/opinions-2024-12-31.csv.bz2")
    
    if not file_path.exists():
        print("Opinion file not found")
        return
    
    print("🔍 Quick test - finding 5 valid opinions...")
    
    # Get 5 valid opinion rows
    valid_rows = OpinionCSVParser.parse_opinion_csv(file_path, limit=5)
    print(f"Found {len(valid_rows)} valid opinion rows")
    
    if not valid_rows:
        print("No valid opinions found")
        return
    
    # Try to parse the first one
    for i, row in enumerate(valid_rows):
        print(f"\n--- Testing Opinion {i+1} ---")
        print(f"ID: {row.get('id')}")
        print(f"Type: {row.get('type')}")
        print(f"Cluster ID: {row.get('cluster_id')}")
        
        try:
            opinion = parse_opinion_row(row)
            print(f"✅ Successfully parsed opinion {opinion.id}")
            print(f"   Opinion type: {opinion.type}")
            print(f"   Cluster ID: {opinion.cluster_id}")
            
            # Try to save it
            storage.save_opinion(opinion)
            print(f"✅ Successfully saved opinion {opinion.id}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    quick_test()