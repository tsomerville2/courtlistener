"""
Domain Aggregates for CourtFinder

Updated to work with CourtListener models and new data structures
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Iterator
from datetime import datetime
import json
from pathlib import Path

from .value_objects import (
    DataFile, DataRange, QueryParams, CourtIdentifier, CaseMetadata,
    DataFileStatus, ColumnCleaningRule, DEFAULT_COLUMN_CLEANING, PROBLEMATIC_COLUMNS
)
from .events import (
    DataDownloadRequested, DataParsingCompleted, QueryExecuted, 
    DataValidationFailed, DomainEvent
)

# Import new CourtListener models
try:
    from ..courtfinder.models import Court, Docket, OpinionCluster, Opinion, Citation, Person
    from ..courtfinder.storage import CourtFinderStorage
    from ..courtfinder.search import CourtFinderSearch
except ImportError:
    # Fallback for when courtfinder module is not available
    Court = Docket = OpinionCluster = Opinion = Citation = Person = None
    CourtFinderStorage = CourtFinderSearch = None


@dataclass
class BulkDataSet:
    """
    Aggregate root for bulk data operations
    Manages the lifecycle of court data downloads and processing
    """
    dataset_id: str
    data_files: List[DataFile] = field(default_factory=list)
    download_url: Optional[str] = None
    total_size: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    events: List[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate bulk dataset"""
        if not self.dataset_id:
            raise ValueError("Dataset ID cannot be empty")
        
        # Ensure total size is calculated
        if not self.total_size and self.data_files:
            self.total_size = sum(f.size for f in self.data_files if f.size)
    
    def add_data_file(self, file_path: str) -> None:
        """Add a data file to the dataset"""
        data_file = DataFile(path=file_path)
        self.data_files.append(data_file)
        self.updated_at = datetime.now()
        self._update_total_size()
    
    def update_file_status(self, file_path: str, status: DataFileStatus, 
                          error_message: Optional[str] = None) -> None:
        """Update the status of a data file"""
        for i, data_file in enumerate(self.data_files):
            if data_file.path == file_path:
                self.data_files[i] = data_file.with_status(status, error_message)
                self.updated_at = datetime.now()
                break
        else:
            raise ValueError(f"Data file not found: {file_path}")
    
    def get_files_by_status(self, status: DataFileStatus) -> List[DataFile]:
        """Get all files with a specific status"""
        return [f for f in self.data_files if f.status == status]
    
    def is_download_complete(self) -> bool:
        """Check if all files have been downloaded"""
        if not self.data_files:
            return False
        return all(f.status == DataFileStatus.DOWNLOADED for f in self.data_files)
    
    def is_parsing_complete(self) -> bool:
        """Check if all files have been parsed"""
        if not self.data_files:
            return False
        return all(f.status == DataFileStatus.PARSED for f in self.data_files)
    
    def has_errors(self) -> bool:
        """Check if any files have errors"""
        return any(f.status == DataFileStatus.ERROR for f in self.data_files)
    
    def get_error_files(self) -> List[DataFile]:
        """Get all files with errors"""
        return self.get_files_by_status(DataFileStatus.ERROR)
    
    def validate_for_processing(self) -> bool:
        """Validate dataset is ready for processing"""
        if not self.data_files:
            self._add_event(DataValidationFailed(
                aggregate_id=self.dataset_id,
                reason="No data files in dataset"
            ))
            return False
        
        if self.has_errors():
            self._add_event(DataValidationFailed(
                aggregate_id=self.dataset_id,
                reason="Dataset contains files with errors"
            ))
            return False
        
        if not self.is_download_complete():
            self._add_event(DataValidationFailed(
                aggregate_id=self.dataset_id,
                reason="Not all files have been downloaded"
            ))
            return False
        
        # Check if total size is manageable (< 1GB)
        if self.total_size and self.total_size > 1024 * 1024 * 1024:
            self._add_event(DataValidationFailed(
                aggregate_id=self.dataset_id,
                reason="Dataset size exceeds 1GB limit"
            ))
            return False
        
        return True
    
    def request_download(self, url: str) -> None:
        """Request download of bulk data"""
        self.download_url = url
        self.updated_at = datetime.now()
        self._add_event(DataDownloadRequested(
            aggregate_id=self.dataset_id,
            download_url=url
        ))
    
    def complete_parsing(self) -> None:
        """Mark parsing as complete"""
        self.updated_at = datetime.now()
        self._add_event(DataParsingCompleted(
            aggregate_id=self.dataset_id,
            parsed_files=len(self.data_files)
        ))
    
    def _update_total_size(self) -> None:
        """Update total size calculation"""
        self.total_size = sum(f.size for f in self.data_files if f.size)
    
    def _add_event(self, event: DomainEvent) -> None:
        """Add domain event"""
        self.events.append(event)
    
    def get_events(self) -> List[DomainEvent]:
        """Get all domain events"""
        return self.events.copy()
    
    def clear_events(self) -> None:
        """Clear all domain events"""
        self.events.clear()


@dataclass
class CourtRecord:
    """
    Aggregate root for court record data
    Represents a single court record with metadata and content
    Now integrates with CourtListener models
    """
    record_id: str
    court_identifier: CourtIdentifier
    case_metadata: CaseMetadata
    raw_data: Dict[str, Any] = field(default_factory=dict)
    parsed_data: Dict[str, Any] = field(default_factory=dict)
    column_data: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    events: List[DomainEvent] = field(default_factory=list)
    
    # New fields for CourtListener integration
    courtlistener_court: Optional[Any] = None  # Court object
    courtlistener_docket: Optional[Any] = None  # Docket object
    courtlistener_opinions: List[Any] = field(default_factory=list)  # Opinion objects
    
    def __post_init__(self):
        """Validate court record"""
        if not self.record_id:
            raise ValueError("Record ID cannot be empty")
    
    def update_raw_data(self, data: Dict[str, Any]) -> None:
        """Update raw data"""
        self.raw_data = data
        self.updated_at = datetime.now()
    
    def update_column_data(self, columns: List[str]) -> None:
        """Update column data with cleaning for problematic columns"""
        self.column_data = columns.copy()
        self.updated_at = datetime.now()
        
        # Apply special handling for columns 12-18
        if len(columns) > PROBLEMATIC_COLUMNS.end_column:
            cleaned_columns = columns.copy()
            for i in range(PROBLEMATIC_COLUMNS.start_column, 
                          min(PROBLEMATIC_COLUMNS.end_column + 1, len(columns))):
                cleaned_columns[i] = DEFAULT_COLUMN_CLEANING.apply(columns[i])
            self.column_data = cleaned_columns
    
    def parse_structured_data(self, field_mapping: Dict[int, str]) -> None:
        """Parse column data into structured fields"""
        self.parsed_data = {}
        
        for column_index, field_name in field_mapping.items():
            if column_index < len(self.column_data):
                value = self.column_data[column_index]
                
                # Apply additional cleaning if in problematic range
                if PROBLEMATIC_COLUMNS.contains(column_index):
                    value = DEFAULT_COLUMN_CLEANING.apply(value)
                
                self.parsed_data[field_name] = value
        
        self.updated_at = datetime.now()
    
    def add_validation_error(self, error: str) -> None:
        """Add validation error"""
        self.validation_errors.append(error)
        self.updated_at = datetime.now()
    
    def is_valid(self) -> bool:
        """Check if record is valid"""
        return len(self.validation_errors) == 0
    
    def matches_query(self, query: QueryParams) -> bool:
        """Check if record matches query parameters"""
        # Check parsed data first
        if query.matches(self.parsed_data):
            return True
        
        # Check raw data
        if query.matches(self.raw_data):
            return True
        
        # Check specific fields
        court_data = {
            'jurisdiction': self.court_identifier.jurisdiction,
            'court_name': self.court_identifier.court_name,
            'court_code': self.court_identifier.court_code or '',
            'case_number': self.case_metadata.case_number,
            'filing_date': self.case_metadata.filing_date or '',
            'parties': self.case_metadata.parties or '',
            'case_type': self.case_metadata.case_type or '',
            'status': self.case_metadata.status or ''
        }
        
        return query.matches(court_data)
    
    def get_searchable_text(self) -> str:
        """Get all searchable text combined"""
        text_parts = [
            self.court_identifier.jurisdiction,
            self.court_identifier.court_name,
            self.case_metadata.case_number,
            self.case_metadata.parties or '',
            self.case_metadata.case_type or '',
        ]
        
        # Add parsed data values
        text_parts.extend(str(v) for v in self.parsed_data.values())
        
        # Add column data (excluding problematic columns that might have bad chars)
        for i, col in enumerate(self.column_data):
            if not PROBLEMATIC_COLUMNS.contains(i):
                text_parts.append(col)
        
        return ' '.join(text_parts)
    
    def execute_query(self, query: QueryParams) -> bool:
        """Execute query and emit event"""
        matches = self.matches_query(query)
        
        self._add_event(QueryExecuted(
            aggregate_id=self.record_id,
            query_field=query.field,
            query_value=query.value,
            matches=matches
        ))
        
        return matches
    
    def _add_event(self, event: DomainEvent) -> None:
        """Add domain event"""
        self.events.append(event)
    
    def get_events(self) -> List[DomainEvent]:
        """Get all domain events"""
        return self.events.copy()
    
    def clear_events(self) -> None:
        """Clear all domain events"""
        self.events.clear()
    
    def set_courtlistener_court(self, court: Any) -> None:
        """Set CourtListener court object"""
        self.courtlistener_court = court
        self.updated_at = datetime.now()
    
    def set_courtlistener_docket(self, docket: Any) -> None:
        """Set CourtListener docket object"""
        self.courtlistener_docket = docket
        self.updated_at = datetime.now()
    
    def add_courtlistener_opinion(self, opinion: Any) -> None:
        """Add CourtListener opinion object"""
        self.courtlistener_opinions.append(opinion)
        self.updated_at = datetime.now()
    
    def has_courtlistener_data(self) -> bool:
        """Check if CourtListener data is available"""
        return (self.courtlistener_court is not None or 
                self.courtlistener_docket is not None or 
                len(self.courtlistener_opinions) > 0)
    
    def get_enhanced_searchable_text(self) -> str:
        """Get enhanced searchable text including CourtListener data"""
        text_parts = [self.get_searchable_text()]
        
        # Add CourtListener court text
        if self.courtlistener_court and hasattr(self.courtlistener_court, 'full_name'):
            text_parts.extend([
                self.courtlistener_court.full_name,
                self.courtlistener_court.jurisdiction,
                getattr(self.courtlistener_court, 'citation_string', '')
            ])
        
        # Add CourtListener docket text
        if self.courtlistener_docket and hasattr(self.courtlistener_docket, 'case_name'):
            text_parts.extend([
                self.courtlistener_docket.case_name,
                self.courtlistener_docket.docket_number,
                getattr(self.courtlistener_docket, 'case_name_full', '')
            ])
        
        # Add CourtListener opinion text
        for opinion in self.courtlistener_opinions:
            if hasattr(opinion, 'plain_text') and opinion.plain_text:
                text_parts.append(opinion.plain_text[:1000])  # First 1000 chars
        
        return ' '.join(filter(None, text_parts))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'record_id': self.record_id,
            'court_identifier': {
                'jurisdiction': self.court_identifier.jurisdiction,
                'court_name': self.court_identifier.court_name,
                'court_code': self.court_identifier.court_code
            },
            'case_metadata': {
                'case_number': self.case_metadata.case_number,
                'filing_date': self.case_metadata.filing_date,
                'parties': self.case_metadata.parties,
                'case_type': self.case_metadata.case_type,
                'status': self.case_metadata.status
            },
            'raw_data': self.raw_data,
            'parsed_data': self.parsed_data,
            'column_data': self.column_data,
            'validation_errors': self.validation_errors,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CourtRecord':
        """Create from dictionary"""
        court_id_data = data['court_identifier']
        court_identifier = CourtIdentifier(
            jurisdiction=court_id_data['jurisdiction'],
            court_name=court_id_data['court_name'],
            court_code=court_id_data.get('court_code')
        )
        
        case_data = data['case_metadata']
        case_metadata = CaseMetadata(
            case_number=case_data['case_number'],
            filing_date=case_data.get('filing_date'),
            parties=case_data.get('parties'),
            case_type=case_data.get('case_type'),
            status=case_data.get('status')
        )
        
        return cls(
            record_id=data['record_id'],
            court_identifier=court_identifier,
            case_metadata=case_metadata,
            raw_data=data.get('raw_data', {}),
            parsed_data=data.get('parsed_data', {}),
            column_data=data.get('column_data', []),
            validation_errors=data.get('validation_errors', []),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )