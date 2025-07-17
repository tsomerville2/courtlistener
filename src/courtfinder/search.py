"""
Search and lookup functionality for CourtFinder

Provides advanced search capabilities across CourtListener data
with filtering, sorting, and full-text search
"""

import re
from typing import List, Dict, Any, Optional, Union, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
import json
from enum import Enum

from .models import Court, Docket, OpinionCluster, Opinion, Citation, Person
from .storage import CourtFinderStorage


class SearchOperator(Enum):
    """Search operators for query construction"""
    EQUALS = "eq"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"
    FUZZY = "fuzzy"


class SortOrder(Enum):
    """Sort order options"""
    ASC = "asc"
    DESC = "desc"


@dataclass
class SearchFilter:
    """Individual search filter"""
    field: str
    operator: SearchOperator
    value: Any
    case_sensitive: bool = True
    
    def matches(self, obj: Any) -> bool:
        """Check if object matches this filter"""
        try:
            # Get field value from object
            field_value = getattr(obj, self.field, None)
            
            # Handle None values
            if field_value is None:
                return self.value is None and self.operator == SearchOperator.EQUALS
            
            # Convert to string for string operations
            if isinstance(field_value, str) and not self.case_sensitive:
                field_value = field_value.lower()
                if isinstance(self.value, str):
                    self.value = self.value.lower()
            
            # Apply operator
            if self.operator == SearchOperator.EQUALS:
                return field_value == self.value
            elif self.operator == SearchOperator.CONTAINS:
                return str(self.value) in str(field_value)
            elif self.operator == SearchOperator.STARTS_WITH:
                return str(field_value).startswith(str(self.value))
            elif self.operator == SearchOperator.ENDS_WITH:
                return str(field_value).endswith(str(self.value))
            elif self.operator == SearchOperator.GREATER_THAN:
                return field_value > self.value
            elif self.operator == SearchOperator.LESS_THAN:
                return field_value < self.value
            elif self.operator == SearchOperator.GREATER_EQUAL:
                return field_value >= self.value
            elif self.operator == SearchOperator.LESS_EQUAL:
                return field_value <= self.value
            elif self.operator == SearchOperator.BETWEEN:
                return self.value[0] <= field_value <= self.value[1]
            elif self.operator == SearchOperator.IN:
                return field_value in self.value
            elif self.operator == SearchOperator.NOT_IN:
                return field_value not in self.value
            elif self.operator == SearchOperator.REGEX:
                pattern = re.compile(str(self.value), re.IGNORECASE if not self.case_sensitive else 0)
                return bool(pattern.search(str(field_value)))
            elif self.operator == SearchOperator.FUZZY:
                # Simple fuzzy matching using edit distance
                return self._fuzzy_match(str(field_value), str(self.value))
            
            return False
            
        except Exception:
            return False
    
    def _fuzzy_match(self, text: str, pattern: str, max_distance: int = 2) -> bool:
        """Simple fuzzy matching using Levenshtein distance"""
        if abs(len(text) - len(pattern)) > max_distance:
            return False
        
        # Calculate Levenshtein distance
        d = [[0] * (len(pattern) + 1) for _ in range(len(text) + 1)]
        
        for i in range(len(text) + 1):
            d[i][0] = i
        for j in range(len(pattern) + 1):
            d[0][j] = j
        
        for i in range(1, len(text) + 1):
            for j in range(1, len(pattern) + 1):
                cost = 0 if text[i-1] == pattern[j-1] else 1
                d[i][j] = min(
                    d[i-1][j] + 1,      # deletion
                    d[i][j-1] + 1,      # insertion
                    d[i-1][j-1] + cost  # substitution
                )
        
        return d[len(text)][len(pattern)] <= max_distance


@dataclass
class SortCriteria:
    """Sort criteria for search results"""
    field: str
    order: SortOrder = SortOrder.ASC
    
    def sort_key(self, obj: Any) -> Any:
        """Get sort key for object"""
        value = getattr(obj, self.field, None)
        
        # Handle None values
        if value is None:
            return "" if self.order == SortOrder.ASC else "~"
        
        # Handle datetime and date objects
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        
        return value


@dataclass
class SearchQuery:
    """Complete search query with filters, sorting, and pagination"""
    filters: List[SearchFilter] = field(default_factory=list)
    sort_criteria: List[SortCriteria] = field(default_factory=list)
    limit: Optional[int] = None
    offset: int = 0
    full_text_query: Optional[str] = None
    
    def add_filter(self, field: str, operator: SearchOperator, value: Any, 
                  case_sensitive: bool = True) -> 'SearchQuery':
        """Add a filter to the query"""
        self.filters.append(SearchFilter(field, operator, value, case_sensitive))
        return self
    
    def add_sort(self, field: str, order: SortOrder = SortOrder.ASC) -> 'SearchQuery':
        """Add sort criteria to the query"""
        self.sort_criteria.append(SortCriteria(field, order))
        return self
    
    def set_pagination(self, limit: int, offset: int = 0) -> 'SearchQuery':
        """Set pagination parameters"""
        self.limit = limit
        self.offset = offset
        return self
    
    def set_full_text_search(self, query: str) -> 'SearchQuery':
        """Set full-text search query"""
        self.full_text_query = query
        return self
    
    def matches(self, obj: Any) -> bool:
        """Check if object matches all filters"""
        return all(filter.matches(obj) for filter in self.filters)
    
    def matches_full_text(self, obj: Any, text_extractor: Callable[[Any], str]) -> bool:
        """Check if object matches full-text query"""
        if not self.full_text_query:
            return True
        
        text = text_extractor(obj).lower()
        query_terms = self.full_text_query.lower().split()
        
        # All terms must be present (AND logic)
        return all(term in text for term in query_terms)


@dataclass
class SearchResult:
    """Search result with metadata"""
    results: List[Any]
    total_count: int
    filtered_count: int
    query: SearchQuery
    execution_time: float
    
    def has_more_results(self) -> bool:
        """Check if there are more results available"""
        if self.query.limit is None:
            return False
        return self.query.offset + len(self.results) < self.filtered_count


class CourtFinderSearch:
    """
    Main search engine for CourtFinder data
    """
    
    def __init__(self, storage: CourtFinderStorage):
        """
        Initialize search engine
        
        Args:
            storage: CourtFinderStorage instance
        """
        self.storage = storage
        
        # Text extractors for full-text search
        self.text_extractors = {
            Court: self._extract_court_text,
            Docket: self._extract_docket_text,
            OpinionCluster: self._extract_cluster_text,
            Opinion: self._extract_opinion_text,
            Citation: self._extract_citation_text,
            Person: self._extract_person_text
        }
    
    def _extract_court_text(self, court: Court) -> str:
        """Extract searchable text from court"""
        return ' '.join(filter(None, [
            court.full_name,
            court.short_name,
            court.jurisdiction,
            court.citation_string,
            court.notes
        ]))
    
    def _extract_docket_text(self, docket: Docket) -> str:
        """Extract searchable text from docket"""
        return ' '.join(filter(None, [
            docket.case_name,
            docket.case_name_short,
            docket.case_name_full,
            docket.docket_number,
            docket.source,
            docket.federal_dn_case_type
        ]))
    
    def _extract_cluster_text(self, cluster: OpinionCluster) -> str:
        """Extract searchable text from opinion cluster"""
        return ' '.join(filter(None, [
            cluster.case_name,
            cluster.case_name_short,
            cluster.case_name_full,
            cluster.judges,
            cluster.procedural_history,
            cluster.attorneys,
            cluster.nature_of_suit,
            cluster.posture,
            cluster.syllabus,
            cluster.headnotes,
            cluster.summary,
            cluster.disposition,
            cluster.history
        ]))
    
    def _extract_opinion_text(self, opinion: Opinion) -> str:
        """Extract searchable text from opinion"""
        return ' '.join(filter(None, [
            opinion.plain_text,
            opinion.html,
            opinion.sha1
        ]))
    
    def _extract_citation_text(self, citation: Citation) -> str:
        """Extract searchable text from citation"""
        return ' '.join(filter(None, [
            str(citation.cited_opinion_id),
            str(citation.citing_opinion_id),
            citation.parenthetical_text
        ]))
    
    def _extract_person_text(self, person: Person) -> str:
        """Extract searchable text from person"""
        return ' '.join(filter(None, [
            person.name_first,
            person.name_middle,
            person.name_last,
            person.name_suffix,
            person.dob_city,
            person.dob_state,
            person.dod_city,
            person.dod_state,
            person.gender,
            person.religion
        ]))
    
    def _search_storage(self, storage_attr: str, model_class: type, 
                       query: SearchQuery) -> SearchResult:
        """Search a specific storage"""
        start_time = datetime.now()
        
        # Get storage instance
        storage = getattr(self.storage, storage_attr)
        
        # Get all IDs
        all_ids = storage.list_all_ids()
        total_count = len(all_ids)
        
        # Load and filter objects
        filtered_objects = []
        text_extractor = self.text_extractors.get(model_class, lambda x: "")
        
        for obj_id in all_ids:
            obj = storage.load(obj_id)
            if obj is None:
                continue
            
            # Apply filters
            if not query.matches(obj):
                continue
            
            # Apply full-text search
            if not query.matches_full_text(obj, text_extractor):
                continue
            
            filtered_objects.append(obj)
        
        filtered_count = len(filtered_objects)
        
        # Sort results
        if query.sort_criteria:
            def sort_key(obj):
                keys = []
                for criteria in query.sort_criteria:
                    key = criteria.sort_key(obj)
                    keys.append(key)
                return keys
            
            # Apply reverse for descending order
            reverse = any(criteria.order == SortOrder.DESC for criteria in query.sort_criteria)
            filtered_objects.sort(key=sort_key, reverse=reverse)
        
        # Apply pagination
        start_idx = query.offset
        end_idx = start_idx + query.limit if query.limit else None
        results = filtered_objects[start_idx:end_idx]
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResult(
            results=results,
            total_count=total_count,
            filtered_count=filtered_count,
            query=query,
            execution_time=execution_time
        )
    
    def search_courts(self, query: SearchQuery) -> SearchResult:
        """Search courts"""
        return self._search_storage('courts', Court, query)
    
    def search_dockets(self, query: SearchQuery) -> SearchResult:
        """Search dockets"""
        return self._search_storage('dockets', Docket, query)
    
    def search_opinion_clusters(self, query: SearchQuery) -> SearchResult:
        """Search opinion clusters"""
        return self._search_storage('opinion_clusters', OpinionCluster, query)
    
    def search_opinions(self, query: SearchQuery) -> SearchResult:
        """Search opinions"""
        return self._search_storage('opinions', Opinion, query)
    
    def search_citations(self, query: SearchQuery) -> SearchResult:
        """Search citations"""
        return self._search_storage('citations', Citation, query)
    
    def search_people(self, query: SearchQuery) -> SearchResult:
        """Search people"""
        return self._search_storage('people', Person, query)
    
    def find_court_by_name(self, name: str, exact: bool = False) -> List[Court]:
        """Find courts by name"""
        query = SearchQuery()
        
        if exact:
            query.add_filter('full_name', SearchOperator.EQUALS, name, case_sensitive=False)
        else:
            query.add_filter('full_name', SearchOperator.CONTAINS, name, case_sensitive=False)
        
        result = self.search_courts(query)
        return result.results
    
    def find_dockets_by_case_name(self, case_name: str, court_id: Optional[int] = None) -> List[Docket]:
        """Find dockets by case name"""
        query = SearchQuery()
        query.add_filter('case_name', SearchOperator.CONTAINS, case_name, case_sensitive=False)
        
        if court_id:
            query.add_filter('court_id', SearchOperator.EQUALS, court_id)
        
        result = self.search_dockets(query)
        return result.results
    
    def find_opinions_by_text(self, text: str, limit: int = 100) -> List[Opinion]:
        """Find opinions containing specific text"""
        query = SearchQuery()
        query.set_full_text_search(text)
        query.set_pagination(limit)
        
        result = self.search_opinions(query)
        return result.results
    
    def find_citations_by_opinion(self, opinion_id: int) -> List[Citation]:
        """Find all citations for an opinion"""
        query = SearchQuery()
        query.add_filter('cited_opinion_id', SearchOperator.EQUALS, opinion_id)
        
        result = self.search_citations(query)
        citing_citations = result.results
        
        # Also find citations where this opinion cites others
        query2 = SearchQuery()
        query2.add_filter('citing_opinion_id', SearchOperator.EQUALS, opinion_id)
        
        result2 = self.search_citations(query2)
        cited_citations = result2.results
        
        return citing_citations + cited_citations
    
    def find_person_by_name(self, name: str, fuzzy: bool = False) -> List[Person]:
        """Find person by name"""
        query = SearchQuery()
        
        if fuzzy:
            query.add_filter('name_last', SearchOperator.FUZZY, name, case_sensitive=False)
        else:
            query.set_full_text_search(name)
        
        result = self.search_people(query)
        return result.results
    
    def get_case_hierarchy(self, docket_id: int) -> Dict[str, Any]:
        """Get complete case hierarchy (docket -> clusters -> opinions)"""
        # Get docket
        docket = self.storage.get_docket(docket_id)
        if not docket:
            return {}
        
        # Get opinion clusters for this docket
        clusters = self.storage.find_clusters_by_docket(docket_id)
        
        # Get opinions for each cluster
        hierarchy = {
            'docket': docket,
            'clusters': []
        }
        
        for cluster in clusters:
            opinions = self.storage.find_opinions_by_cluster(cluster.id)
            hierarchy['clusters'].append({
                'cluster': cluster,
                'opinions': opinions
            })
        
        return hierarchy
    
    def get_citation_network(self, opinion_id: int, depth: int = 1) -> Dict[str, Any]:
        """Get citation network for an opinion"""
        visited = set()
        network = {'nodes': [], 'edges': []}
        
        def collect_citations(current_id: int, current_depth: int):
            if current_depth > depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # Get opinion
            opinion = self.storage.get_opinion(current_id)
            if opinion:
                network['nodes'].append({
                    'id': current_id,
                    'opinion': opinion,
                    'depth': current_depth
                })
            
            # Get citations
            citations = self.find_citations_by_opinion(current_id)
            for citation in citations:
                network['edges'].append({
                    'citing_id': citation.citing_opinion_id,
                    'cited_id': citation.cited_opinion_id,
                    'depth': citation.depth,
                    'quoted': citation.quoted
                })
                
                # Recursively collect citations
                if citation.citing_opinion_id != current_id:
                    collect_citations(citation.citing_opinion_id, current_depth + 1)
                if citation.cited_opinion_id != current_id:
                    collect_citations(citation.cited_opinion_id, current_depth + 1)
        
        collect_citations(opinion_id, 0)
        return network
    
    def search_advanced(self, query_dict: Dict[str, Any]) -> SearchResult:
        """
        Advanced search with complex query structure
        
        Args:
            query_dict: Query dictionary with filters, sorting, etc.
            
        Returns:
            SearchResult
        """
        query = SearchQuery()
        
        # Parse filters
        for filter_dict in query_dict.get('filters', []):
            query.add_filter(
                filter_dict['field'],
                SearchOperator(filter_dict['operator']),
                filter_dict['value'],
                filter_dict.get('case_sensitive', True)
            )
        
        # Parse sorting
        for sort_dict in query_dict.get('sort', []):
            query.add_sort(
                sort_dict['field'],
                SortOrder(sort_dict.get('order', 'asc'))
            )
        
        # Parse pagination
        if 'limit' in query_dict:
            query.set_pagination(
                query_dict['limit'],
                query_dict.get('offset', 0)
            )
        
        # Parse full-text search
        if 'full_text' in query_dict:
            query.set_full_text_search(query_dict['full_text'])
        
        # Determine search type
        search_type = query_dict.get('type', 'opinions')
        
        if search_type == 'courts':
            return self.search_courts(query)
        elif search_type == 'dockets':
            return self.search_dockets(query)
        elif search_type == 'opinion_clusters':
            return self.search_opinion_clusters(query)
        elif search_type == 'opinions':
            return self.search_opinions(query)
        elif search_type == 'citations':
            return self.search_citations(query)
        elif search_type == 'people':
            return self.search_people(query)
        else:
            raise ValueError(f"Unknown search type: {search_type}")
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            'storage_stats': self.storage.get_storage_stats(),
            'supported_search_types': ['courts', 'dockets', 'opinion_clusters', 'opinions', 'citations', 'people'],
            'available_operators': [op.value for op in SearchOperator],
            'sort_orders': [order.value for order in SortOrder]
        }