#!/usr/bin/env python3
"""
Test script to verify CourtFinder implementation
"""

import sys
import os
from datetime import datetime, date

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from courtfinder.models import (
    Court, Docket, OpinionCluster, Opinion, Citation, Person,
    PrecedentialStatus, OpinionType
)
from courtfinder.storage import CourtFinderStorage
from courtfinder.search import CourtFinderSearch, SearchQuery, SearchOperator
from courtfinder.csv_parser import BulkCSVParser
from courtfinder.api_client import CourtListenerAPIClient


def test_models():
    """Test domain models"""
    print("Testing domain models...")
    
    # Test Court
    court = Court(
        id=1,
        full_name="Supreme Court of the United States",
        short_name="SCOTUS",
        jurisdiction="Federal",
        position=1.0,
        citation_string="U.S."
    )
    
    print(f"Court: {court.full_name} ({court.jurisdiction})")
    print(f"Is active: {court.is_active()}")
    
    # Test Docket
    docket = Docket(
        id=1,
        court_id=1,
        case_name="Test v. Example",
        docket_number="20-1234",
        date_created=datetime.now(),
        date_modified=datetime.now(),
        source="test"
    )
    
    print(f"Docket: {docket.case_name} - {docket.docket_number}")
    print(f"Is active: {docket.is_active()}")
    
    # Test OpinionCluster
    cluster = OpinionCluster(
        id=1,
        docket_id=1,
        date_created=datetime.now(),
        date_modified=datetime.now(),
        case_name="Test v. Example",
        precedential_status=PrecedentialStatus.PUBLISHED
    )
    
    print(f"Cluster: {cluster.case_name}")
    print(f"Is published: {cluster.is_published()}")
    
    # Test Opinion
    opinion = Opinion(
        id=1,
        cluster_id=1,
        date_created=datetime.now(),
        date_modified=datetime.now(),
        type=OpinionType.LEAD,
        plain_text="This is a test opinion."
    )
    
    print(f"Opinion: {opinion.type.value}")
    print(f"Has text: {opinion.has_text()}")
    
    # Test Citation
    citation = Citation(
        cited_opinion_id=1,
        citing_opinion_id=2,
        depth=1,
        quoted=True
    )
    
    print(f"Citation: {citation.citing_opinion_id} -> {citation.cited_opinion_id}")
    
    # Test Person
    person = Person(
        id=1,
        date_created=datetime.now(),
        date_modified=datetime.now(),
        name_first="John",
        name_last="Smith"
    )
    
    print(f"Person: {person.get_full_name()}")
    print(f"Is deceased: {person.is_deceased()}")
    
    print("✓ Models working correctly")


def test_storage():
    """Test storage system"""
    print("\nTesting storage system...")
    
    # Initialize storage
    storage = CourtFinderStorage("test_data")
    
    # Create test data
    court = Court(
        id=1,
        full_name="Test Court",
        short_name="TC",
        jurisdiction="Test",
        position=1.0,
        citation_string="Test"
    )
    
    # Save and load
    storage.save_court(court)
    loaded_court = storage.get_court(1)
    
    assert loaded_court is not None
    assert loaded_court.full_name == "Test Court"
    
    print(f"Stored and loaded court: {loaded_court.full_name}")
    
    # Test statistics
    stats = storage.get_storage_stats()
    print(f"Storage stats: {stats['courts']['total_items']} courts")
    
    print("✓ Storage working correctly")


def test_search():
    """Test search functionality"""
    print("\nTesting search functionality...")
    
    # Initialize storage and search
    storage = CourtFinderStorage("test_data")
    search = CourtFinderSearch(storage)
    
    # Create test data
    court1 = Court(
        id=1,
        full_name="Supreme Court of the United States",
        short_name="SCOTUS",
        jurisdiction="Federal",
        position=1.0,
        citation_string="U.S."
    )
    
    court2 = Court(
        id=2,
        full_name="Court of Appeals",
        short_name="CA",
        jurisdiction="Federal",
        position=2.0,
        citation_string="F.3d"
    )
    
    storage.save_court(court1)
    storage.save_court(court2)
    
    # Test search
    results = search.find_court_by_name("Supreme")
    assert len(results) == 1
    assert results[0].full_name == "Supreme Court of the United States"
    
    print(f"Found {len(results)} courts matching 'Supreme'")
    
    # Test advanced search
    query = SearchQuery()
    query.add_filter('jurisdiction', SearchOperator.EQUALS, 'Federal')
    query.add_sort('position')
    
    result = search.search_courts(query)
    assert len(result.results) == 2
    assert result.results[0].position == 1.0
    
    print(f"Advanced search found {len(result.results)} federal courts")
    
    print("✓ Search working correctly")


def test_csv_parser():
    """Test CSV parser"""
    print("\nTesting CSV parser...")
    
    parser = BulkCSVParser()
    
    # Test supported data types
    data_types = parser.get_supported_data_types()
    expected_types = ['courts', 'dockets', 'opinion_clusters', 'opinions', 'citations', 'people']
    
    for dtype in expected_types:
        assert dtype in data_types
    
    print(f"Supported data types: {', '.join(data_types)}")
    
    print("✓ CSV parser working correctly")


def test_api_client():
    """Test API client (without making real requests)"""
    print("\nTesting API client...")
    
    # Initialize client without token
    client = CourtListenerAPIClient()
    
    # Test URL construction
    url = client._get_absolute_url('courts/')
    assert url == 'https://www.courtlistener.com/api/rest/v4/courts/'
    
    print(f"API base URL: {client.BASE_URL}")
    
    # Test bulk downloader
    from courtfinder.api_client import BulkDataDownloader
    downloader = BulkDataDownloader("test_downloads")
    
    files = downloader.list_available_files()
    assert len(files) > 0
    
    print(f"Available bulk data files: {len(files)}")
    
    print("✓ API client working correctly")


def main():
    """Run all tests"""
    print("CourtFinder Implementation Test")
    print("=" * 50)
    
    try:
        test_models()
        test_storage()
        test_search()
        test_csv_parser()
        test_api_client()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! CourtFinder implementation is working correctly.")
        print("\nNext steps:")
        print("1. Set up authentication token for CourtListener API")
        print("2. Download sample bulk data files")
        print("3. Import data using the CSV parser")
        print("4. Use the CLI for interactive searches")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()