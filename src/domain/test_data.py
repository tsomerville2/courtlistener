"""
Test data structures for development and testing
"""
from datetime import datetime
from typing import List, Dict, Any
import uuid

from .aggregates import BulkDataSet, CourtRecord
from .value_objects import (
    DataFile, DataFileStatus, CourtIdentifier, CaseMetadata,
    QueryParams, QueryOperator
)


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_sample_bulk_dataset() -> BulkDataSet:
        """Create a sample bulk dataset for testing"""
        dataset_id = "test_dataset_001"
        
        # Create sample data files
        data_files = [
            DataFile(
                path="/Users/t/clients/mercola/courtfinder/data/sample_court_data.txt",
                size=1024000,
                status=DataFileStatus.DOWNLOADED
            ),
            DataFile(
                path="/Users/t/clients/mercola/courtfinder/data/sample_court_data_2.txt",
                size=2048000,
                status=DataFileStatus.PARSED
            )
        ]
        
        dataset = BulkDataSet(
            dataset_id=dataset_id,
            data_files=data_files,
            download_url="https://freelaw.org/bulk-data/sample.zip",
            total_size=3072000
        )
        
        return dataset
    
    @staticmethod
    def create_sample_court_records() -> List[CourtRecord]:
        """Create sample court records for testing"""
        records = []
        
        # Record 1: Clean case with all fields
        court_id_1 = CourtIdentifier(
            jurisdiction="Federal",
            court_name="U.S. District Court for the Northern District of California",
            court_code="cand"
        )
        
        case_meta_1 = CaseMetadata(
            case_number="3:21-cv-00123",
            filing_date="2021-01-15",
            parties="Smith vs Johnson",
            case_type="Civil",
            status="Active"
        )
        
        record_1 = CourtRecord(
            record_id="rec_001",
            court_identifier=court_id_1,
            case_metadata=case_meta_1,
            column_data=TestDataFactory.create_sample_columns_clean()
        )
        
        records.append(record_1)
        
        # Record 2: Case with problematic columns 12-18
        court_id_2 = CourtIdentifier(
            jurisdiction="State",
            court_name="Superior Court of California, County of Los Angeles",
            court_code="lasc"
        )
        
        case_meta_2 = CaseMetadata(
            case_number="BC123456",
            filing_date="2021-02-20",
            parties="Doe vs Roe",
            case_type="Personal Injury",
            status="Pending"
        )
        
        record_2 = CourtRecord(
            record_id="rec_002",
            court_identifier=court_id_2,
            case_metadata=case_meta_2,
            column_data=TestDataFactory.create_sample_columns_with_problems()
        )
        
        records.append(record_2)
        
        # Record 3: Minimal case
        court_id_3 = CourtIdentifier(
            jurisdiction="Federal",
            court_name="U.S. Court of Appeals for the Ninth Circuit",
            court_code="ca9"
        )
        
        case_meta_3 = CaseMetadata(
            case_number="21-1234",
            case_type="Appeal"
        )
        
        record_3 = CourtRecord(
            record_id="rec_003",
            court_identifier=court_id_3,
            case_metadata=case_meta_3,
            column_data=TestDataFactory.create_sample_columns_minimal()
        )
        
        records.append(record_3)
        
        return records
    
    @staticmethod
    def create_sample_columns_clean() -> List[str]:
        """Create clean sample column data"""
        return [
            "rec_001",                           # 0: id
            "2021-01-15T10:00:00Z",             # 1: date_created
            "2021-01-15T10:00:00Z",             # 2: date_modified
            "2021-01-15",                       # 3: date_filed
            "3:21-cv-00123",                    # 4: case_number
            "CV-123",                           # 5: docket_number
            "cand",                             # 6: court_id
            "U.S. District Court for the Northern District of California",  # 7: court_name
            "Federal",                          # 8: jurisdiction
            "Smith vs Johnson",                 # 9: case_name
            "Civil",                            # 10: case_type
            "Active",                           # 11: status
            "John Smith",                       # 12: plaintiff (problematic)
            "Jane Johnson",                     # 13: defendant (problematic)
            "Smith & Associates",               # 14: attorney_plaintiff (problematic)
            "Johnson Law Firm",                 # 15: attorney_defendant (problematic)
            "Judge Williams",                   # 16: judge (problematic)
            "Contract dispute case",            # 17: notes (problematic)
            "contract,dispute,commercial",      # 18: tags (problematic)
            "Full case description here",       # 19: description
            "https://example.com/case/123"      # 20: file_url
        ]
    
    @staticmethod
    def create_sample_columns_with_problems() -> List[str]:
        """Create sample column data with problematic characters in columns 12-18"""
        return [
            "rec_002",                           # 0: id
            "2021-02-20T14:30:00Z",             # 1: date_created
            "2021-02-20T14:30:00Z",             # 2: date_modified
            "2021-02-20",                       # 3: date_filed
            "BC123456",                         # 4: case_number
            "PI-456",                           # 5: docket_number
            "lasc",                             # 6: court_id
            "Superior Court of California, County of Los Angeles",  # 7: court_name
            "State",                            # 8: jurisdiction
            "Doe vs Roe",                       # 9: case_name
            "Personal Injury",                  # 10: case_type
            "Pending",                          # 11: status
            "John\x00Doe\n\tExtra chars",       # 12: plaintiff (with null bytes and control chars)
            "Jane\r\nRoe   \x01\x02",           # 13: defendant (with control chars)
            "  Law Firm\x00\x03\x04  ",         # 14: attorney_plaintiff (with nulls and whitespace)
            "Attorney\x05\x06Name\x07",         # 15: attorney_defendant (with control chars)
            "Judge\x08\x09Smith\x0A",           # 16: judge (with control chars)
            "Case\x00notes\x0B\x0C with problems",  # 17: notes (with null bytes)
            "injury,\x0D\x0Epersonal\x0F",      # 18: tags (with control chars)
            "Full case description here",       # 19: description
            "https://example.com/case/456"      # 20: file_url
        ]
    
    @staticmethod
    def create_sample_columns_minimal() -> List[str]:
        """Create minimal sample column data"""
        return [
            "rec_003",                           # 0: id
            "2021-03-01T09:00:00Z",             # 1: date_created
            "2021-03-01T09:00:00Z",             # 2: date_modified
            "2021-03-01",                       # 3: date_filed
            "21-1234",                          # 4: case_number
            "APP-789",                          # 5: docket_number
            "ca9",                              # 6: court_id
            "U.S. Court of Appeals for the Ninth Circuit",  # 7: court_name
            "Federal",                          # 8: jurisdiction
            "Appeal Case",                      # 9: case_name
            "Appeal",                           # 10: case_type
            "Closed",                           # 11: status
            "",                                 # 12: plaintiff (empty)
            "",                                 # 13: defendant (empty)
            "",                                 # 14: attorney_plaintiff (empty)
            "",                                 # 15: attorney_defendant (empty)
            "",                                 # 16: judge (empty)
            "",                                 # 17: notes (empty)
            "",                                 # 18: tags (empty)
            "Appeal case description",          # 19: description
            "https://example.com/case/789"      # 20: file_url
        ]
    
    @staticmethod
    def create_sample_raw_data_lines() -> List[str]:
        """Create sample raw data lines as they would appear in a file"""
        return [
            "\t".join(TestDataFactory.create_sample_columns_clean()),
            "\t".join(TestDataFactory.create_sample_columns_with_problems()),
            "\t".join(TestDataFactory.create_sample_columns_minimal()),
        ]
    
    @staticmethod
    def create_sample_query_params() -> List[QueryParams]:
        """Create sample query parameters for testing"""
        return [
            QueryParams(
                field="case_number",
                value="3:21-cv-00123",
                operator=QueryOperator.EQUALS
            ),
            QueryParams(
                field="jurisdiction",
                value="Federal",
                operator=QueryOperator.EQUALS
            ),
            QueryParams(
                field="case_name",
                value="Smith",
                operator=QueryOperator.CONTAINS
            ),
            QueryParams(
                field="case_type",
                value="Civil",
                operator=QueryOperator.EQUALS
            ),
            QueryParams(
                field="court_name",
                value="District Court",
                operator=QueryOperator.CONTAINS
            ),
            QueryParams(
                field="parties",
                value="vs",
                operator=QueryOperator.CONTAINS
            )
        ]
    
    @staticmethod
    def create_test_file_content() -> str:
        """Create test file content with problematic columns"""
        lines = TestDataFactory.create_sample_raw_data_lines()
        return "\n".join(lines)
    
    @staticmethod
    def write_test_data_file(file_path: str) -> None:
        """Write test data to file"""
        content = TestDataFactory.create_test_file_content()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def create_dataset_with_problems() -> BulkDataSet:
        """Create a dataset with various problems for testing error handling"""
        dataset_id = "problematic_dataset"
        
        data_files = [
            DataFile(
                path="/nonexistent/path/file1.txt",
                size=None,
                status=DataFileStatus.ERROR,
                error_message="File not found"
            ),
            DataFile(
                path="/Users/t/clients/mercola/courtfinder/data/empty_file.txt",
                size=0,
                status=DataFileStatus.DOWNLOADED
            ),
            DataFile(
                path="/Users/t/clients/mercola/courtfinder/data/large_file.txt",
                size=2000000000,  # 2GB - too large
                status=DataFileStatus.DOWNLOADED
            )
        ]
        
        dataset = BulkDataSet(
            dataset_id=dataset_id,
            data_files=data_files,
            download_url="https://freelaw.org/bulk-data/problematic.zip",
            total_size=2000000000
        )
        
        return dataset


# Sample field mappings for different data formats
SAMPLE_FIELD_MAPPINGS = {
    "standard": {
        0: 'id',
        1: 'date_created',
        2: 'date_modified',
        3: 'date_filed',
        4: 'case_number',
        5: 'docket_number',
        6: 'court_id',
        7: 'court_name',
        8: 'jurisdiction',
        9: 'case_name',
        10: 'case_type',
        11: 'status',
        12: 'plaintiff',
        13: 'defendant',
        14: 'attorney_plaintiff',
        15: 'attorney_defendant',
        16: 'judge',
        17: 'notes',
        18: 'tags',
        19: 'description',
        20: 'file_url'
    },
    "minimal": {
        0: 'id',
        4: 'case_number',
        7: 'court_name',
        8: 'jurisdiction',
        9: 'case_name',
        10: 'case_type'
    },
    "custom": {
        0: 'record_id',
        1: 'case_id',
        2: 'court_code',
        3: 'filing_date',
        4: 'case_title',
        5: 'case_status'
    }
}


# Sample configuration for different data sources
SAMPLE_DATA_SOURCES = {
    "freelaw_bulk": {
        "url": "https://freelaw.org/bulk-data/sample.zip",
        "delimiter": "\t",
        "encoding": "utf-8",
        "field_mapping": SAMPLE_FIELD_MAPPINGS["standard"],
        "problematic_columns": [12, 13, 14, 15, 16, 17, 18]
    },
    "court_records_csv": {
        "url": "https://example.com/court-records.csv",
        "delimiter": ",",
        "encoding": "utf-8",
        "field_mapping": SAMPLE_FIELD_MAPPINGS["minimal"],
        "problematic_columns": []
    },
    "legacy_system": {
        "url": "https://legacy.court.gov/data.txt",
        "delimiter": "|",
        "encoding": "latin-1",
        "field_mapping": SAMPLE_FIELD_MAPPINGS["custom"],
        "problematic_columns": [1, 2, 3]
    }
}