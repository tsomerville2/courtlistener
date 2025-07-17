"""
CSV Parser for CourtListener Bulk Data

Handles parsing of real CourtListener CSV files with proper quote handling,
null/blank distinction, and field mapping based on API documentation.
"""

import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator, Callable, Union
from datetime import datetime, date
from dataclasses import dataclass
import json
from enum import Enum

from .models import (
    Court, Docket, OpinionCluster, Opinion, Citation, Person,
    PrecedentialStatus, OpinionType
)


class ParseError(Exception):
    """CSV parsing error"""
    pass


@dataclass
class ParseStats:
    """Statistics for CSV parsing operation"""
    total_rows: int = 0
    parsed_rows: int = 0
    error_rows: int = 0
    skipped_rows: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def add_error(self, error: str):
        """Add parsing error"""
        self.errors.append(error)
        self.error_rows += 1
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.total_rows == 0:
            return 0.0
        return (self.parsed_rows / self.total_rows) * 100


class CSVFieldMapper:
    """Maps CSV fields to model attributes with type conversion"""
    
    @staticmethod
    def parse_date(value: str) -> Optional[date]:
        """Parse date string to date object"""
        if not value or value.strip() == '':
            return None
        
        # Try different date formats
        formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']
        
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {value}")
    
    @staticmethod
    def parse_datetime(value: str) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not value or value.strip() == '':
            return None
        
        # Try different datetime formats
        formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse datetime: {value}")
    
    @staticmethod
    def parse_boolean(value: str) -> bool:
        """Parse boolean string"""
        if not value or value.strip() == '':
            return False
        
        value = value.strip().lower()
        return value in ['true', 't', '1', 'yes', 'y']
    
    @staticmethod
    def parse_integer(value: str) -> Optional[int]:
        """Parse integer string"""
        if not value or value.strip() == '':
            return None
        
        try:
            return int(value.strip())
        except ValueError:
            raise ValueError(f"Unable to parse integer: {value}")
    
    @staticmethod
    def parse_float(value: str) -> Optional[float]:
        """Parse float string"""
        if not value or value.strip() == '':
            return None
        
        try:
            return float(value.strip())
        except ValueError:
            raise ValueError(f"Unable to parse float: {value}")
    
    @staticmethod
    def parse_list(value: str, separator: str = ',') -> List[str]:
        """Parse comma-separated list"""
        if not value or value.strip() == '':
            return []
        
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    @staticmethod
    def parse_enum(value: str, enum_class) -> Optional[Any]:
        """Parse enum value"""
        if not value or value.strip() == '':
            return None
        
        try:
            return enum_class(value.strip())
        except ValueError:
            # Try to find by name
            for enum_item in enum_class:
                if enum_item.name.lower() == value.strip().lower():
                    return enum_item
            
            raise ValueError(f"Unknown enum value: {value}")


class CourtCSVParser:
    """Parser for courts.csv"""
    
    FIELD_MAPPING = {
        'id': ('id', str),
        'full_name': ('full_name', str),
        'short_name': ('short_name', str),
        'jurisdiction': ('jurisdiction', str),
        'position': ('position', CSVFieldMapper.parse_float),
        'citation_string': ('citation_string', str),
        'start_date': ('start_date', CSVFieldMapper.parse_date),
        'end_date': ('end_date', CSVFieldMapper.parse_date),
        'notes': ('notes', str)
    }
    
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Court:
        """Parse a single CSV row into a Court object"""
        parsed_data = {}
        
        for csv_field, (model_field, parser) in cls.FIELD_MAPPING.items():
            if csv_field in row:
                value = row[csv_field]
                
                # Handle null vs blank distinction
                if value == '' or value is None:
                    parsed_data[model_field] = None
                else:
                    try:
                        parsed_data[model_field] = parser(value)
                    except (ValueError, TypeError) as e:
                        if model_field == 'id':  # Required field
                            raise ParseError(f"Error parsing required field {csv_field}: {e}")
                        parsed_data[model_field] = None
        
        return Court(**parsed_data)


class DocketCSVParser:
    """Parser for dockets.csv"""
    
    FIELD_MAPPING = {
        'id': ('id', CSVFieldMapper.parse_integer),
        'date_created': ('date_created', CSVFieldMapper.parse_datetime),
        'date_modified': ('date_modified', CSVFieldMapper.parse_datetime),
        'source': ('source', str),
        'court_id': ('court_id', str),
        'appeal_from_id': ('appeal_from_id', str),
        'case_name': ('case_name', str),
        'case_name_short': ('case_name_short', str),
        'case_name_full': ('case_name_full', str),
        'slug': ('slug', str),
        'docket_number': ('docket_number', str),
        'date_filed': ('date_filed', CSVFieldMapper.parse_date),
        'date_filed_is_approximate': ('date_filed_is_approximate', CSVFieldMapper.parse_boolean),
        'date_terminated': ('date_terminated', CSVFieldMapper.parse_date),
        'date_terminated_is_approximate': ('date_terminated_is_approximate', CSVFieldMapper.parse_boolean),
        'federal_dn_case_type': ('federal_dn_case_type', str),
        'federal_dn_office_code': ('federal_dn_office_code', str),
        'federal_defendant_number': ('federal_defendant_number', str)
    }
    
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Docket:
        """Parse a single CSV row into a Docket object"""
        parsed_data = {}
        
        for csv_field, (model_field, parser) in cls.FIELD_MAPPING.items():
            if csv_field in row:
                value = row[csv_field]
                
                if value == '' or value is None:
                    parsed_data[model_field] = None
                else:
                    try:
                        parsed_data[model_field] = parser(value)
                    except (ValueError, TypeError) as e:
                        if model_field in ['id', 'court_id', 'case_name', 'docket_number']:
                            raise ParseError(f"Error parsing required field {csv_field}: {e}")
                        parsed_data[model_field] = None
        
        return Docket(**parsed_data)


class OpinionClusterCSVParser:
    """Parser for opinion_clusters.csv"""
    
    FIELD_MAPPING = {
        'id': ('id', CSVFieldMapper.parse_integer),
        'date_created': ('date_created', CSVFieldMapper.parse_datetime),
        'date_modified': ('date_modified', CSVFieldMapper.parse_datetime),
        'judges': ('judges', str),
        'date_filed': ('date_filed', CSVFieldMapper.parse_date),
        'date_filed_is_approximate': ('date_filed_is_approximate', CSVFieldMapper.parse_boolean),
        'slug': ('slug', str),
        'case_name': ('case_name', str),
        'case_name_short': ('case_name_short', str),
        'case_name_full': ('case_name_full', str),
        'scdb_id': ('scdb_id', str),
        'scdb_decision_direction': ('scdb_decision_direction', str),
        'scdb_votes_majority': ('scdb_votes_majority', CSVFieldMapper.parse_integer),
        'scdb_votes_minority': ('scdb_votes_minority', CSVFieldMapper.parse_integer),
        'source': ('source', str),
        'procedural_history': ('procedural_history', str),
        'attorneys': ('attorneys', str),
        'nature_of_suit': ('nature_of_suit', str),
        'posture': ('posture', str),
        'syllabus': ('syllabus', str),
        'headnotes': ('headnotes', str),
        'summary': ('summary', str),
        'disposition': ('disposition', str),
        'history': ('history', str),
        'other_dates': ('other_dates', str),
        'cross_reference': ('cross_reference', str),
        'correction': ('correction', str),
        'citation_count': ('citation_count', CSVFieldMapper.parse_integer),
        'precedential_status': ('precedential_status', lambda x: CSVFieldMapper.parse_enum(x, PrecedentialStatus)),
        'date_blocked': ('date_blocked', CSVFieldMapper.parse_date),
        'blocked': ('blocked', CSVFieldMapper.parse_boolean),
        'docket_id': ('docket_id', CSVFieldMapper.parse_integer),
        'sub_opinions': ('sub_opinions', lambda x: CSVFieldMapper.parse_list(x))
    }
    
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> OpinionCluster:
        """Parse a single CSV row into an OpinionCluster object"""
        parsed_data = {}
        
        for csv_field, (model_field, parser) in cls.FIELD_MAPPING.items():
            if csv_field in row:
                value = row[csv_field]
                
                if value == '' or value is None:
                    parsed_data[model_field] = None if model_field != 'sub_opinions' else []
                else:
                    try:
                        parsed_data[model_field] = parser(value)
                    except (ValueError, TypeError) as e:
                        if model_field in ['id', 'docket_id']:
                            raise ParseError(f"Error parsing required field {csv_field}: {e}")
                        parsed_data[model_field] = None if model_field != 'sub_opinions' else []
        
        return OpinionCluster(**parsed_data)


class OpinionCSVParser:
    """Parser for opinions.csv"""
    
    FIELD_MAPPING = {
        'id': ('id', CSVFieldMapper.parse_integer),
        'date_created': ('date_created', CSVFieldMapper.parse_datetime),
        'date_modified': ('date_modified', CSVFieldMapper.parse_datetime),
        'type': ('type', lambda x: CSVFieldMapper.parse_enum(x, OpinionType)),
        'sha1': ('sha1', str),
        'page_count': ('page_count', CSVFieldMapper.parse_integer),
        'download_url': ('download_url', str),
        'local_path': ('local_path', str),
        'plain_text': ('plain_text', str),
        'html': ('html', str),
        'html_lawbox': ('html_lawbox', str),
        'html_columbia': ('html_columbia', str),
        'html_anon_2020': ('html_anon_2020', str),
        'xml_harvard': ('xml_harvard', str),
        'html_with_citations': ('html_with_citations', str),
        'extracted_by_ocr': ('extracted_by_ocr', CSVFieldMapper.parse_boolean),
        'author_id': ('author_id', CSVFieldMapper.parse_integer),
        'per_curiam': ('per_curiam', CSVFieldMapper.parse_boolean),
        'joined_by': ('joined_by', lambda x: CSVFieldMapper.parse_list(x)),
        'cluster_id': ('cluster_id', CSVFieldMapper.parse_integer)
    }
    
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Opinion:
        """Parse a single CSV row into an Opinion object"""
        parsed_data = {}
        
        for csv_field, (model_field, parser) in cls.FIELD_MAPPING.items():
            if csv_field in row:
                value = row[csv_field]
                
                if value == '' or value is None:
                    parsed_data[model_field] = None if model_field != 'joined_by' else []
                else:
                    try:
                        parsed_data[model_field] = parser(value)
                    except (ValueError, TypeError) as e:
                        if model_field in ['id', 'cluster_id', 'type']:
                            raise ParseError(f"Error parsing required field {csv_field}: {e}")
                        parsed_data[model_field] = None if model_field != 'joined_by' else []
        
        return Opinion(**parsed_data)


class CitationCSVParser:
    """Parser for citations.csv"""
    
    FIELD_MAPPING = {
        'cited_opinion_id': ('cited_opinion_id', CSVFieldMapper.parse_integer),
        'citing_opinion_id': ('citing_opinion_id', CSVFieldMapper.parse_integer),
        'depth': ('depth', CSVFieldMapper.parse_integer),
        'quoted': ('quoted', CSVFieldMapper.parse_boolean),
        'parenthetical_id': ('parenthetical_id', CSVFieldMapper.parse_integer),
        'parenthetical_text': ('parenthetical_text', str)
    }
    
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Citation:
        """Parse a single CSV row into a Citation object"""
        parsed_data = {}
        
        for csv_field, (model_field, parser) in cls.FIELD_MAPPING.items():
            if csv_field in row:
                value = row[csv_field]
                
                if value == '' or value is None:
                    parsed_data[model_field] = None
                else:
                    try:
                        parsed_data[model_field] = parser(value)
                    except (ValueError, TypeError) as e:
                        if model_field in ['cited_opinion_id', 'citing_opinion_id', 'depth']:
                            raise ParseError(f"Error parsing required field {csv_field}: {e}")
                        parsed_data[model_field] = None
        
        return Citation(**parsed_data)


class PersonCSVParser:
    """Parser for people.csv"""
    
    FIELD_MAPPING = {
        'id': ('id', CSVFieldMapper.parse_integer),
        'date_created': ('date_created', CSVFieldMapper.parse_datetime),
        'date_modified': ('date_modified', CSVFieldMapper.parse_datetime),
        'name_first': ('name_first', str),
        'name_middle': ('name_middle', str),
        'name_last': ('name_last', str),
        'name_suffix': ('name_suffix', str),
        'date_dob': ('date_dob', CSVFieldMapper.parse_date),
        'date_granularity_dob': ('date_granularity_dob', str),
        'date_dod': ('date_dod', CSVFieldMapper.parse_date),
        'date_granularity_dod': ('date_granularity_dod', str),
        'dob_city': ('dob_city', str),
        'dob_state': ('dob_state', str),
        'dod_city': ('dod_city', str),
        'dod_state': ('dod_state', str),
        'gender': ('gender', str),
        'religion': ('religion', str),
        'ftm_total_received': ('ftm_total_received', CSVFieldMapper.parse_float),
        'ftm_eid': ('ftm_eid', str),
        'has_photo': ('has_photo', CSVFieldMapper.parse_boolean),
        'is_alias_of': ('is_alias_of', CSVFieldMapper.parse_integer)
    }
    
    @classmethod
    def parse_row(cls, row: Dict[str, str]) -> Person:
        """Parse a single CSV row into a Person object"""
        parsed_data = {}
        
        for csv_field, (model_field, parser) in cls.FIELD_MAPPING.items():
            if csv_field in row:
                value = row[csv_field]
                
                if value == '' or value is None:
                    parsed_data[model_field] = None
                else:
                    try:
                        parsed_data[model_field] = parser(value)
                    except (ValueError, TypeError) as e:
                        if model_field in ['id']:
                            raise ParseError(f"Error parsing required field {csv_field}: {e}")
                        parsed_data[model_field] = None
        
        return Person(**parsed_data)


class BulkCSVParser:
    """
    Main parser for CourtListener bulk CSV files
    """
    
    PARSERS = {
        'courts': CourtCSVParser,
        'dockets': DocketCSVParser,
        'opinion_clusters': OpinionClusterCSVParser,
        'opinions': OpinionCSVParser,
        'citations': CitationCSVParser,
        'people': PersonCSVParser
    }
    
    def __init__(self, max_errors: int = 100):
        """
        Initialize bulk CSV parser
        
        Args:
            max_errors: Maximum number of errors before stopping
        """
        self.max_errors = max_errors
    
    def parse_file(self, file_path: Union[str, Path], data_type: str, 
                  limit: Optional[int] = None, 
                  progress_callback: Optional[Callable[[int], None]] = None) -> Iterator[Any]:
        """
        Parse CSV file and yield objects
        
        Args:
            file_path: Path to CSV file
            data_type: Type of data (courts, dockets, etc.)
            limit: Maximum number of rows to parse
            progress_callback: Function to call with progress updates
            
        Yields:
            Parsed objects
        """
        if data_type not in self.PARSERS:
            raise ValueError(f"Unknown data type: {data_type}")
        
        parser_class = self.PARSERS[data_type]
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            # Use csv.DictReader with proper quoting
            reader = csv.DictReader(csvfile, quoting=csv.QUOTE_ALL)
            
            row_count = 0
            for row in reader:
                if limit and row_count >= limit:
                    break
                
                try:
                    obj = parser_class.parse_row(row)
                    yield obj
                    row_count += 1
                    
                    if progress_callback:
                        progress_callback(row_count)
                        
                except ParseError as e:
                    print(f"Parse error at row {row_count + 1}: {e}")
                    if self.max_errors > 0:
                        self.max_errors -= 1
                        if self.max_errors <= 0:
                            raise ParseError("Too many parsing errors")
                    continue
    
    def parse_file_with_stats(self, file_path: Union[str, Path], data_type: str,
                             limit: Optional[int] = None) -> tuple[List[Any], ParseStats]:
        """
        Parse CSV file and return objects with statistics
        
        Args:
            file_path: Path to CSV file
            data_type: Type of data
            limit: Maximum number of rows to parse
            
        Returns:
            Tuple of (parsed_objects, parse_stats)
        """
        objects = []
        stats = ParseStats()
        
        def progress_callback(count: int):
            stats.total_rows = count
        
        try:
            for obj in self.parse_file(file_path, data_type, limit, progress_callback):
                objects.append(obj)
                stats.parsed_rows += 1
                
        except ParseError as e:
            stats.add_error(str(e))
        
        return objects, stats
    
    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types"""
        return list(self.PARSERS.keys())
    
    def validate_csv_structure(self, file_path: Union[str, Path], 
                              data_type: str) -> Dict[str, Any]:
        """
        Validate CSV file structure
        
        Args:
            file_path: Path to CSV file
            data_type: Expected data type
            
        Returns:
            Validation results
        """
        if data_type not in self.PARSERS:
            return {
                'valid': False,
                'error': f"Unknown data type: {data_type}"
            }
        
        file_path = Path(file_path)
        if not file_path.exists():
            return {
                'valid': False,
                'error': f"File not found: {file_path}"
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                
                parser_class = self.PARSERS[data_type]
                expected_fields = set(parser_class.FIELD_MAPPING.keys())
                actual_fields = set(headers) if headers else set()
                
                missing_fields = expected_fields - actual_fields
                extra_fields = actual_fields - expected_fields
                
                return {
                    'valid': len(missing_fields) == 0,
                    'headers': headers,
                    'expected_fields': list(expected_fields),
                    'missing_fields': list(missing_fields),
                    'extra_fields': list(extra_fields)
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f"Error reading file: {str(e)}"
            }