"""
Value Objects for CourtFinder domain model
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum
import os


class DataFileStatus(Enum):
    """Status of a data file"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PARSING = "parsing"
    PARSED = "parsed"
    ERROR = "error"


class QueryOperator(Enum):
    """Query operators for search"""
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"


@dataclass(frozen=True)
class DataFile:
    """Value object representing a data file"""
    path: str
    size: Optional[int] = None
    status: DataFileStatus = DataFileStatus.PENDING
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate data file"""
        if not self.path:
            raise ValueError("Data file path cannot be empty")
        
        # Convert to Path object for validation
        path_obj = Path(self.path)
        
        # If file exists, get its size
        if path_obj.exists():
            object.__setattr__(self, 'size', path_obj.stat().st_size)
    
    @property
    def exists(self) -> bool:
        """Check if file exists"""
        return Path(self.path).exists()
    
    @property
    def filename(self) -> str:
        """Get filename without path"""
        return Path(self.path).name
    
    def with_status(self, status: DataFileStatus, error_message: Optional[str] = None) -> 'DataFile':
        """Create new DataFile with updated status"""
        return DataFile(
            path=self.path,
            size=self.size,
            status=status,
            error_message=error_message
        )


@dataclass(frozen=True)
class DataRange:
    """Value object representing a range of data columns"""
    start_column: int
    end_column: int
    
    def __post_init__(self):
        """Validate data range"""
        if self.start_column < 0:
            raise ValueError("Start column must be non-negative")
        if self.end_column < 0:
            raise ValueError("End column must be non-negative")
        if self.start_column > self.end_column:
            raise ValueError("Start column must be less than or equal to end column")
    
    @property
    def size(self) -> int:
        """Get the size of the range"""
        return self.end_column - self.start_column + 1
    
    def contains(self, column: int) -> bool:
        """Check if column is within range"""
        return self.start_column <= column <= self.end_column
    
    def overlaps_with(self, other: 'DataRange') -> bool:
        """Check if this range overlaps with another"""
        return (self.start_column <= other.end_column and 
                self.end_column >= other.start_column)


@dataclass(frozen=True)
class QueryParams:
    """Value object representing search query parameters"""
    field: str
    value: str
    operator: QueryOperator = QueryOperator.CONTAINS
    case_sensitive: bool = False
    
    def __post_init__(self):
        """Validate query parameters"""
        if not self.field:
            raise ValueError("Query field cannot be empty")
        if not self.value:
            raise ValueError("Query value cannot be empty")
    
    def matches(self, data: Dict[str, Any]) -> bool:
        """Check if data matches this query"""
        if self.field not in data:
            return False
        
        field_value = str(data[self.field])
        query_value = self.value
        
        if not self.case_sensitive:
            field_value = field_value.lower()
            query_value = query_value.lower()
        
        if self.operator == QueryOperator.EQUALS:
            return field_value == query_value
        elif self.operator == QueryOperator.CONTAINS:
            return query_value in field_value
        elif self.operator == QueryOperator.STARTS_WITH:
            return field_value.startswith(query_value)
        elif self.operator == QueryOperator.ENDS_WITH:
            return field_value.endswith(query_value)
        elif self.operator == QueryOperator.REGEX:
            import re
            pattern = re.compile(query_value, re.IGNORECASE if not self.case_sensitive else 0)
            return bool(pattern.search(field_value))
        
        return False


@dataclass(frozen=True)
class CourtIdentifier:
    """Value object representing a court identifier"""
    jurisdiction: str
    court_name: str
    court_code: Optional[str] = None
    
    def __post_init__(self):
        """Validate court identifier"""
        if not self.jurisdiction:
            raise ValueError("Jurisdiction cannot be empty")
        if not self.court_name:
            raise ValueError("Court name cannot be empty")
    
    @property
    def full_name(self) -> str:
        """Get full court name with jurisdiction"""
        return f"{self.jurisdiction} - {self.court_name}"
    
    def __str__(self) -> str:
        """String representation"""
        return self.full_name


@dataclass(frozen=True)
class CaseMetadata:
    """Value object representing case metadata"""
    case_number: str
    filing_date: Optional[str] = None
    parties: Optional[str] = None
    case_type: Optional[str] = None
    status: Optional[str] = None
    
    def __post_init__(self):
        """Validate case metadata"""
        if not self.case_number:
            raise ValueError("Case number cannot be empty")
    
    def __str__(self) -> str:
        """String representation"""
        return f"Case {self.case_number}"


# Special handling for problematic columns 12-18
PROBLEMATIC_COLUMNS = DataRange(12, 18)

@dataclass(frozen=True)
class ColumnCleaningRule:
    """Value object for column cleaning rules"""
    column_range: DataRange
    remove_null_bytes: bool = True
    trim_whitespace: bool = True
    remove_control_chars: bool = True
    encoding_fix: bool = True
    
    def apply(self, text: str) -> str:
        """Apply cleaning rules to text"""
        if text is None:
            return ""
        
        result = str(text)
        
        if self.remove_null_bytes:
            result = result.replace('\x00', '')
        
        if self.remove_control_chars:
            # Remove control characters except newlines and tabs
            result = ''.join(char for char in result 
                           if ord(char) >= 32 or char in '\n\t')
        
        if self.encoding_fix:
            # Try to fix common encoding issues
            result = result.encode('utf-8', errors='ignore').decode('utf-8')
        
        if self.trim_whitespace:
            result = result.strip()
        
        return result


# Default cleaning rule for columns 12-18
DEFAULT_COLUMN_CLEANING = ColumnCleaningRule(
    column_range=PROBLEMATIC_COLUMNS,
    remove_null_bytes=True,
    trim_whitespace=True,
    remove_control_chars=True,
    encoding_fix=True
)