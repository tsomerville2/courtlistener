#!/usr/bin/env python3
"""
Test to verify we're back to a working state
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.storage import CourtFinderStorage

# Import the parsing functions
exec(open('import_ALL_freelaw_data_FIXED.py').read())

def test_working_state():
    """Test that we can import a small amount of data successfully"""
    
    print("🔍 TESTING WORKING STATE")
    print("=" * 30)
    
    storage = CourtFinderStorage("real_data")
    
    # Test dockets import with small limit
    dockets_file = Path("downloads/dockets-2024-12-31.csv.bz2")
    if dockets_file.exists():
        print("📥 Testing dockets import...")
        result = import_data_type(storage, dockets_file, "dockets", parse_docket_row, storage.save_docket, 100)
        
        if result['success']:
            print(f"✅ Successfully imported {result['imported_count']} dockets")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Test opinion clusters import with small limit
    clusters_file = Path("downloads/opinion-clusters-2024-12-31.csv.bz2")
    if clusters_file.exists():
        print("📥 Testing opinion clusters import...")
        result = import_data_type(storage, clusters_file, "opinion_clusters", parse_opinion_cluster_row, storage.save_opinion_cluster, 100)
        
        if result['success']:
            print(f"✅ Successfully imported {result['imported_count']} opinion clusters")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Test citations import with small limit
    citations_file = Path("downloads/citation-map-2025-07-02.csv.bz2")
    if citations_file.exists():
        print("📥 Testing citations import...")
        result = import_data_type(storage, citations_file, "citations", parse_citation_row, storage.save_citation, 100)
        
        if result['success']:
            print(f"✅ Successfully imported {result['imported_count']} citations")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Test opinions import with small limit
    opinions_file = Path("downloads/opinions-2024-12-31.csv.bz2")
    if opinions_file.exists():
        print("📥 Testing opinions import...")
        result = import_opinions_html_aware(storage, opinions_file, 10)
        
        if result['success']:
            print(f"✅ Successfully imported {result['imported_count']} opinions")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Show final stats
    print("\n📊 Storage stats:")
    stats = storage.get_storage_stats()
    for data_type, stat in stats.items():
        if isinstance(stat, dict) and 'total_items' in stat:
            print(f"  {data_type}: {stat['total_items']:,} items")

if __name__ == "__main__":
    test_working_state()