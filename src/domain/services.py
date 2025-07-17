"""
Domain Services for CourtFinder
Business logic that doesn't belong to any specific aggregate
"""
from typing import List, Dict, Any, Optional, Iterator
import re
from datetime import datetime
import hashlib

from .aggregates import BulkDataSet, CourtRecord
from .value_objects import (
    DataFile, DataFileStatus, QueryParams, CourtIdentifier, CaseMetadata,
    DataRange, ColumnCleaningRule, PROBLEMATIC_COLUMNS, DEFAULT_COLUMN_CLEANING
)
from .events import ColumnCleaningApplied, RecordValidationFailed


class DataValidationService:
    """Service for validating court data"""
    
    @staticmethod
    def validate_dataset(dataset: BulkDataSet) -> List[str]:
        """Validate entire dataset and return validation errors"""
        errors = []
        
        if not dataset.data_files:
            errors.append("Dataset must contain at least one data file")
        
        for data_file in dataset.data_files:
            file_errors = DataValidationService.validate_data_file(data_file)
            errors.extend(file_errors)
        
        if dataset.total_size and dataset.total_size > 1024 * 1024 * 1024:  # 1GB
            errors.append("Dataset size exceeds 1GB limit")
        
        return errors
    
    @staticmethod
    def validate_data_file(data_file: DataFile) -> List[str]:
        """Validate a single data file"""
        errors = []
        
        if not data_file.path:
            errors.append("Data file path cannot be empty")
        
        if data_file.status == DataFileStatus.ERROR and data_file.error_message:
            errors.append(f"File error: {data_file.error_message}")
        
        if data_file.size is not None and data_file.size == 0:
            errors.append("Data file is empty")
        
        return errors
    
    @staticmethod
    def validate_court_record(record: CourtRecord) -> List[str]:
        """Validate a court record"""
        errors = []
        
        if not record.record_id:
            errors.append("Record ID cannot be empty")
        
        if not record.court_identifier.jurisdiction:
            errors.append("Court jurisdiction cannot be empty")
        
        if not record.court_identifier.court_name:
            errors.append("Court name cannot be empty")
        
        if not record.case_metadata.case_number:
            errors.append("Case number cannot be empty")
        
        # Validate column data
        if record.column_data:
            column_errors = DataValidationService.validate_column_data(record.column_data)
            errors.extend(column_errors)
        
        return errors
    
    @staticmethod
    def validate_column_data(columns: List[str]) -> List[str]:
        """Validate column data for common issues"""
        errors = []
        
        for i, column in enumerate(columns):
            if column is None:
                errors.append(f"Column {i} is None")
                continue
            
            # Check for null bytes
            if '\x00' in column:
                errors.append(f"Column {i} contains null bytes")
            
            # Check for excessive control characters
            control_chars = sum(1 for c in column if ord(c) < 32 and c not in '\n\t\r')
            if control_chars > len(column) * 0.1:  # More than 10% control chars
                errors.append(f"Column {i} contains excessive control characters")
        
        return errors


class ColumnCleaningService:
    """Service for cleaning problematic columns"""
    
    @staticmethod
    def clean_record_columns(record: CourtRecord) -> CourtRecord:
        """Clean problematic columns in a record"""
        if not record.column_data:
            return record
        
        cleaned_columns = record.column_data.copy()
        cleaning_applied = False
        
        for i in range(len(cleaned_columns)):
            if PROBLEMATIC_COLUMNS.contains(i):
                original = cleaned_columns[i]
                cleaned = DEFAULT_COLUMN_CLEANING.apply(original)
                
                if cleaned != original:
                    cleaned_columns[i] = cleaned
                    cleaning_applied = True
        
        if cleaning_applied:
            record.update_column_data(cleaned_columns)
            
            # Add event
            record._add_event(ColumnCleaningApplied(
                aggregate_id=record.record_id,
                column_range=f"{PROBLEMATIC_COLUMNS.start_column}-{PROBLEMATIC_COLUMNS.end_column}",
                cleaned_count=PROBLEMATIC_COLUMNS.size
            ))
        
        return record
    
    @staticmethod
    def clean_columns_batch(records: List[CourtRecord]) -> List[CourtRecord]:
        """Clean columns for multiple records"""
        cleaned_records = []
        
        for record in records:
            cleaned_record = ColumnCleaningService.clean_record_columns(record)
            cleaned_records.append(cleaned_record)
        
        return cleaned_records
    
    @staticmethod
    def create_custom_cleaning_rule(
        column_range: DataRange,
        remove_patterns: List[str] = None,
        replace_patterns: Dict[str, str] = None
    ) -> ColumnCleaningRule:
        """Create custom cleaning rule"""
        # This would be extended to support custom patterns
        # For now, return default rule
        return DEFAULT_COLUMN_CLEANING


class DataParsingService:
    """Service for parsing court data"""
    
    # Standard field mapping for court data
    STANDARD_FIELD_MAPPING = {
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
        12: 'plaintiff',      # Problematic column
        13: 'defendant',      # Problematic column
        14: 'attorney_plaintiff',  # Problematic column
        15: 'attorney_defendant',  # Problematic column
        16: 'judge',          # Problematic column
        17: 'notes',          # Problematic column
        18: 'tags',           # Problematic column
        19: 'description',
        20: 'file_url'
    }
    
    @staticmethod
    def parse_raw_line(line: str, delimiter: str = '\t') -> List[str]:
        """Parse a raw data line into columns"""
        if not line:
            return []
        
        columns = line.split(delimiter)
        
        # Apply cleaning to problematic columns
        for i in range(len(columns)):
            if PROBLEMATIC_COLUMNS.contains(i):
                columns[i] = DEFAULT_COLUMN_CLEANING.apply(columns[i])
        
        return columns
    
    @staticmethod
    def parse_columns_to_record(
        columns: List[str],
        field_mapping: Dict[int, str] = None
    ) -> CourtRecord:
        """Parse columns into a CourtRecord"""
        if field_mapping is None:
            field_mapping = DataParsingService.STANDARD_FIELD_MAPPING
        
        # Extract required fields
        record_id = columns[0] if len(columns) > 0 else str(hashlib.md5(str(columns).encode()).hexdigest())
        
        # Extract court identifier
        jurisdiction = columns[8] if len(columns) > 8 else "Unknown"
        court_name = columns[7] if len(columns) > 7 else "Unknown Court"
        court_id = columns[6] if len(columns) > 6 else None
        
        court_identifier = CourtIdentifier(
            jurisdiction=jurisdiction,
            court_name=court_name,
            court_code=court_id
        )
        
        # Extract case metadata
        case_number = columns[4] if len(columns) > 4 else "Unknown"
        filing_date = columns[3] if len(columns) > 3 else None
        case_type = columns[10] if len(columns) > 10 else None
        status = columns[11] if len(columns) > 11 else None
        
        # Handle parties (from problematic columns)
        parties = None
        if len(columns) > 12 and len(columns) > 13:
            plaintiff = columns[12] if columns[12] else ""
            defendant = columns[13] if columns[13] else ""
            if plaintiff or defendant:
                parties = f"{plaintiff} vs {defendant}".strip(" vs")
        
        case_metadata = CaseMetadata(
            case_number=case_number,
            filing_date=filing_date,
            parties=parties,
            case_type=case_type,
            status=status
        )
        
        # Create record
        record = CourtRecord(
            record_id=record_id,
            court_identifier=court_identifier,
            case_metadata=case_metadata,
            column_data=columns
        )
        
        # Parse structured data
        record.parse_structured_data(field_mapping)
        
        return record
    
    @staticmethod
    def parse_raw_data_file(file_path: str) -> Iterator[CourtRecord]:
        """Parse raw data file into court records"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                line_number = 0
                
                for line in file:
                    line_number += 1
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        columns = DataParsingService.parse_raw_line(line)
                        if columns:
                            record = DataParsingService.parse_columns_to_record(columns)
                            yield record
                    except Exception as e:
                        # Log error but continue processing
                        print(f"Error parsing line {line_number}: {e}")
                        continue
        
        except Exception as e:
            raise ValueError(f"Failed to parse file {file_path}: {e}")


class QueryService:
    """Service for querying court records"""
    
    @staticmethod
    def build_query(field: str, value: str, operator: str = "contains") -> QueryParams:
        """Build query parameters"""
        from .value_objects import QueryOperator
        
        op_mapping = {
            "equals": QueryOperator.EQUALS,
            "contains": QueryOperator.CONTAINS,
            "starts_with": QueryOperator.STARTS_WITH,
            "ends_with": QueryOperator.ENDS_WITH,
            "regex": QueryOperator.REGEX
        }
        
        operator_enum = op_mapping.get(operator, QueryOperator.CONTAINS)
        
        return QueryParams(
            field=field,
            value=value,
            operator=operator_enum
        )
    
    @staticmethod
    def execute_search(
        records: Iterator[CourtRecord],
        query: QueryParams,
        limit: Optional[int] = None
    ) -> List[CourtRecord]:
        """Execute search on records"""
        results = []
        count = 0
        
        for record in records:
            if limit and count >= limit:
                break
            
            if record.matches_query(query):
                results.append(record)
                count += 1
        
        return results
    
    @staticmethod
    def build_text_search_query(search_text: str) -> QueryParams:
        """Build a text search query that searches all fields"""
        return QueryParams(
            field="searchable_text",
            value=search_text,
            operator=QueryOperator.CONTAINS,
            case_sensitive=False
        )


class RecordValidationService:
    """Service for validating and enriching court records"""
    
    @staticmethod
    def validate_and_enrich_record(record: CourtRecord) -> CourtRecord:
        """Validate and enrich a court record"""
        errors = DataValidationService.validate_court_record(record)
        
        if errors:
            for error in errors:
                record.add_validation_error(error)
            
            record._add_event(RecordValidationFailed(
                aggregate_id=record.record_id,
                validation_errors=errors
            ))
        
        # Apply column cleaning
        record = ColumnCleaningService.clean_record_columns(record)
        
        # Enrich with additional data
        record = RecordValidationService._enrich_record(record)
        
        return record
    
    @staticmethod
    def _enrich_record(record: CourtRecord) -> CourtRecord:
        """Enrich record with additional computed fields"""
        # Add searchable text
        searchable_text = record.get_searchable_text()
        record.parsed_data['searchable_text'] = searchable_text
        
        # Add computed fields
        record.parsed_data['has_parties'] = bool(record.case_metadata.parties)
        record.parsed_data['has_filing_date'] = bool(record.case_metadata.filing_date)
        record.parsed_data['column_count'] = len(record.column_data)
        
        return record