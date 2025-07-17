#!/usr/bin/env python3
"""
Setup script for CourtFinder test data
Creates sample data files and initializes storage structure
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.domain.test_data import TestDataFactory
from src.storage.file_storage import FileStorage
from src.domain.services import DataParsingService, RecordValidationService


def setup_directories():
    """Create necessary directories"""
    directories = [
        "data",
        "data/raw",
        "data/parsed",
        "data/datasets",
        "data/records",
        "data/events"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")


def create_sample_data_files():
    """Create sample data files"""
    # Create main test data file
    test_file = "data/sample_court_data.txt"
    TestDataFactory.write_test_data_file(test_file)
    print(f"Created test data file: {test_file}")
    
    # Create additional sample files
    additional_lines = [
        "rec_004\t2021-04-01T12:00:00Z\t2021-04-01T12:00:00Z\t2021-04-01\tCV-2021-004\tCIV-004\tfdc\tU.S. District Court for the District of Columbia\tFederal\tTech Corp vs Innovation LLC\tIntellectual Property\tActive\tTech Corp\tInnovation LLC\tTech Legal Group\tInnovation Lawyers\tJudge Anderson\tPatent dispute case\tpatent,technology,IP\tIntellectual property dispute\thttps://example.com/case/004",
        "rec_005\t2021-05-01T15:30:00Z\t2021-05-01T15:30:00Z\t2021-05-01\tCR-2021-005\tCRIM-005\tsdny\tU.S. District Court for the Southern District of New York\tFederal\tUnited States vs Defendant\tCriminal\tClosed\tUnited States\tJohn Defendant\tUS Attorney Office\tDefense Attorney\tJudge Roberts\tCriminal case\tcriminal,federal\tCriminal prosecution case\thttps://example.com/case/005"
    ]
    
    additional_file = "data/additional_court_data.txt"
    with open(additional_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(additional_lines))
    print(f"Created additional data file: {additional_file}")


def initialize_storage_and_records():
    """Initialize storage system and create sample records"""
    storage = FileStorage("data")
    
    # Create and save sample dataset
    dataset = TestDataFactory.create_sample_bulk_dataset()
    storage.save_dataset(dataset)
    print(f"Created sample dataset: {dataset.dataset_id}")
    
    # Parse and save sample records
    sample_records = TestDataFactory.create_sample_court_records()
    
    # Enrich records with validation and cleaning
    enriched_records = []
    for record in sample_records:
        enriched = RecordValidationService.validate_and_enrich_record(record)
        enriched_records.append(enriched)
    
    # Save records to storage
    storage.save_records_batch(enriched_records)
    print(f"Created {len(enriched_records)} sample court records")
    
    # Parse additional data from files
    data_files = ["data/sample_court_data.txt", "data/additional_court_data.txt"]
    all_parsed_records = []
    
    for data_file in data_files:
        if os.path.exists(data_file):
            print(f"Parsing data file: {data_file}")
            parsed_records = list(DataParsingService.parse_raw_data_file(data_file))
            
            # Validate and enrich
            for record in parsed_records:
                enriched = RecordValidationService.validate_and_enrich_record(record)
                all_parsed_records.append(enriched)
    
    # Save all parsed records
    if all_parsed_records:
        storage.save_records_batch(all_parsed_records)
        print(f"Parsed and saved {len(all_parsed_records)} records from data files")
    
    # Display storage stats
    stats = storage.get_storage_stats()
    print(f"\\nStorage Statistics:")
    print(f"  Total datasets: {stats['total_datasets']}")
    print(f"  Total records: {stats['total_records']}")
    print(f"  Storage path: {stats['storage_path']}")
    print(f"  Disk usage: {stats['disk_usage']} bytes")


def demonstrate_search_functionality():
    """Demonstrate search functionality"""
    storage = FileStorage("data")
    
    print("\\n=== Search Functionality Demo ===")
    
    # Test various search queries
    from src.domain.value_objects import QueryParams, QueryOperator
    
    queries = [
        QueryParams(field="jurisdiction", value="Federal", operator=QueryOperator.EQUALS),
        QueryParams(field="case_type", value="Civil", operator=QueryOperator.EQUALS),
        QueryParams(field="court_name", value="District Court", operator=QueryOperator.CONTAINS),
        QueryParams(field="case_number", value="CV", operator=QueryOperator.CONTAINS),
    ]
    
    for query in queries:
        results = list(storage.search_records(query, limit=5))
        print(f"\\nQuery: {query.field} {query.operator.value} '{query.value}'")
        print(f"Results: {len(results)} records found")
        
        for record in results[:3]:  # Show first 3 results
            print(f"  - {record.case_metadata.case_number}: {record.court_identifier.court_name}")


def main():
    """Main setup function"""
    print("Setting up CourtFinder test data...")
    
    try:
        # 1. Setup directories
        setup_directories()
        
        # 2. Create sample data files
        create_sample_data_files()
        
        # 3. Initialize storage and records
        initialize_storage_and_records()
        
        # 4. Demonstrate search functionality
        demonstrate_search_functionality()
        
        print("\\n✅ Test data setup complete!")
        print("\\nYou can now:")
        print("  - Run tests: python -m pytest tests/test_domain_models.py -v")
        print("  - Explore data: python -c \"from src.storage.file_storage import FileStorage; s=FileStorage(); print(s.get_storage_stats())\"")
        print("  - Search records: python -c \"from src.storage.file_storage import FileStorage; from src.domain.value_objects import QueryParams; s=FileStorage(); print(list(s.search_records(QueryParams('jurisdiction', 'Federal'))))\"")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()