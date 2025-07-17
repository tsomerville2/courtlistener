#!/usr/bin/env python3
"""
Debug the opinion import process to find the exact error
"""

import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import OpinionType

# Import necessary functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def debug_opinion_import():
    """Debug the opinion import process step by step"""
    
    print("🔍 DEBUGGING OPINION IMPORT")
    print("=" * 50)
    
    # Step 1: Test the HTML-aware parser
    print("\n1. Testing HTML-aware parser...")
    file_path = Path("downloads/opinions-2024-12-31.csv.bz2")
    
    if not file_path.exists():
        print("❌ Opinion file not found")
        return
    
    try:
        # Get just 3 valid rows for testing
        print("   Parsing 3 valid opinion rows...")
        valid_rows = OpinionCSVParser.parse_opinion_csv(file_path, limit=3)
        print(f"   ✅ Found {len(valid_rows)} valid rows")
        
        if not valid_rows:
            print("   ❌ No valid rows found")
            return
        
        # Step 2: Test row parsing
        print("\n2. Testing row parsing...")
        for i, row in enumerate(valid_rows):
            print(f"\n   --- Row {i+1} ---")
            print(f"   Raw ID: {row.get('id')}")
            print(f"   Raw Type: {row.get('type')}")
            print(f"   Raw Cluster ID: {row.get('cluster_id')}")
            
            try:
                # Test parsing this row
                opinion = parse_opinion_row(row)
                print(f"   ✅ Successfully parsed opinion {opinion.id}")
                print(f"      Opinion type: {opinion.type}")
                print(f"      Opinion type value: {opinion.type.value}")
                print(f"      Cluster ID: {opinion.cluster_id}")
                
                # Step 3: Test storage
                print(f"\n3. Testing storage for opinion {opinion.id}...")
                storage = CourtFinderStorage("real_data")
                
                try:
                    storage.save_opinion(opinion)
                    print(f"   ✅ Successfully saved opinion {opinion.id}")
                    
                    # Test retrieval
                    retrieved = storage.get_opinion(opinion.id)
                    if retrieved:
                        print(f"   ✅ Successfully retrieved opinion {opinion.id}")
                    else:
                        print(f"   ❌ Failed to retrieve opinion {opinion.id}")
                        
                except Exception as save_error:
                    print(f"   ❌ Storage error: {save_error}")
                    traceback.print_exc()
                    
            except Exception as parse_error:
                print(f"   ❌ Parse error: {parse_error}")
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ HTML parser error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_opinion_import()