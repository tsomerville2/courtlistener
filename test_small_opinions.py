#!/usr/bin/env python3
"""
Test with small opinion file
"""

import sys
import csv
import io
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import OpinionType

# Import the parsing functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def parse_small_file():
    """Parse the small test file"""
    print("🔍 Testing with small opinion file...")
    
    file_path = Path("test_opinions.csv")
    if not file_path.exists():
        print("❌ Test file not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Get header
        header_line = f.readline().strip()
        expected_columns = header_line.split(',')
        
        print(f"📝 CSV has {len(expected_columns)} columns")
        print(f"📝 Columns: {expected_columns}")
        
        # Process lines to build complete rows
        current_row_parts = []
        in_record = False
        valid_rows = []
        
        for line_num, line in enumerate(f, 1):
            line = line.rstrip('\n\r')
            
            print(f"Line {line_num}: {line[:100]}...")
            
            # Check if this is the start of a new record
            if line.startswith('`'):
                print(f"  → New record starts")
                
                # If we were building a record, try to parse it
                if in_record and current_row_parts:
                    complete_row = ''.join(current_row_parts)
                    print(f"  → Parsing previous record: {complete_row[:100]}...")
                    
                    try:
                        row_io = io.StringIO(complete_row)
                        csv_reader = csv.reader(
                            row_io,
                            quoting=csv.QUOTE_ALL,
                            skipinitialspace=True
                        )
                        
                        row_data = next(csv_reader)
                        print(f"  → Parsed {len(row_data)} fields (expected {len(expected_columns)})")
                        
                        if len(row_data) == len(expected_columns):
                            row_dict = dict(zip(expected_columns, row_data))
                            print(f"  → Opinion ID: {row_dict.get('id')}")
                            print(f"  → Opinion Type: {row_dict.get('type')}")
                            valid_rows.append(row_dict)
                            
                    except Exception as e:
                        print(f"  → Parse error: {e}")
                
                # Start new record
                current_row_parts = [line]
                in_record = True
                
            elif in_record:
                # This is a continuation of the current record
                print(f"  → Continuation of current record")
                current_row_parts.append(line)
            
            # Stop after a few lines for testing
            if line_num > 50:
                break
        
        # Process the last record
        if in_record and current_row_parts:
            complete_row = ''.join(current_row_parts)
            print(f"Final record: {complete_row[:100]}...")
            
            try:
                row_io = io.StringIO(complete_row)
                csv_reader = csv.reader(
                    row_io,
                    quoting=csv.QUOTE_ALL,
                    skipinitialspace=True
                )
                
                row_data = next(csv_reader)
                print(f"Final parsed {len(row_data)} fields")
                
                if len(row_data) == len(expected_columns):
                    row_dict = dict(zip(expected_columns, row_data))
                    valid_rows.append(row_dict)
                    
            except Exception as e:
                print(f"Final parse error: {e}")
        
        print(f"\n✅ Found {len(valid_rows)} valid opinion rows")
        
        # Test parsing one opinion
        if valid_rows:
            print("\nTesting opinion parsing...")
            try:
                opinion = parse_opinion_row(valid_rows[0])
                print(f"✅ Successfully parsed opinion {opinion.id}")
                print(f"   Type: {opinion.type}")
                print(f"   Type value: {opinion.type.value}")
                
                # Test storage
                storage = CourtFinderStorage("real_data")
                storage.save_opinion(opinion)
                print(f"✅ Successfully saved opinion {opinion.id}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    parse_small_file()