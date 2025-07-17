"""
Test suite for domain models and core functionality
"""
import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from src.domain.aggregates import BulkDataSet, CourtRecord
from src.domain.value_objects import (
    DataFile, DataFileStatus, CourtIdentifier, CaseMetadata,
    QueryParams, QueryOperator, DataRange, ColumnCleaningRule,
    PROBLEMATIC_COLUMNS, DEFAULT_COLUMN_CLEANING
)
from src.domain.services import (
    DataValidationService, ColumnCleaningService, 
    DataParsingService, QueryService, RecordValidationService
)
from src.domain.test_data import TestDataFactory
from src.storage.file_storage import FileStorage


class TestValueObjects:
    """Test value objects"""
    
    def test_data_file_creation(self):
        """Test DataFile creation and validation"""
        data_file = DataFile(path="/test/path/file.txt", size=1024)
        
        assert data_file.path == "/test/path/file.txt"
        assert data_file.size == 1024
        assert data_file.status == DataFileStatus.PENDING
        assert data_file.filename == "file.txt"
    
    def test_data_file_with_status_update(self):
        """Test DataFile status updates"""
        original = DataFile(path="/test/file.txt", size=1024)
        updated = original.with_status(DataFileStatus.DOWNLOADED)
        
        assert updated.status == DataFileStatus.DOWNLOADED
        assert updated.path == original.path
        assert updated.size == original.size
    
    def test_data_range_validation(self):
        """Test DataRange validation"""
        # Valid range
        range1 = DataRange(start_column=0, end_column=5)
        assert range1.size == 6
        assert range1.contains(3) == True
        assert range1.contains(6) == False
        
        # Invalid range
        with pytest.raises(ValueError):
            DataRange(start_column=5, end_column=2)
    
    def test_court_identifier_validation(self):
        """Test CourtIdentifier validation"""
        court_id = CourtIdentifier(jurisdiction="Federal", court_name="District Court")
        assert court_id.full_name == "Federal - District Court"
        
        with pytest.raises(ValueError):
            CourtIdentifier(jurisdiction="", court_name="Test Court")
    
    def test_query_params_matching(self):
        """Test QueryParams matching logic"""
        query = QueryParams(field="name", value="test", operator=QueryOperator.CONTAINS)
        
        data1 = {"name": "testing data"}
        data2 = {"name": "other data"}
        
        assert query.matches(data1) == True
        assert query.matches(data2) == False
    
    def test_column_cleaning_rule(self):
        """Test ColumnCleaningRule"""
        rule = ColumnCleaningRule(
            column_range=DataRange(0, 2),
            remove_null_bytes=True,
            trim_whitespace=True
        )
        
        dirty_text = "  text with\x00null bytes  "
        clean_text = rule.apply(dirty_text)
        
        assert clean_text == "text withnull bytes"
        assert "\x00" not in clean_text


class TestAggregates:
    """Test aggregate root objects"""
    
    def test_bulk_dataset_creation(self):
        """Test BulkDataSet creation and validation"""
        dataset = TestDataFactory.create_sample_bulk_dataset()
        
        assert dataset.dataset_id == "test_dataset_001"
        assert len(dataset.data_files) == 2
        assert dataset.total_size == 3072000
    
    def test_bulk_dataset_file_operations(self):
        """Test BulkDataSet file operations"""
        dataset = BulkDataSet(dataset_id="test_dataset")
        
        # Add file
        dataset.add_data_file("/test/file.txt")
        assert len(dataset.data_files) == 1
        
        # Update file status
        dataset.update_file_status("/test/file.txt", DataFileStatus.DOWNLOADED)
        assert dataset.data_files[0].status == DataFileStatus.DOWNLOADED
    
    def test_bulk_dataset_validation(self):
        """Test BulkDataSet validation"""
        dataset = TestDataFactory.create_sample_bulk_dataset()
        
        # Should be valid
        assert dataset.validate_for_processing() == True
        
        # Test with problematic dataset
        problematic = TestDataFactory.create_dataset_with_problems()
        assert problematic.validate_for_processing() == False
    
    def test_court_record_creation(self):
        """Test CourtRecord creation"""
        records = TestDataFactory.create_sample_court_records()
        
        assert len(records) == 3
        assert records[0].record_id == "rec_001"
        assert records[0].court_identifier.jurisdiction == "Federal"
        assert records[0].case_metadata.case_number == "3:21-cv-00123"
    
    def test_court_record_column_data(self):
        """Test CourtRecord column data handling"""
        records = TestDataFactory.create_sample_court_records()
        problematic_record = records[1]  # Has problematic columns
        
        # Check that problematic columns are cleaned
        column_12 = problematic_record.column_data[12]
        assert "\x00" not in column_12  # Null bytes should be removed
    
    def test_court_record_query_matching(self):
        """Test CourtRecord query matching"""
        records = TestDataFactory.create_sample_court_records()
        record = records[0]
        
        query = QueryParams(field="case_number", value="3:21-cv-00123", operator=QueryOperator.EQUALS)
        assert record.matches_query(query) == True
        
        query2 = QueryParams(field="jurisdiction", value="State", operator=QueryOperator.EQUALS)
        assert record.matches_query(query2) == False


class TestServices:
    """Test domain services"""
    
    def test_data_validation_service(self):
        """Test DataValidationService"""
        dataset = TestDataFactory.create_sample_bulk_dataset()
        errors = DataValidationService.validate_dataset(dataset)
        
        # Should have no errors for valid dataset
        assert len(errors) == 0
        
        # Test with problematic dataset
        problematic = TestDataFactory.create_dataset_with_problems()
        errors = DataValidationService.validate_dataset(problematic)
        assert len(errors) > 0
    
    def test_column_cleaning_service(self):
        """Test ColumnCleaningService"""
        records = TestDataFactory.create_sample_court_records()
        problematic_record = records[1]  # Has problematic columns
        
        # Apply cleaning
        cleaned_record = ColumnCleaningService.clean_record_columns(problematic_record)
        
        # Check that columns 12-18 are cleaned
        for i in range(12, 19):
            if i < len(cleaned_record.column_data):
                column_data = cleaned_record.column_data[i]
                assert "\x00" not in column_data
                assert column_data.strip() == column_data  # Should be trimmed
    
    def test_data_parsing_service(self):
        """Test DataParsingService"""
        # Test line parsing
        test_line = "\t".join(TestDataFactory.create_sample_columns_clean())
        columns = DataParsingService.parse_raw_line(test_line)
        
        assert len(columns) == 21
        assert columns[0] == "rec_001"
        assert columns[4] == "3:21-cv-00123"
        
        # Test record parsing
        record = DataParsingService.parse_columns_to_record(columns)
        assert record.record_id == "rec_001"
        assert record.case_metadata.case_number == "3:21-cv-00123"
    
    def test_query_service(self):
        """Test QueryService"""
        # Test query building
        query = QueryService.build_query("case_number", "123", "contains")
        assert query.field == "case_number"
        assert query.value == "123"
        assert query.operator == QueryOperator.CONTAINS
        
        # Test text search query
        text_query = QueryService.build_text_search_query("Smith")
        assert text_query.field == "searchable_text"
        assert text_query.value == "Smith"
    
    def test_record_validation_service(self):
        """Test RecordValidationService"""
        records = TestDataFactory.create_sample_court_records()
        record = records[0]
        
        # Validate and enrich
        enriched = RecordValidationService.validate_and_enrich_record(record)
        
        # Should have searchable text
        assert "searchable_text" in enriched.parsed_data
        assert enriched.parsed_data["has_parties"] == True
        assert enriched.parsed_data["column_count"] == len(record.column_data)


class TestFileStorage:
    """Test file storage system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = FileStorage(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_dataset_storage(self):
        """Test dataset storage operations"""
        dataset = TestDataFactory.create_sample_bulk_dataset()
        
        # Save dataset
        self.storage.save_dataset(dataset)
        
        # Load dataset
        loaded = self.storage.load_dataset(dataset.dataset_id)
        
        assert loaded.dataset_id == dataset.dataset_id
        assert len(loaded.data_files) == len(dataset.data_files)
        assert loaded.total_size == dataset.total_size
    
    def test_record_storage(self):
        """Test record storage operations"""
        records = TestDataFactory.create_sample_court_records()
        record = records[0]
        
        # Save record
        self.storage.save_record(record)
        
        # Load record
        loaded = self.storage.load_record(record.record_id)
        
        assert loaded.record_id == record.record_id
        assert loaded.court_identifier.jurisdiction == record.court_identifier.jurisdiction
        assert loaded.case_metadata.case_number == record.case_metadata.case_number
    
    def test_record_search(self):
        """Test record search functionality"""
        records = TestDataFactory.create_sample_court_records()
        
        # Save all records
        for record in records:
            self.storage.save_record(record)
        
        # Search by jurisdiction
        query = QueryParams(field="jurisdiction", value="Federal", operator=QueryOperator.EQUALS)
        results = list(self.storage.search_records(query))
        
        # Should find 2 federal records
        assert len(results) == 2
        assert all(r.court_identifier.jurisdiction == "Federal" for r in results)
    
    def test_batch_operations(self):
        """Test batch storage operations"""
        records = TestDataFactory.create_sample_court_records()
        
        # Save batch
        self.storage.save_records_batch(records)
        
        # Count records
        count = self.storage.count_records()
        assert count == len(records)
        
        # Get all records
        all_records = list(self.storage.get_all_records())
        assert len(all_records) == len(records)
    
    def test_storage_stats(self):
        """Test storage statistics"""
        dataset = TestDataFactory.create_sample_bulk_dataset()
        records = TestDataFactory.create_sample_court_records()
        
        # Save data
        self.storage.save_dataset(dataset)
        for record in records:
            self.storage.save_record(record)
        
        # Get stats
        stats = self.storage.get_storage_stats()
        
        assert stats["total_datasets"] == 1
        assert stats["total_records"] == len(records)
        assert stats["storage_path"] == str(Path(self.temp_dir).absolute())
        assert stats["disk_usage"] > 0


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = FileStorage(self.temp_dir)
        self.test_file = os.path.join(self.temp_dir, "test_data.txt")
        
        # Create test data file
        TestDataFactory.write_test_data_file(self.test_file)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_complete_data_processing_workflow(self):
        """Test complete data processing workflow"""
        # 1. Create dataset
        dataset = BulkDataSet(dataset_id="integration_test")
        dataset.add_data_file(self.test_file)
        dataset.update_file_status(self.test_file, DataFileStatus.DOWNLOADED)
        
        # 2. Save dataset
        self.storage.save_dataset(dataset)
        
        # 3. Parse data file
        records = list(DataParsingService.parse_raw_data_file(self.test_file))
        assert len(records) == 3
        
        # 4. Validate and enrich records
        enriched_records = []
        for record in records:
            enriched = RecordValidationService.validate_and_enrich_record(record)
            enriched_records.append(enriched)
        
        # 5. Save records
        self.storage.save_records_batch(enriched_records)
        
        # 6. Mark dataset as parsed
        dataset.complete_parsing()
        self.storage.save_dataset(dataset)
        
        # 7. Test search functionality
        query = QueryParams(field="jurisdiction", value="Federal", operator=QueryOperator.EQUALS)
        results = list(self.storage.search_records(query))
        
        assert len(results) >= 1
        assert all(r.court_identifier.jurisdiction == "Federal" for r in results)
    
    def test_error_handling_workflow(self):
        """Test error handling in workflows"""
        # Test with problematic dataset
        dataset = TestDataFactory.create_dataset_with_problems()
        
        # Should fail validation
        assert dataset.validate_for_processing() == False
        
        # Should have error files
        error_files = dataset.get_error_files()
        assert len(error_files) > 0
        
        # Should have validation errors
        errors = DataValidationService.validate_dataset(dataset)
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])