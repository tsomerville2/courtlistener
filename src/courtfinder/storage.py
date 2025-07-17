"""
File-based storage system for CourtFinder data persistence

Uses JSON files for storing CourtListener data with efficient indexing
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, TypeVar, Generic, Type, Union
from datetime import datetime, date
from dataclasses import asdict
import gzip
import threading
from concurrent.futures import ThreadPoolExecutor

from .models import Court, Docket, OpinionCluster, Opinion, Citation, Person

T = TypeVar('T')


class StorageError(Exception):
    """Base exception for storage operations"""
    pass


class FileStorage(Generic[T]):
    """
    Generic file-based storage for CourtListener models
    Handles JSON serialization, compression, and indexing
    """
    
    def __init__(self, base_path: str, model_class: Type[T], use_compression: bool = True):
        self.base_path = Path(base_path)
        self.model_class = model_class
        self.use_compression = use_compression
        self.lock = threading.RLock()
        
        # Create directory structure
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.data_path = self.base_path / "data"
        self.index_path = self.base_path / "indexes"
        self.data_path.mkdir(exist_ok=True)
        self.index_path.mkdir(exist_ok=True)
        
        # Load or create indexes
        self._load_indexes()
    
    def _load_indexes(self):
        """Load existing indexes or create new ones"""
        self.id_index = self._load_index("id_index.json", {})
        self.field_indexes = {}
        
        # Load field indexes
        for index_file in self.index_path.glob("*_index.json"):
            if index_file.name != "id_index.json":
                field_name = index_file.stem.replace("_index", "")
                self.field_indexes[field_name] = self._load_index(index_file.name, {})
    
    def _load_index(self, filename: str, default: dict) -> dict:
        """Load index from file"""
        index_file = self.index_path / filename
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return default
    
    def _save_index(self, filename: str, index: dict):
        """Save index to file"""
        index_file = self.index_path / filename
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _get_file_path(self, item_id: Union[int, str]) -> Path:
        """Get file path for an item"""
        filename = f"{item_id}.json"
        if self.use_compression:
            filename += ".gz"
        return self.data_path / filename
    
    def _serialize_item(self, item: T) -> dict:
        """Serialize item to dictionary"""
        if hasattr(item, 'to_dict'):
            return item.to_dict()
        return asdict(item)
    
    def _deserialize_item(self, data: dict) -> T:
        """Deserialize dictionary to item"""
        if hasattr(self.model_class, 'from_dict'):
            return self.model_class.from_dict(data)
        return self.model_class(**data)
    
    def _save_data(self, file_path: Path, data: dict):
        """Save data to file with optional compression"""
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        if self.use_compression:
            with gzip.open(file_path, 'wt', encoding='utf-8') as f:
                f.write(json_data)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data)
    
    def _load_data(self, file_path: Path) -> dict:
        """Load data from file with optional compression"""
        if self.use_compression:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def _update_indexes(self, item_id: Union[int, str], item: T):
        """Update indexes for an item"""
        with self.lock:
            # Update ID index
            self.id_index[str(item_id)] = {
                'created': datetime.now().isoformat(),
                'file_path': str(self._get_file_path(item_id))
            }
            
            # Update field indexes
            item_data = self._serialize_item(item)
            for field, value in item_data.items():
                if value is not None and field not in ['date_created', 'date_modified']:
                    if field not in self.field_indexes:
                        self.field_indexes[field] = {}
                    
                    str_value = str(value)[:100]  # Limit index key length
                    if str_value not in self.field_indexes[field]:
                        self.field_indexes[field][str_value] = []
                    
                    if str(item_id) not in self.field_indexes[field][str_value]:
                        self.field_indexes[field][str_value].append(str(item_id))
    
    def _save_indexes(self):
        """Save all indexes to disk"""
        with self.lock:
            self._save_index("id_index.json", self.id_index)
            for field, index in self.field_indexes.items():
                self._save_index(f"{field}_index.json", index)
    
    def save(self, item: T) -> bool:
        """Save item to storage"""
        try:
            # Get item ID
            item_id = getattr(item, 'id', None)
            if item_id is None:
                raise StorageError("Item must have an 'id' attribute")
            
            # Serialize and save data
            data = self._serialize_item(item)
            file_path = self._get_file_path(item_id)
            self._save_data(file_path, data)
            
            # Update indexes
            self._update_indexes(item_id, item)
            self._save_indexes()
            
            return True
            
        except Exception as e:
            raise StorageError(f"Failed to save item {item_id}: {str(e)}")
    
    def save_batch(self, items: List[T]) -> int:
        """Save multiple items efficiently"""
        saved_count = 0
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for item in items:
                future = executor.submit(self._save_single_item, item)
                futures.append(future)
            
            for future in futures:
                try:
                    if future.result():
                        saved_count += 1
                except Exception as e:
                    # Log error but continue with other items
                    print(f"Error saving item: {e}")
        
        # Save indexes after batch
        self._save_indexes()
        return saved_count
    
    def _save_single_item(self, item: T) -> bool:
        """Save single item without updating indexes immediately"""
        try:
            item_id = getattr(item, 'id', None)
            if item_id is None:
                return False
            
            data = self._serialize_item(item)
            file_path = self._get_file_path(item_id)
            self._save_data(file_path, data)
            
            self._update_indexes(item_id, item)
            return True
            
        except Exception:
            return False
    
    def load(self, item_id: Union[int, str]) -> Optional[T]:
        """Load item by ID"""
        try:
            file_path = self._get_file_path(item_id)
            
            if not file_path.exists():
                return None
            
            data = self._load_data(file_path)
            return self._deserialize_item(data)
            
        except Exception as e:
            raise StorageError(f"Failed to load item {item_id}: {str(e)}")
    
    def load_batch(self, item_ids: List[Union[int, str]]) -> List[T]:
        """Load multiple items efficiently"""
        items = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(self.load, item_id): item_id for item_id in item_ids}
            
            for future in futures:
                try:
                    item = future.result()
                    if item is not None:
                        items.append(item)
                except Exception as e:
                    # Log error but continue with other items
                    print(f"Error loading item {futures[future]}: {e}")
        
        return items
    
    def exists(self, item_id: Union[int, str]) -> bool:
        """Check if item exists"""
        return self._get_file_path(item_id).exists()
    
    def delete(self, item_id: Union[int, str]) -> bool:
        """Delete item from storage"""
        try:
            file_path = self._get_file_path(item_id)
            
            if file_path.exists():
                file_path.unlink()
            
            # Remove from indexes
            with self.lock:
                str_id = str(item_id)
                if str_id in self.id_index:
                    del self.id_index[str_id]
                
                # Remove from field indexes
                for field_index in self.field_indexes.values():
                    for value_list in field_index.values():
                        if str_id in value_list:
                            value_list.remove(str_id)
                
                self._save_indexes()
            
            return True
            
        except Exception as e:
            raise StorageError(f"Failed to delete item {item_id}: {str(e)}")
    
    def find_by_field(self, field: str, value: Any) -> List[T]:
        """Find items by field value"""
        if field not in self.field_indexes:
            return []
        
        str_value = str(value)[:100]
        if str_value not in self.field_indexes[field]:
            return []
        
        item_ids = self.field_indexes[field][str_value]
        return self.load_batch(item_ids)
    
    def list_all_ids(self) -> List[str]:
        """List all item IDs"""
        return list(self.id_index.keys())
    
    def count(self) -> int:
        """Count total items"""
        return len(self.id_index)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            'total_items': self.count(),
            'storage_path': str(self.base_path),
            'compression_enabled': self.use_compression,
            'indexed_fields': list(self.field_indexes.keys()),
            'disk_usage': sum(f.stat().st_size for f in self.data_path.glob('*') if f.is_file())
        }


class CourtFinderStorage:
    """
    Main storage coordinator for all CourtFinder data
    """
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage for each model type
        self.courts = FileStorage(str(self.base_path / "courts"), Court)
        self.dockets = FileStorage(str(self.base_path / "dockets"), Docket)
        self.opinion_clusters = FileStorage(str(self.base_path / "opinion_clusters"), OpinionCluster)
        self.opinions = FileStorage(str(self.base_path / "opinions"), Opinion)
        self.citations = FileStorage(str(self.base_path / "citations"), Citation)
        self.people = FileStorage(str(self.base_path / "people"), Person)
    
    def save_court(self, court: Court) -> bool:
        """Save court to storage"""
        return self.courts.save(court)
    
    def save_docket(self, docket: Docket) -> bool:
        """Save docket to storage"""
        return self.dockets.save(docket)
    
    def save_opinion_cluster(self, cluster: OpinionCluster) -> bool:
        """Save opinion cluster to storage"""
        return self.opinion_clusters.save(cluster)
    
    def save_opinion(self, opinion: Opinion) -> bool:
        """Save opinion to storage"""
        return self.opinions.save(opinion)
    
    def save_citation(self, citation: Citation) -> bool:
        """Save citation to storage"""
        # For citations, use a composite key
        citation_id = f"{citation.citing_opinion_id}_{citation.cited_opinion_id}"
        # Store the composite ID in the citation object
        citation.id = citation_id
        return self.citations.save(citation)
    
    def save_person(self, person: Person) -> bool:
        """Save person to storage"""
        return self.people.save(person)
    
    def get_court(self, court_id: int) -> Optional[Court]:
        """Get court by ID"""
        return self.courts.load(court_id)
    
    def get_docket(self, docket_id: int) -> Optional[Docket]:
        """Get docket by ID"""
        return self.dockets.load(docket_id)
    
    def get_opinion_cluster(self, cluster_id: int) -> Optional[OpinionCluster]:
        """Get opinion cluster by ID"""
        return self.opinion_clusters.load(cluster_id)
    
    def get_opinion(self, opinion_id: int) -> Optional[Opinion]:
        """Get opinion by ID"""
        return self.opinions.load(opinion_id)
    
    def get_person(self, person_id: int) -> Optional[Person]:
        """Get person by ID"""
        return self.people.load(person_id)
    
    def find_dockets_by_court(self, court_id: int) -> List[Docket]:
        """Find all dockets for a court"""
        return self.dockets.find_by_field('court_id', court_id)
    
    def find_clusters_by_docket(self, docket_id: int) -> List[OpinionCluster]:
        """Find all opinion clusters for a docket"""
        return self.opinion_clusters.find_by_field('docket_id', docket_id)
    
    def find_opinions_by_cluster(self, cluster_id: int) -> List[Opinion]:
        """Find all opinions for a cluster"""
        return self.opinions.find_by_field('cluster_id', cluster_id)
    
    def find_citations_by_opinion(self, opinion_id: int) -> List[Citation]:
        """Find all citations for an opinion (both citing and cited)"""
        citing = self.citations.find_by_field('citing_opinion_id', opinion_id)
        cited = self.citations.find_by_field('cited_opinion_id', opinion_id)
        return citing + cited
    
    def search_courts(self, query: str) -> List[Court]:
        """Search courts by name or jurisdiction"""
        results = []
        results.extend(self.courts.find_by_field('full_name', query))
        results.extend(self.courts.find_by_field('jurisdiction', query))
        # Remove duplicates
        return list({court.id: court for court in results}.values())
    
    def search_dockets(self, case_name: str) -> List[Docket]:
        """Search dockets by case name"""
        return self.dockets.find_by_field('case_name', case_name)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        return {
            'courts': self.courts.get_stats(),
            'dockets': self.dockets.get_stats(),
            'opinion_clusters': self.opinion_clusters.get_stats(),
            'opinions': self.opinions.get_stats(),
            'citations': self.citations.get_stats(),
            'people': self.people.get_stats(),
            'total_disk_usage': sum(
                storage.get_stats()['disk_usage'] for storage in [
                    self.courts, self.dockets, self.opinion_clusters,
                    self.opinions, self.citations, self.people
                ]
            )
        }
    
    def cleanup_indexes(self):
        """Clean up and rebuild all indexes"""
        for storage in [self.courts, self.dockets, self.opinion_clusters, 
                       self.opinions, self.citations, self.people]:
            storage._save_indexes()