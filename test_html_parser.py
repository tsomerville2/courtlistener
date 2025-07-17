#!/usr/bin/env python3
"""
Test the updated HTML-aware opinion parser
"""

import sys
import csv
import bz2
import io
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

class OpinionCSVParser:
    @staticmethod
    def parse_opinion_csv(file_path: Path, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Parse opinion CSV file with proper HTML handling"""
        valid_rows = []
        total_processed = 0
        
        # Use a different approach - scan for rows that start with backtick (valid IDs)
        with bz2.open(file_path, 'rt', encoding='utf-8') as f:
            # Get header
            header_line = f.readline().strip()
            expected_columns = header_line.split(',')
            
            print(f"  📝 CSV has {len(expected_columns)} columns")
            print(f"  📝 Expected columns: {expected_columns[:5]}...{expected_columns[-3:]}")
            
            # Read file in chunks and look for valid opinion rows
            line_count = 0
            
            for line in f:
                line_count += 1
                
                # Stop if we've processed enough
                if limit and total_processed >= limit:
                    break
                
                # Skip obviously corrupted lines that don't start with a backtick
                if not line.strip().startswith('`'):
                    continue
                
                # This might be a valid opinion row, try to parse it
                try:
                    # Use csv.reader with proper PostgreSQL-style settings
                    row_io = io.StringIO(line.strip())
                    csv_reader = csv.reader(
                        row_io,
                        quoting=csv.QUOTE_ALL,
                        skipinitialspace=True
                    )
                    
                    row_data = next(csv_reader)
                    
                    # Check if we have the right number of fields
                    if len(row_data) != len(expected_columns):
                        continue
                        
                    # Create dictionary
                    row_dict = dict(zip(expected_columns, row_data))
                    
                    # Validate that this looks like a valid opinion row
                    if OpinionCSVParser.is_valid_opinion_row(row_dict):
                        valid_rows.append(row_dict)
                        total_processed += 1
                        
                        if total_processed % 10 == 0:
                            print(f"  ✅ Found {total_processed} valid opinions so far...")
                            
                except (csv.Error, StopIteration, UnicodeDecodeError, IndexError):
                    # This row is corrupted, skip it
                    continue
                    
                # Periodic progress update
                if line_count % 10000 == 0:
                    print(f"  📊 Scanned {line_count} lines, found {total_processed} valid opinions")
        
        return valid_rows
    
    @staticmethod
    def is_valid_opinion_row(row_dict: Dict[str, str]) -> bool:
        """Validate that a row dictionary represents a valid opinion record"""
        # Check for required fields
        opinion_id = row_dict.get('id', '').strip()
        if not opinion_id:
            return False
        
        # Opinion IDs should be wrapped in backticks and be numeric
        if not (opinion_id.startswith('`') and opinion_id.endswith('`')):
            return False
            
        # Remove backticks and check if it's a valid integer
        clean_id = opinion_id[1:-1]
        if not clean_id.isdigit():
            return False
        
        # Check if we have a reasonable type field
        opinion_type = row_dict.get('type', '').strip()
        if opinion_type and opinion_type.startswith('`') and opinion_type.endswith('`'):
            clean_type = opinion_type[1:-1]
            # Should be a valid opinion type code
            if clean_type and not clean_type.startswith('<'):  # Not HTML
                return True
        
        return False

if __name__ == "__main__":
    # Test the parser
    file_path = Path('downloads/opinions-2024-12-31.csv.bz2')
    if file_path.exists():
        print('Testing HTML-aware opinion parser...')
        valid_rows = OpinionCSVParser.parse_opinion_csv(file_path, limit=100)
        print(f'Results: Found {len(valid_rows)} valid opinions')
        
        if valid_rows:
            print('\nSample valid rows:')
            for i, row in enumerate(valid_rows[:3]):
                print(f'  Row {i+1}:')
                print(f'    ID: {row.get("id")}')
                print(f'    Type: {row.get("type")}')
                print(f'    Cluster ID: {row.get("cluster_id")}')
    else:
        print('Opinion file not found')