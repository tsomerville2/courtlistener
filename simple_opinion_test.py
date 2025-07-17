#!/usr/bin/env python3
"""
Simple test - create a manual opinion and test the import
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage
from courtfinder.models import OpinionType

# Import necessary functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def simple_test():
    """Simple test - manually create an opinion row and test import"""
    
    print("🔍 SIMPLE OPINION IMPORT TEST")
    print("=" * 40)
    
    # Create a manual opinion row (based on what we know works)
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
        'local_path': '`/home/mlissner/columbia/opinions/test.xml`',
        'plain_text': '',
        'html': '`<p>Test opinion content</p>`',
        'html_lawbox': '',
        'html_columbia': '',
        'html_anon_2020': '',
        'xml_harvard': '',
        'html_with_citations': '',
        'extracted_by_ocr': '`f`',
        'author_id': '',
        'cluster_id': '`3092898`'
    }
    
    print("1. Testing opinion row parsing...")
    print(f"   Raw ID: {test_row['id']}")
    print(f"   Raw Type: {test_row['type']}")
    print(f"   Raw Cluster ID: {test_row['cluster_id']}")
    
    try:
        # Test parsing
        opinion = parse_opinion_row(test_row)
        print(f"   ✅ Successfully parsed opinion {opinion.id}")
        print(f"      Opinion type: {opinion.type}")
        print(f"      Opinion type value: {opinion.type.value}")
        print(f"      Cluster ID: {opinion.cluster_id}")
        
        # Test storage
        print(f"\n2. Testing storage...")
        storage = CourtFinderStorage("real_data")
        
        try:
            storage.save_opinion(opinion)
            print(f"   ✅ Successfully saved opinion {opinion.id}")
            
            # Test retrieval
            retrieved = storage.get_opinion(opinion.id)
            if retrieved:
                print(f"   ✅ Successfully retrieved opinion {opinion.id}")
                print(f"      Retrieved type: {retrieved.type}")
            else:
                print(f"   ❌ Failed to retrieve opinion {opinion.id}")
                
        except Exception as save_error:
            print(f"   ❌ Storage error: {save_error}")
            import traceback
            traceback.print_exc()
            
    except Exception as parse_error:
        print(f"   ❌ Parse error: {parse_error}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()