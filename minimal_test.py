#!/usr/bin/env python3
"""
Minimal test to process just one opinion record
"""

import sys
import csv
import io
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import OpinionType

# Import the parsing functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def minimal_test():
    """Test with one manually reconstructed opinion record"""
    print("🔍 Minimal test - processing one opinion record")
    
    # Read the small CSV file and manually reconstruct the first record
    with open('test_opinions.csv', 'r', encoding='utf-8') as f:
        # Get header
        header_line = f.readline().strip()
        expected_columns = header_line.split(',')
        
        print(f"📝 CSV has {len(expected_columns)} columns")
        
        # Read all lines and reconstruct the first record
        lines = f.readlines()
        
        # Find the end of the first record by looking for a line that starts with backtick
        # or by finding the `, marker that would indicate the next field
        record_lines = []
        for i, line in enumerate(lines):
            line = line.rstrip('\n\r')
            record_lines.append(line)
            
            # Check if this completes the record by trying to parse it
            complete_record = ''.join(record_lines)
            
            print(f"Line {i+1}: {line[:50]}...")
            
            try:
                # Try to parse as CSV
                row_io = io.StringIO(complete_record)
                csv_reader = csv.reader(
                    row_io,
                    quoting=csv.QUOTE_ALL,
                    skipinitialspace=True
                )
                
                row_data = next(csv_reader)
                
                # Check if we have the right number of fields
                if len(row_data) == len(expected_columns):
                    print(f"✅ Successfully parsed record with {len(row_data)} fields")
                    
                    # Create dictionary
                    row_dict = dict(zip(expected_columns, row_data))
                    
                    print(f"Opinion ID: {row_dict.get('id')}")
                    print(f"Opinion Type: {row_dict.get('type')}")
                    print(f"Cluster ID: {row_dict.get('cluster_id')}")
                    
                    # Test parsing
                    try:
                        opinion = parse_opinion_row(row_dict)
                        print(f"✅ Successfully parsed opinion {opinion.id}")
                        print(f"   Type: {opinion.type}")
                        print(f"   Type value: {opinion.type.value}")
                        
                        # Test storage
                        storage = CourtFinderStorage("real_data")
                        storage.save_opinion(opinion)
                        print(f"✅ Successfully saved opinion {opinion.id}")
                        
                        # Test retrieval
                        retrieved = storage.get_opinion(opinion.id)
                        if retrieved:
                            print(f"✅ Successfully retrieved opinion {opinion.id}")
                        else:
                            print(f"❌ Failed to retrieve opinion {opinion.id}")
                        
                        break
                        
                    except Exception as e:
                        print(f"❌ Error processing opinion: {e}")
                        import traceback
                        traceback.print_exc()
                        break
                        
            except Exception as e:
                # Not a complete record yet, continue
                continue
        
        print(f"Complete record:\n{complete_record[:500]}...")

if __name__ == "__main__":
    minimal_test()