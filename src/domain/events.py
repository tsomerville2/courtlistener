"""
Domain Events for CourtFinder
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events"""
    aggregate_id: str
    occurred_at: datetime = None
    
    def __post_init__(self):
        if self.occurred_at is None:
            object.__setattr__(self, 'occurred_at', datetime.now())
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        pass
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Get event type identifier"""
        pass


@dataclass
class DataDownloadRequested(DomainEvent):
    """Event raised when data download is requested"""
    download_url: str
    
    @property
    def event_type(self) -> str:
        return "DataDownloadRequested"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'download_url': self.download_url,
            'occurred_at': self.occurred_at.isoformat()
        }


@dataclass
class DataParsingCompleted(DomainEvent):
    """Event raised when data parsing is completed"""
    parsed_files: int
    
    @property
    def event_type(self) -> str:
        return "DataParsingCompleted"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'parsed_files': self.parsed_files,
            'occurred_at': self.occurred_at.isoformat()
        }


@dataclass
class QueryExecuted(DomainEvent):
    """Event raised when a query is executed"""
    query_field: str
    query_value: str
    matches: bool
    
    @property
    def event_type(self) -> str:
        return "QueryExecuted"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'query_field': self.query_field,
            'query_value': self.query_value,
            'matches': self.matches,
            'occurred_at': self.occurred_at.isoformat()
        }


@dataclass
class DataValidationFailed(DomainEvent):
    """Event raised when data validation fails"""
    reason: str
    details: Optional[Dict[str, Any]] = None
    
    @property
    def event_type(self) -> str:
        return "DataValidationFailed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'reason': self.reason,
            'details': self.details,
            'occurred_at': self.occurred_at.isoformat()
        }


@dataclass
class ColumnCleaningApplied(DomainEvent):
    """Event raised when column cleaning is applied"""
    column_range: str
    cleaned_count: int
    
    @property
    def event_type(self) -> str:
        return "ColumnCleaningApplied"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'column_range': self.column_range,
            'cleaned_count': self.cleaned_count,
            'occurred_at': self.occurred_at.isoformat()
        }


@dataclass
class RecordValidationFailed(DomainEvent):
    """Event raised when record validation fails"""
    validation_errors: list
    
    @property
    def event_type(self) -> str:
        return "RecordValidationFailed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'validation_errors': self.validation_errors,
            'occurred_at': self.occurred_at.isoformat()
        }


class EventStore:
    """Simple event store for domain events"""
    
    def __init__(self):
        self.events: list[DomainEvent] = []
    
    def append(self, event: DomainEvent) -> None:
        """Append event to store"""
        self.events.append(event)
    
    def get_events_for_aggregate(self, aggregate_id: str) -> list[DomainEvent]:
        """Get all events for a specific aggregate"""
        return [event for event in self.events if event.aggregate_id == aggregate_id]
    
    def get_events_by_type(self, event_type: str) -> list[DomainEvent]:
        """Get all events of a specific type"""
        return [event for event in self.events if event.event_type == event_type]
    
    def clear(self) -> None:
        """Clear all events"""
        self.events.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event store to dictionary"""
        return {
            'events': [event.to_dict() for event in self.events]
        }