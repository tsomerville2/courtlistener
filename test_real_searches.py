#!/usr/bin/env python3
"""
Test real searches on actual downloaded data
Be 100% honest about what we find vs what we don't find
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.main import CourtFinderCLI

def test_search_honestly():
    print("🔍 HONEST SEARCH TESTING")
    print("=" * 50)
    
    # Initialize CLI with test data
    cli = CourtFinderCLI("test_data")
    
    print("First, let's see what data we actually have loaded:")
    stats = cli.get_stats()
    print(f"📊 Storage stats:")
    for data_type, stat in stats['storage_stats'].items():
        if isinstance(stat, dict) and 'total_items' in stat:
            print(f"  {data_type}: {stat['total_items']} items")
    
    print("\n" + "=" * 50)
    print("TESTING REAL SEARCHES")
    print("=" * 50)
    
    # Test 1: Search for courts we saw in the data
    print("\n1. 🏛️ COURT SEARCHES")
    print("-" * 30)
    
    searches = [
        "Supreme Court",
        "North Carolina", 
        "Alaska",
        "Arizona",
        "Montana",
        "Missouri"
    ]
    
    for search_term in searches:
        try:
            results = cli.search_courts(search_term, limit=5)
            print(f"Search '{search_term}': {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                if hasattr(result, 'full_name'):
                    print(f"  {i}. {result.full_name}")
                else:
                    print(f"  {i}. {result}")
        except Exception as e:
            print(f"Search '{search_term}': ERROR - {e}")
    
    # Test 2: Search for cases we saw in dockets
    print("\n2. ⚖️ CASE SEARCHES")
    print("-" * 30)
    
    case_searches = [
        "United States v",
        "Dickson",
        "Marion",
        "Hunt",
        "Sayyad"
    ]
    
    for search_term in case_searches:
        try:
            results = cli.search_cases(search_term, limit=5)
            print(f"Search '{search_term}': {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                if hasattr(result, 'case_name'):
                    print(f"  {i}. {result.case_name}")
                else:
                    print(f"  {i}. {result}")
        except Exception as e:
            print(f"Search '{search_term}': ERROR - {e}")
    
    # Test 3: Search for opinions
    print("\n3. 📝 OPINION SEARCHES")
    print("-" * 30)
    
    opinion_searches = [
        "criminal",
        "contract",
        "patent",
        "copyright"
    ]
    
    for search_term in opinion_searches:
        try:
            results = cli.search_opinions(search_term, limit=5)
            print(f"Search '{search_term}': {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                if hasattr(result, 'case_name'):
                    print(f"  {i}. {result.case_name}")
                else:
                    print(f"  {i}. {result}")
        except Exception as e:
            print(f"Search '{search_term}': ERROR - {e}")
    
    # Test 4: Search for judges
    print("\n4. 👨‍⚖️ JUDGE SEARCHES")
    print("-" * 30)
    
    judge_searches = [
        "Wright",
        "Sellers",
        "Small",
        "Ryskamp"
    ]
    
    for search_term in judge_searches:
        try:
            results = cli.search_judges(search_term, limit=5)
            print(f"Search '{search_term}': {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                if hasattr(result, 'name'):
                    print(f"  {i}. {result.name}")
                else:
                    print(f"  {i}. {result}")
        except Exception as e:
            print(f"Search '{search_term}': ERROR - {e}")
    
    print("\n" + "=" * 50)
    print("HONEST ASSESSMENT")
    print("=" * 50)
    
    # Check what's actually in test_data
    test_data_path = Path("test_data")
    if test_data_path.exists():
        print(f"📁 Test data directory exists: {test_data_path}")
        for file in test_data_path.glob("**/*.json*"):
            print(f"  📄 {file}")
    else:
        print("❌ No test_data directory found")
    
    # Check what's in downloads
    downloads_path = Path("downloads")
    if downloads_path.exists():
        print(f"📁 Downloads directory exists: {downloads_path}")
        for file in downloads_path.glob("*.bz2"):
            size = file.stat().st_size
            print(f"  📄 {file.name} ({size:,} bytes)")
    else:
        print("❌ No downloads directory found")
    
    print("\n🎯 CONCLUSION:")
    print("The search results above show exactly what our current system returns.")
    print("If most searches return 0 results, it means:")
    print("1. We have the bulk data files but haven't imported them into our system")
    print("2. Our test_data only contains mock/sample data")
    print("3. We need to run the import process to load the real bulk data")

if __name__ == "__main__":
    test_search_honestly()