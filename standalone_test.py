#!/usr/bin/env python3
"""
Standalone test for opinion parsing
"""

import sys
import csv
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import OpinionType

def clean_value(value: str) -> str:
    """Remove backticks that FreeLaw wraps around all values"""
    if isinstance(value, str) and value.startswith('`') and value.endswith('`'):
        return value[1:-1]  # Remove first and last backtick
    return value

def parse_integer(value: str) -> Optional[int]:
    """Parse integer value"""
    if not value or value.strip() == '':
        return None
    
    value = clean_value(value).strip()
    if not value:
        return None
    
    try:
        return int(value)
    except ValueError:
        return None

def parse_boolean(value: str) -> bool:
    """Parse boolean value"""
    if not value or value.strip() == '':
        return False
    
    value = clean_value(value).strip().lower()
    return value in ['true', 't', '1', 'yes', 'y', 'f'] and value != 'f'

def parse_string(value: str) -> str:
    """Parse string value"""
    if not value:
        return ''
    
    return clean_value(value)

def parse_datetime(value: str) -> Optional[datetime]:
    """Parse FreeLaw datetime format"""
    if not value or value.strip() == '':
        return None
    
    value = clean_value(value).strip()
    if not value:
        return None
    
    try:
        # Remove timezone part if present
        if '+' in value:
            value = value.split('+')[0]
        elif value.endswith('Z'):
            value = value[:-1]
        
        # Try different datetime formats
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        return None
    except Exception:
        return None

def standalone_test():
    """Standalone test with manual opinion record"""
    print("🔍 Standalone test - processing one opinion record")
    
    # Manually create a test opinion record based on the CSV structure
    test_row = {
        'id': '`3447253`',
        'date_created': '`2016-07-05 20:18:57.164305+00`',
        'date_modified': '`2020-03-02 21:38:43.821906+00`',
        'author_str': '``',
        'per_curiam': '`f`',
        'joined_by_str': '``',
        'type': '`020lead`',
        'sha1': '`d224d72282754b8cda985d1e315f87fe5d3fbb27`',
        'page_count': '',
        'download_url': '',
        'local_path': '`/home/mlissner/columbia/opinions/kentucky/court_opinions/documents/713e36da3367181a.xml`',
        'plain_text': '``',
        'html': '`<p>Affirming.</p><p>Test content</p>`',
        'html_lawbox': '``',
        'html_columbia': '``',
        'html_anon_2020': '``',
        'xml_harvard': '``',
        'html_with_citations': '``',
        'extracted_by_ocr': '`f`',
        'author_id': '',
        'cluster_id': '`3092898`'
    }
    
    print(f"Raw row data:")
    print(f"  ID: {test_row['id']}")
    print(f"  Type: {test_row['type']}")
    print(f"  Cluster ID: {test_row['cluster_id']}")
    
    try:
        # Parse manually
        opinion_id = parse_integer(test_row.get('id', ''))
        cluster_id = parse_integer(test_row.get('cluster_id', ''))
        
        if opinion_id is None:
            print("❌ Missing required field: id")
            return
        
        # Parse date fields
        date_created = parse_datetime(test_row.get('date_created', ''))
        date_modified = parse_datetime(test_row.get('date_modified', ''))
        
        # Parse string fields
        author_str = parse_string(test_row.get('author_str', ''))
        joined_by_str = parse_string(test_row.get('joined_by_str', ''))
        opinion_type = parse_string(test_row.get('type', ''))
        sha1 = parse_string(test_row.get('sha1', ''))
        download_url = parse_string(test_row.get('download_url', ''))
        local_path = parse_string(test_row.get('local_path', ''))
        plain_text = parse_string(test_row.get('plain_text', ''))
        html = parse_string(test_row.get('html', ''))
        
        # Parse optional fields
        page_count = parse_integer(test_row.get('page_count', ''))
        per_curiam = parse_boolean(test_row.get('per_curiam', ''))
        extracted_by_ocr = parse_boolean(test_row.get('extracted_by_ocr', ''))
        
        # Handle missing opinion type
        if not opinion_type or not opinion_type.strip():
            opinion_type = '999unknown'
        
        # Map opinion type to enum
        type_mapping = {
            '010combined': OpinionType.COMBINED,
            '015unamimous': OpinionType.UNANIMOUS,
            '020lead': OpinionType.LEAD,
            '025plurality': OpinionType.PLURALITY,
            '030concurrence': OpinionType.CONCURRENCE,
            '035concurrenceinpart': OpinionType.CONCUR_IN_PART,
            '040dissent': OpinionType.DISSENT,
            '050addendum': OpinionType.ADDENDUM,
            '060remittitur': OpinionType.REMITTUR,
            '070rehearing': OpinionType.REHEARING,
            '080onthemerits': OpinionType.ON_THE_MERITS,
            '090onmotiontostrike': OpinionType.ON_MOTION_TO_STRIKE,
            '100trialcourt': OpinionType.TRIAL_COURT,
            '999unknown': OpinionType.UNKNOWN
        }
        
        opinion_type_enum = type_mapping.get(opinion_type, OpinionType.UNKNOWN)
        
        # Create Opinion object with cluster_id fallback
        if cluster_id is None:
            cluster_id = 0  # Use 0 as placeholder for corrupted data
        
        print(f"✅ Successfully parsed opinion {opinion_id}")
        print(f"   Type: {opinion_type_enum}")
        print(f"   Type value: {opinion_type_enum.value}")
        print(f"   Cluster ID: {cluster_id}")
        
        # Test storage
        storage = CourtFinderStorage("real_data")
        
        # Create Opinion object manually to avoid import issues
        from courtfinder.models import Opinion
        
        opinion = Opinion(
            id=opinion_id,
            cluster_id=cluster_id,
            date_created=date_created,
            date_modified=date_modified,
            type=opinion_type_enum,
            sha1=sha1,
            page_count=page_count,
            download_url=download_url,
            local_path=local_path,
            plain_text=plain_text,
            html=html,
            per_curiam=per_curiam,
            extracted_by_ocr=extracted_by_ocr
        )
        
        storage.save_opinion(opinion)
        print(f"✅ Successfully saved opinion {opinion.id}")
        
        # Test retrieval
        retrieved = storage.get_opinion(opinion.id)
        if retrieved:
            print(f"✅ Successfully retrieved opinion {opinion.id}")
        else:
            print(f"❌ Failed to retrieve opinion {opinion.id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    standalone_test()