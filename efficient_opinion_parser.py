#!/usr/bin/env python3
"""
Efficient opinion parser that handles multi-line HTML content
"""

import sys
import csv
import bz2
import io
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import OpinionType

# Import the parsing functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

class EfficientOpinionParser:
    """Efficient parser that reconstructs CSV rows from multi-line HTML content"""
    
    @staticmethod
    def parse_opinions_fast(file_path: Path, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Fast opinion parser that handles multi-line HTML content
        
        Args:
            file_path: Path to the opinion CSV file
            limit: Optional limit on number of rows to parse
            
        Returns:
            List of valid opinion row dictionaries
        """
        valid_rows = []
        total_processed = 0
        
        with bz2.open(file_path, 'rt', encoding='utf-8') as f:
            # Get header
            header_line = f.readline().strip()
            expected_columns = header_line.split(',')
            
            print(f"  📝 CSV has {len(expected_columns)} columns")
            
            # Process file line by line, building complete rows
            current_row_parts = []
            in_record = False
            
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n\r')
                
                # Check if this is the start of a new record
                if line.startswith('`'):
                    # If we were building a record, try to parse it
                    if in_record and current_row_parts:
                        complete_row = ''.join(current_row_parts)
                        parsed_row = EfficientOpinionParser.try_parse_row(complete_row, expected_columns)
                        if parsed_row:
                            valid_rows.append(parsed_row)
                            total_processed += 1
                            
                            if total_processed % 10 == 0:
                                print(f"  ✅ Found {total_processed} valid opinions so far...")
                            
                            # Check limit
                            if limit and total_processed >= limit:
                                break
                    
                    # Start new record
                    current_row_parts = [line]
                    in_record = True
                    
                elif in_record:
                    # This is a continuation of the current record
                    current_row_parts.append(line)
                
                # Progress update
                if line_num % 100000 == 0:
                    print(f"  📊 Processed {line_num} lines, found {total_processed} valid opinions")
            
            # Process the last record
            if in_record and current_row_parts:
                complete_row = ''.join(current_row_parts)
                parsed_row = EfficientOpinionParser.try_parse_row(complete_row, expected_columns)
                if parsed_row:
                    valid_rows.append(parsed_row)
                    total_processed += 1
        
        return valid_rows
    
    @staticmethod
    def try_parse_row(row_line: str, expected_columns: List[str]) -> Optional[Dict[str, str]]:
        """
        Try to parse a complete row line
        
        Args:
            row_line: Complete CSV row as a string
            expected_columns: List of expected column names
            
        Returns:
            Dictionary of parsed row data or None if invalid
        """
        try:
            # Use csv.reader with proper settings
            row_io = io.StringIO(row_line)
            csv_reader = csv.reader(
                row_io,
                quoting=csv.QUOTE_ALL,
                skipinitialspace=True
            )
            
            row_data = next(csv_reader)
            
            # Check if we have the right number of fields
            if len(row_data) != len(expected_columns):
                return None
                
            # Create dictionary
            row_dict = dict(zip(expected_columns, row_data))
            
            # Basic validation
            if EfficientOpinionParser.is_valid_opinion_row(row_dict):
                return row_dict
            
            return None
            
        except (csv.Error, StopIteration, UnicodeDecodeError, IndexError):
            return None
    
    @staticmethod
    def is_valid_opinion_row(row_dict: Dict[str, str]) -> bool:
        """Basic validation of opinion row"""
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
        
        return True

def test_efficient_parser():
    """Test the efficient parser"""
    print("🔍 Testing efficient opinion parser...")
    
    storage = CourtFinderStorage("real_data")
    file_path = Path("downloads/opinions-2024-12-31.csv.bz2")
    
    if not file_path.exists():
        print("❌ Opinion file not found")
        return
    
    try:
        # Test parsing 20 opinions
        print("Parsing 20 opinions...")
        valid_rows = EfficientOpinionParser.parse_opinions_fast(file_path, limit=20)
        
        print(f"\n✅ Found {len(valid_rows)} valid opinion rows")
        
        if not valid_rows:
            print("❌ No valid opinions found")
            return
        
        # Test processing the first few
        imported_count = 0
        error_count = 0
        
        for i, row in enumerate(valid_rows[:10]):
            try:
                # Parse the row
                opinion = parse_opinion_row(row)
                
                # Save to storage
                storage.save_opinion(opinion)
                
                imported_count += 1
                print(f"✅ Imported opinion {opinion.id} (type: {opinion.type})")
                
            except Exception as e:
                error_count += 1
                print(f"❌ Error processing opinion {row.get('id', 'unknown')}: {e}")
                
                if error_count <= 3:
                    import traceback
                    traceback.print_exc()
        
        print(f"\n📊 Final results: {imported_count} imported, {error_count} errors")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_efficient_parser()