#!/usr/bin/env python3
"""
Test the HTML-aware opinion parser with a small sample
"""

import sys
import bz2
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import Opinion, OpinionType

class FreeLawCSVParser:
    @staticmethod
    def clean_value(value: str) -> str:
        if isinstance(value, str) and value.startswith('`') and value.endswith('`'):
            return value[1:-1]
        return value
    
    @staticmethod
    def parse_integer(value: str) -> Optional[int]:
        if not value or value.strip() == '':
            return None
        value = FreeLawCSVParser.clean_value(value).strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None
    
    @staticmethod
    def parse_datetime(value: str):
        # Simplified for testing
        return None
    
    @staticmethod
    def parse_string(value: str) -> str:
        if not value:
            return ''
        return FreeLawCSVParser.clean_value(value)
    
    @staticmethod
    def parse_boolean(value: str) -> bool:
        if not value or value.strip() == '':
            return False
        value = FreeLawCSVParser.clean_value(value).strip().lower()
        return value in ['true', 't', '1', 'yes', 'y', 'f']

def test_opinion_parser():
    """Test the opinion parser with a small sample"""
    
    # Create test data with some valid rows (matching actual CSV format)
    test_data = [
        '`3447253`,`2016-07-05 20:18:57.164305+00`,`2020-03-02 21:38:43.821906+00`,``,`f`,``,`020lead`,`d224d72282754b8cda985d1e315f87fe5d3fbb27`,,,`/home/path.xml`,``,``,``,`<p>Valid HTML</p>`,``,``,`f`,``,`3092898`',
        '`10311486`,`2016-07-05 20:18:57.164305+00`,`2020-03-02 21:38:43.821906+00`,``,`f`,``,`100trialcourt`,`abc123hash`,,,`/home/path2.xml`,``,``,``,`<p>More HTML</p>`,``,``,`f`,``,`3092899`'
    ]
    
    header = 'id,date_created,date_modified,author_str,per_curiam,joined_by_str,type,sha1,page_count,download_url,local_path,plain_text,html,html_lawbox,html_columbia,html_anon_2020,xml_harvard,html_with_citations,extracted_by_ocr,author_id,cluster_id'
    
    import csv
    import io
    
    for i, row_data in enumerate(test_data):
        print(f"\n=== Testing Row {i+1} ===")
        print(f"Raw data: {row_data[:100]}...")
        
        try:
            # Parse using CSV
            row_io = io.StringIO(row_data)
            csv_reader = csv.DictReader(
                row_io,
                fieldnames=header.split(','),
                quoting=csv.QUOTE_ALL,
                skipinitialspace=True
            )
            
            row_dict = next(csv_reader)
            print(f"Parsed ID: {row_dict.get('id')}")
            print(f"Parsed Type: {row_dict.get('type')}")
            print(f"Parsed cluster_id: {row_dict.get('cluster_id')}")
            print(f"Dict keys: {list(row_dict.keys())}")
            print(f"Dict length: {len(row_dict)} vs expected: {len(header.split(','))}")
            
            # Test parsing
            opinion_id = FreeLawCSVParser.parse_integer(row_dict.get('id', ''))
            cluster_id = FreeLawCSVParser.parse_integer(row_dict.get('cluster_id', ''))
            opinion_type = FreeLawCSVParser.parse_string(row_dict.get('type', ''))
            
            print(f"Clean ID: {opinion_id}")
            print(f"Clean cluster_id: {cluster_id}")
            print(f"Clean type: {opinion_type}")
            
            # Test Opinion creation (simplified)
            if opinion_id and cluster_id:
                print("✅ Would create valid Opinion object")
            else:
                print("❌ Missing required fields")
            
        except Exception as e:
            print(f"❌ Error parsing row: {e}")

if __name__ == "__main__":
    test_opinion_parser()