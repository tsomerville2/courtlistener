"""
CourtListener API Client

Handles authentication, rate limiting, and data downloading from CourtListener.com
Based on real API documentation: https://www.courtlistener.com/help/api/
"""

import requests
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import gzip
import bz2
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from .models import Court, Docket, OpinionCluster, Opinion, Citation, Person


@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    limit: int
    remaining: int
    reset_time: datetime
    
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted"""
        return self.remaining <= 0
    
    def seconds_until_reset(self) -> int:
        """Get seconds until rate limit resets"""
        return max(0, int((self.reset_time - datetime.now()).total_seconds()))


class CourtListenerAPIError(Exception):
    """Base exception for CourtListener API errors"""
    pass


class RateLimitExceededError(CourtListenerAPIError):
    """Rate limit exceeded error"""
    pass


class AuthenticationError(CourtListenerAPIError):
    """Authentication error"""
    pass


class CourtListenerAPIClient:
    """
    Client for CourtListener REST API v4
    
    Handles authentication, rate limiting, and data fetching
    """
    
    BASE_URL = "https://www.courtlistener.com/api/rest/v4/"
    BULK_DATA_URL = "https://www.courtlistener.com/api/bulk-data/"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize API client
        
        Args:
            token: Authentication token (optional, reduces rate limits)
        """
        self.token = token
        self.session = requests.Session()
        
        # Set up authentication
        if self.token:
            self.session.headers.update({
                'Authorization': f'Token {self.token}'
            })
        
        # Set up default headers
        self.session.headers.update({
            'User-Agent': 'CourtFinder-CLI/1.0 (https://github.com/courtfinder)',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Rate limiting
        self.rate_limit_info: Optional[RateLimitInfo] = None
        self.last_request_time: Optional[datetime] = None
        
        # Request history for debugging
        self.request_history: List[Dict[str, Any]] = []
    
    def _update_rate_limit_info(self, response: requests.Response):
        """Update rate limit information from response headers"""
        if 'X-RateLimit-Limit' in response.headers:
            limit = int(response.headers['X-RateLimit-Limit'])
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            reset_timestamp = int(response.headers.get('X-RateLimit-Reset', 0))
            reset_time = datetime.fromtimestamp(reset_timestamp) if reset_timestamp else datetime.now()
            
            self.rate_limit_info = RateLimitInfo(limit, remaining, reset_time)
    
    def _wait_for_rate_limit(self):
        """Wait if rate limit is exhausted"""
        if self.rate_limit_info and self.rate_limit_info.is_exhausted():
            sleep_time = self.rate_limit_info.seconds_until_reset() + 1
            print(f"Rate limit exhausted. Waiting {sleep_time} seconds...")
            time.sleep(sleep_time)
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with rate limiting and error handling"""
        # Wait for rate limit
        self._wait_for_rate_limit()
        
        # Add delay between requests
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < 0.1:  # Minimum 100ms between requests
                time.sleep(0.1 - elapsed)
        
        try:
            response = self.session.request(method, url, **kwargs)
            self.last_request_time = datetime.now()
            
            # Update rate limit info
            self._update_rate_limit_info(response)
            
            # Log request
            self.request_history.append({
                'method': method,
                'url': url,
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat()
            })
            
            # Handle errors
            if response.status_code == 429:
                raise RateLimitExceededError("Rate limit exceeded")
            elif response.status_code == 401:
                raise AuthenticationError("Authentication failed")
            elif response.status_code >= 400:
                raise CourtListenerAPIError(f"API request failed: {response.status_code} - {response.text}")
            
            return response
            
        except requests.RequestException as e:
            raise CourtListenerAPIError(f"Request failed: {str(e)}")
    
    def _get_absolute_url(self, endpoint: str) -> str:
        """Get absolute URL for endpoint"""
        return urljoin(self.BASE_URL, endpoint.lstrip('/'))
    
    def get_courts(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get courts from API"""
        params = {'limit': limit, 'offset': offset}
        response = self._make_request('GET', self._get_absolute_url('courts/'), params=params)
        return response.json()
    
    def get_court(self, court_id: int) -> Court:
        """Get specific court by ID"""
        response = self._make_request('GET', self._get_absolute_url(f'courts/{court_id}/'))
        data = response.json()
        return Court.from_dict(data)
    
    def get_dockets(self, court_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get dockets from API"""
        params = {'limit': limit, 'offset': offset}
        if court_id:
            params['court'] = court_id
        
        response = self._make_request('GET', self._get_absolute_url('dockets/'), params=params)
        return response.json()
    
    def get_docket(self, docket_id: int) -> Docket:
        """Get specific docket by ID"""
        response = self._make_request('GET', self._get_absolute_url(f'dockets/{docket_id}/'))
        data = response.json()
        return Docket.from_dict(data)
    
    def get_opinion_clusters(self, docket_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get opinion clusters from API"""
        params = {'limit': limit, 'offset': offset}
        if docket_id:
            params['docket'] = docket_id
        
        response = self._make_request('GET', self._get_absolute_url('clusters/'), params=params)
        return response.json()
    
    def get_opinion_cluster(self, cluster_id: int) -> OpinionCluster:
        """Get specific opinion cluster by ID"""
        response = self._make_request('GET', self._get_absolute_url(f'clusters/{cluster_id}/'))
        data = response.json()
        return OpinionCluster.from_dict(data)
    
    def get_opinions(self, cluster_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get opinions from API"""
        params = {'limit': limit, 'offset': offset}
        if cluster_id:
            params['cluster'] = cluster_id
        
        response = self._make_request('GET', self._get_absolute_url('opinions/'), params=params)
        return response.json()
    
    def get_opinion(self, opinion_id: int) -> Opinion:
        """Get specific opinion by ID"""
        response = self._make_request('GET', self._get_absolute_url(f'opinions/{opinion_id}/'))
        data = response.json()
        return Opinion.from_dict(data)
    
    def get_people(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get people from API"""
        params = {'limit': limit, 'offset': offset}
        response = self._make_request('GET', self._get_absolute_url('people/'), params=params)
        return response.json()
    
    def get_person(self, person_id: int) -> Person:
        """Get specific person by ID"""
        response = self._make_request('GET', self._get_absolute_url(f'people/{person_id}/'))
        data = response.json()
        return Person.from_dict(data)
    
    def search_opinions(self, query: str, court: Optional[str] = None, 
                       limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Search opinions"""
        params = {
            'q': query,
            'limit': limit,
            'offset': offset
        }
        if court:
            params['court'] = court
        
        response = self._make_request('GET', self._get_absolute_url('search/'), params=params)
        return response.json()
    
    def get_api_info(self) -> Dict[str, Any]:
        """Get API information and field definitions"""
        response = self._make_request('OPTIONS', self._get_absolute_url(''))
        return response.json()
    
    def get_rate_limit_status(self) -> Optional[RateLimitInfo]:
        """Get current rate limit status"""
        return self.rate_limit_info
    
    def get_request_history(self) -> List[Dict[str, Any]]:
        """Get request history for debugging"""
        return self.request_history.copy()


class BulkDataDownloader:
    """
    Downloads bulk data files from CourtListener
    
    Handles compressed files and parallel downloads
    """
    
    BASE_URL = "https://www.courtlistener.com/api/bulk-data/"
    
    def __init__(self, download_dir: str = "downloads"):
        """
        Initialize bulk data downloader
        
        Args:
            download_dir: Directory to save downloaded files
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CourtFinder-CLI/1.0 (https://github.com/courtfinder)'
        })
    
    def list_available_files(self) -> List[Dict[str, Any]]:
        """List available bulk data files"""
        # This would normally parse the bulk data page
        # For now, return known file patterns
        return [
            {
                'name': 'courts.csv.bz2',
                'description': 'Court metadata',
                'url': urljoin(self.BASE_URL, 'courts.csv.bz2')
            },
            {
                'name': 'dockets.csv.bz2',
                'description': 'Docket information',
                'url': urljoin(self.BASE_URL, 'dockets.csv.bz2')
            },
            {
                'name': 'opinion_clusters.csv.bz2',
                'description': 'Opinion clusters',
                'url': urljoin(self.BASE_URL, 'opinion_clusters.csv.bz2')
            },
            {
                'name': 'opinions.csv.bz2',
                'description': 'Individual opinions',
                'url': urljoin(self.BASE_URL, 'opinions.csv.bz2')
            },
            {
                'name': 'citations.csv.bz2',
                'description': 'Citation relationships',
                'url': urljoin(self.BASE_URL, 'citations.csv.bz2')
            },
            {
                'name': 'people.csv.bz2',
                'description': 'Judges and attorneys',
                'url': urljoin(self.BASE_URL, 'people.csv.bz2')
            }
        ]
    
    def download_file(self, url: str, filename: Optional[str] = None, 
                     show_progress: bool = True) -> Path:
        """
        Download a single file with progress tracking
        
        Args:
            url: URL to download
            filename: Local filename (optional)
            show_progress: Show download progress
            
        Returns:
            Path to downloaded file
        """
        if filename is None:
            filename = Path(urlparse(url).path).name
        
        file_path = self.download_dir / filename
        
        print(f"Downloading {url} to {file_path}")
        
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if show_progress and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\\rProgress: {progress:.1f}%", end='', flush=True)
            
            if show_progress:
                print()  # New line after progress
            
            print(f"Downloaded {file_path} ({downloaded} bytes)")
            return file_path
            
        except requests.RequestException as e:
            raise CourtListenerAPIError(f"Download failed: {str(e)}")
    
    def download_bulk_data(self, data_types: List[str], 
                          max_workers: int = 3) -> List[Path]:
        """
        Download multiple bulk data files in parallel
        
        Args:
            data_types: List of data types to download (e.g., ['courts', 'dockets'])
            max_workers: Maximum number of parallel downloads
            
        Returns:
            List of downloaded file paths
        """
        available_files = self.list_available_files()
        files_to_download = []
        
        for data_type in data_types:
            for file_info in available_files:
                if data_type in file_info['name']:
                    files_to_download.append(file_info)
                    break
        
        downloaded_files = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.download_file, file_info['url'], file_info['name']): file_info
                for file_info in files_to_download
            }
            
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                try:
                    file_path = future.result()
                    downloaded_files.append(file_path)
                    print(f"Completed download: {file_info['name']}")
                except Exception as e:
                    print(f"Failed to download {file_info['name']}: {e}")
        
        return downloaded_files
    
    def extract_compressed_file(self, file_path: Path, 
                               output_path: Optional[Path] = None) -> Path:
        """
        Extract compressed file (supports .bz2 and .gz)
        
        Args:
            file_path: Path to compressed file
            output_path: Path for extracted file (optional)
            
        Returns:
            Path to extracted file
        """
        if output_path is None:
            if file_path.suffix == '.bz2':
                output_path = file_path.with_suffix('')
            elif file_path.suffix == '.gz':
                output_path = file_path.with_suffix('')
            else:
                output_path = file_path.with_suffix('.extracted')
        
        print(f"Extracting {file_path} to {output_path}")
        
        try:
            if file_path.suffix == '.bz2':
                with bz2.open(file_path, 'rt', encoding='utf-8') as compressed_file:
                    with open(output_path, 'w', encoding='utf-8') as output_file:
                        output_file.write(compressed_file.read())
            elif file_path.suffix == '.gz':
                with gzip.open(file_path, 'rt', encoding='utf-8') as compressed_file:
                    with open(output_path, 'w', encoding='utf-8') as output_file:
                        output_file.write(compressed_file.read())
            else:
                raise ValueError(f"Unsupported compression format: {file_path.suffix}")
            
            print(f"Extracted to {output_path}")
            return output_path
            
        except Exception as e:
            raise CourtListenerAPIError(f"Extraction failed: {str(e)}")
    
    def download_and_extract(self, data_types: List[str], 
                           cleanup_compressed: bool = True) -> List[Path]:
        """
        Download and extract bulk data files
        
        Args:
            data_types: List of data types to download
            cleanup_compressed: Remove compressed files after extraction
            
        Returns:
            List of extracted file paths
        """
        downloaded_files = self.download_bulk_data(data_types)
        extracted_files = []
        
        for file_path in downloaded_files:
            if file_path.suffix in ['.bz2', '.gz']:
                extracted_path = self.extract_compressed_file(file_path)
                extracted_files.append(extracted_path)
                
                if cleanup_compressed:
                    file_path.unlink()
                    print(f"Removed compressed file: {file_path}")
            else:
                extracted_files.append(file_path)
        
        return extracted_files
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get download directory statistics"""
        files = list(self.download_dir.glob('*'))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        return {
            'download_directory': str(self.download_dir),
            'total_files': len(files),
            'total_size_bytes': total_size,
            'files': [{'name': f.name, 'size': f.stat().st_size} for f in files if f.is_file()]
        }