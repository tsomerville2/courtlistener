"""
File-based storage system for CourtFinder
Uses JSON files for data persistence
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator
from datetime import datetime
import shutil
import threading
from contextlib import contextmanager

from ..domain.aggregates import BulkDataSet, CourtRecord
from ..domain.value_objects import DataFile, DataFileStatus, QueryParams
from ..domain.events import DomainEvent, EventStore


class FileStorageError(Exception):
    """Base exception for file storage errors"""
    pass


class DataNotFoundError(FileStorageError):
    """Exception raised when requested data is not found"""
    pass


class StorageCorruptedError(FileStorageError):
    """Exception raised when storage is corrupted"""
    pass


class FileStorage:
    """File-based storage implementation"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.datasets_path = self.base_path / "datasets"
        self.records_path = self.base_path / "records"
        self.events_path = self.base_path / "events"
        self.raw_data_path = self.base_path / "raw"
        self.parsed_data_path = self.base_path / "parsed"
        
        # Thread lock for concurrent access
        self._lock = threading.Lock()
        
        # Initialize directories
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        directories = [
            self.base_path,
            self.datasets_path,
            self.records_path,
            self.events_path,
            self.raw_data_path,
            self.parsed_data_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _file_lock(self):
        """Context manager for file operations"""
        with self._lock:
            yield
    
    def _safe_write_json(self, file_path: Path, data: Any) -> None:
        """Safely write JSON data to file with atomic operation"""
        temp_path = file_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Atomic move
            temp_path.replace(file_path)
            
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise FileStorageError(f"Failed to write file {file_path}: {e}")
    
    def _safe_read_json(self, file_path: Path) -> Any:
        """Safely read JSON data from file"""
        if not file_path.exists():
            raise DataNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise StorageCorruptedError(f"Corrupted JSON file {file_path}: {e}")
        except Exception as e:
            raise FileStorageError(f"Failed to read file {file_path}: {e}")
    
    # BulkDataSet operations
    def save_dataset(self, dataset: BulkDataSet) -> None:
        """Save bulk dataset to storage"""
        with self._file_lock():
            file_path = self.datasets_path / f"{dataset.dataset_id}.json"
            
            data = {
                'dataset_id': dataset.dataset_id,
                'data_files': [
                    {
                        'path': df.path,
                        'size': df.size,
                        'status': df.status.value,
                        'error_message': df.error_message
                    }
                    for df in dataset.data_files
                ],
                'download_url': dataset.download_url,
                'total_size': dataset.total_size,
                'created_at': dataset.created_at.isoformat(),
                'updated_at': dataset.updated_at.isoformat()
            }
            
            self._safe_write_json(file_path, data)
    
    def load_dataset(self, dataset_id: str) -> BulkDataSet:
        """Load bulk dataset from storage"""
        with self._file_lock():
            file_path = self.datasets_path / f"{dataset_id}.json"
            data = self._safe_read_json(file_path)
            
            # Reconstruct data files
            data_files = []
            for df_data in data.get('data_files', []):
                status = DataFileStatus(df_data['status'])
                data_file = DataFile(
                    path=df_data['path'],
                    size=df_data.get('size'),
                    status=status,
                    error_message=df_data.get('error_message')
                )
                data_files.append(data_file)
            
            dataset = BulkDataSet(
                dataset_id=data['dataset_id'],
                data_files=data_files,
                download_url=data.get('download_url'),
                total_size=data.get('total_size'),
                created_at=datetime.fromisoformat(data['created_at']),
                updated_at=datetime.fromisoformat(data['updated_at'])
            )
            
            return dataset
    
    def delete_dataset(self, dataset_id: str) -> None:
        """Delete bulk dataset from storage"""
        with self._file_lock():
            file_path = self.datasets_path / f"{dataset_id}.json"
            if file_path.exists():
                file_path.unlink()
    
    def list_datasets(self) -> List[str]:
        """List all dataset IDs"""
        with self._file_lock():
            return [
                f.stem for f in self.datasets_path.glob("*.json")
                if f.is_file()
            ]
    
    # CourtRecord operations
    def save_record(self, record: CourtRecord) -> None:
        """Save court record to storage"""
        with self._file_lock():
            file_path = self.records_path / f"{record.record_id}.json"
            data = record.to_dict()
            self._safe_write_json(file_path, data)
    
    def load_record(self, record_id: str) -> CourtRecord:
        """Load court record from storage"""
        with self._file_lock():
            file_path = self.records_path / f"{record_id}.json"
            data = self._safe_read_json(file_path)
            return CourtRecord.from_dict(data)
    
    def delete_record(self, record_id: str) -> None:
        """Delete court record from storage"""
        with self._file_lock():
            file_path = self.records_path / f"{record_id}.json"
            if file_path.exists():
                file_path.unlink()
    
    def save_records_batch(self, records: List[CourtRecord]) -> None:
        """Save multiple records efficiently"""
        with self._file_lock():
            for record in records:
                self.save_record(record)
    
    def search_records(self, query: QueryParams, limit: Optional[int] = None) -> Iterator[CourtRecord]:
        """Search records by query parameters"""
        with self._file_lock():
            count = 0
            for record_file in self.records_path.glob("*.json"):
                if limit and count >= limit:
                    break
                
                try:
                    record = CourtRecord.from_dict(self._safe_read_json(record_file))
                    if record.matches_query(query):
                        yield record
                        count += 1
                except (FileStorageError, ValueError):
                    # Skip corrupted records
                    continue
    
    def get_all_records(self, limit: Optional[int] = None) -> Iterator[CourtRecord]:
        """Get all records"""
        with self._file_lock():
            count = 0
            for record_file in self.records_path.glob("*.json"):
                if limit and count >= limit:
                    break
                
                try:
                    record = CourtRecord.from_dict(self._safe_read_json(record_file))
                    yield record
                    count += 1
                except (FileStorageError, ValueError):
                    # Skip corrupted records
                    continue
    
    def count_records(self) -> int:
        """Count total number of records"""
        with self._file_lock():
            return len(list(self.records_path.glob("*.json")))
    
    # Raw data operations
    def save_raw_data(self, dataset_id: str, data: Any) -> None:
        """Save raw data for a dataset"""
        with self._file_lock():
            file_path = self.raw_data_path / f"{dataset_id}.json"
            self._safe_write_json(file_path, data)
    
    def load_raw_data(self, dataset_id: str) -> Any:
        """Load raw data for a dataset"""
        with self._file_lock():
            file_path = self.raw_data_path / f"{dataset_id}.json"
            return self._safe_read_json(file_path)
    
    def save_parsed_data(self, dataset_id: str, data: Any) -> None:
        """Save parsed data for a dataset"""
        with self._file_lock():
            file_path = self.parsed_data_path / f"{dataset_id}.json"
            self._safe_write_json(file_path, data)
    
    def load_parsed_data(self, dataset_id: str) -> Any:
        """Load parsed data for a dataset"""
        with self._file_lock():
            file_path = self.parsed_data_path / f"{dataset_id}.json"
            return self._safe_read_json(file_path)
    
    # Event operations
    def save_events(self, event_store: EventStore) -> None:
        """Save events to storage"""
        with self._file_lock():
            file_path = self.events_path / "events.json"
            data = event_store.to_dict()
            self._safe_write_json(file_path, data)
    
    def load_events(self) -> EventStore:
        """Load events from storage"""
        with self._file_lock():
            file_path = self.events_path / "events.json"
            
            if not file_path.exists():
                return EventStore()
            
            data = self._safe_read_json(file_path)
            event_store = EventStore()
            
            # Note: This is a simplified implementation
            # In a real system, you'd want to properly deserialize events
            # For now, we'll just store the event data
            return event_store
    
    # Utility operations
    def backup_data(self, backup_path: str) -> None:
        """Create backup of all data"""
        backup_path_obj = Path(backup_path)
        backup_path_obj.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = backup_path_obj / f"backup_{timestamp}"
        
        shutil.copytree(self.base_path, backup_dir)
    
    def restore_data(self, backup_path: str) -> None:
        """Restore data from backup"""
        backup_path_obj = Path(backup_path)
        if not backup_path_obj.exists():
            raise FileStorageError(f"Backup path does not exist: {backup_path}")
        
        # Remove current data
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
        
        # Restore from backup
        shutil.copytree(backup_path_obj, self.base_path)
        
        # Reinitialize
        self._ensure_directories()
    
    def clear_all_data(self) -> None:
        """Clear all data (use with caution)"""
        with self._file_lock():
            if self.base_path.exists():
                shutil.rmtree(self.base_path)
            self._ensure_directories()
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        with self._file_lock():
            stats = {
                'total_datasets': len(list(self.datasets_path.glob("*.json"))),
                'total_records': len(list(self.records_path.glob("*.json"))),
                'raw_data_files': len(list(self.raw_data_path.glob("*.json"))),
                'parsed_data_files': len(list(self.parsed_data_path.glob("*.json"))),
                'storage_path': str(self.base_path.absolute()),
                'disk_usage': self._get_directory_size(self.base_path)
            }
            return stats
    
    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                total_size += filepath.stat().st_size
        return total_size


# Singleton instance for global access
_storage_instance = None

def get_storage(base_path: str = "data") -> FileStorage:
    """Get storage instance (singleton pattern)"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = FileStorage(base_path)
    return _storage_instance