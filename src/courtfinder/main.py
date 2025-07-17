"""
Main CourtFinder CLI Module

Integrates all components: API client, CSV parser, storage, and search
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse
import json
from datetime import datetime

from .api_client import CourtListenerAPIClient, BulkDataDownloader
from .csv_parser import BulkCSVParser
from .storage import CourtFinderStorage
from .search import CourtFinderSearch, SearchQuery, SearchOperator, SortOrder
from .models import Court, Docket, OpinionCluster, Opinion, Citation, Person


class CourtFinderCLI:
    """
    Main CLI application for CourtFinder
    """
    
    def __init__(self, data_dir: str = "data", token: Optional[str] = None):
        """
        Initialize CourtFinder CLI
        
        Args:
            data_dir: Directory for data storage
            token: CourtListener API token (optional)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.api_client = CourtListenerAPIClient(token)
        self.bulk_downloader = BulkDataDownloader(str(self.data_dir / "downloads"))
        self.csv_parser = BulkCSVParser()
        self.storage = CourtFinderStorage(str(self.data_dir))
        self.search = CourtFinderSearch(self.storage)
        
        print(f"CourtFinder CLI initialized with data directory: {self.data_dir}")
    
    def download_bulk_data(self, data_types: List[str], extract: bool = True) -> List[Path]:
        """
        Download bulk data from CourtListener
        
        Args:
            data_types: List of data types to download
            extract: Whether to extract compressed files
            
        Returns:
            List of downloaded/extracted file paths
        """
        print(f"Downloading bulk data: {', '.join(data_types)}")
        
        if extract:
            files = self.bulk_downloader.download_and_extract(data_types)
        else:
            files = self.bulk_downloader.download_bulk_data(data_types)
        
        print(f"Downloaded {len(files)} files")
        return files
    
    def import_csv_data(self, file_path: Path, data_type: str, 
                       limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Import CSV data into storage
        
        Args:
            file_path: Path to CSV file
            data_type: Type of data (courts, dockets, etc.)
            limit: Maximum number of records to import
            
        Returns:
            Import statistics
        """
        print(f"Importing {data_type} data from {file_path}")
        
        # Validate CSV structure
        validation = self.csv_parser.validate_csv_structure(file_path, data_type)
        if not validation['valid']:
            print(f"CSV validation failed: {validation['error']}")
            return {'success': False, 'error': validation['error']}
        
        # Parse and import data
        start_time = datetime.now()
        imported_count = 0
        error_count = 0
        
        try:
            for obj in self.csv_parser.parse_file(file_path, data_type, limit):
                try:
                    # Save to appropriate storage
                    if data_type == 'courts':
                        self.storage.save_court(obj)
                    elif data_type == 'dockets':
                        self.storage.save_docket(obj)
                    elif data_type == 'opinion_clusters':
                        self.storage.save_opinion_cluster(obj)
                    elif data_type == 'opinions':
                        self.storage.save_opinion(obj)
                    elif data_type == 'citations':
                        self.storage.save_citation(obj)
                    elif data_type == 'people':
                        self.storage.save_person(obj)
                    
                    imported_count += 1
                    
                    if imported_count % 1000 == 0:
                        print(f"Imported {imported_count} records...")
                        
                except Exception as e:
                    error_count += 1
                    print(f"Error importing record: {e}")
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'imported_count': imported_count,
                'error_count': error_count
            }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"Import completed: {imported_count} records imported, {error_count} errors")
        print(f"Execution time: {execution_time:.2f} seconds")
        
        return {
            'success': True,
            'imported_count': imported_count,
            'error_count': error_count,
            'execution_time': execution_time
        }
    
    def search_courts(self, query: str, limit: int = 10) -> List[Court]:
        """Search courts by name or jurisdiction"""
        results = self.search.find_court_by_name(query)
        return results[:limit]
    
    def search_cases(self, case_name: str, court_id: Optional[int] = None, 
                    limit: int = 10) -> List[Docket]:
        """Search cases by name"""
        results = self.search.find_dockets_by_case_name(case_name, court_id)
        return results[:limit]
    
    def search_opinions(self, text: str, limit: int = 10) -> List[Opinion]:
        """Search opinions by text content"""
        return self.search.find_opinions_by_text(text, limit)
    
    def search_judges(self, name: str, limit: int = 10) -> List[Person]:
        """Search judges by name"""
        results = self.search.find_person_by_name(name, fuzzy=True)
        return results[:limit]
    
    def get_case_details(self, docket_id: int) -> Dict[str, Any]:
        """Get complete case details"""
        return self.search.get_case_hierarchy(docket_id)
    
    def get_citation_network(self, opinion_id: int, depth: int = 1) -> Dict[str, Any]:
        """Get citation network for an opinion"""
        return self.search.get_citation_network(opinion_id, depth)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            'storage_stats': self.storage.get_storage_stats(),
            'search_stats': self.search.get_search_stats(),
            'download_stats': self.bulk_downloader.get_download_stats(),
            'api_rate_limit': self.api_client.get_rate_limit_status()
        }
    
    def run_interactive_search(self):
        """Run interactive search interface"""
        print("CourtFinder Interactive Search")
        print("Commands: courts, cases, opinions, judges, case-details, citations, stats, quit")
        
        while True:
            try:
                command = input("\ncourtfinder> ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'courts':
                    query = input("Search courts: ")
                    results = self.search_courts(query)
                    for court in results:
                        print(f"  {court.id}: {court.full_name} ({court.jurisdiction})")
                
                elif command == 'cases':
                    case_name = input("Case name: ")
                    court_id = input("Court ID (optional): ")
                    court_id = int(court_id) if court_id else None
                    
                    results = self.search_cases(case_name, court_id)
                    for docket in results:
                        print(f"  {docket.id}: {docket.case_name} - {docket.docket_number}")
                
                elif command == 'opinions':
                    text = input("Search text: ")
                    results = self.search_opinions(text)
                    for opinion in results:
                        print(f"  {opinion.id}: {opinion.type.value} (cluster: {opinion.cluster_id})")
                
                elif command == 'judges':
                    name = input("Judge name: ")
                    results = self.search_judges(name)
                    for person in results:
                        print(f"  {person.id}: {person.get_full_name()}")
                
                elif command == 'case-details':
                    docket_id = int(input("Docket ID: "))
                    details = self.get_case_details(docket_id)
                    if details:
                        print(f"Case: {details['docket'].case_name}")
                        print(f"Clusters: {len(details['clusters'])}")
                        for cluster_info in details['clusters']:
                            print(f"  Cluster {cluster_info['cluster'].id}: {len(cluster_info['opinions'])} opinions")
                
                elif command == 'citations':
                    opinion_id = int(input("Opinion ID: "))
                    depth = int(input("Depth (1-3): ") or "1")
                    network = self.get_citation_network(opinion_id, depth)
                    print(f"Citation network: {len(network['nodes'])} nodes, {len(network['edges'])} edges")
                
                elif command == 'stats':
                    stats = self.get_stats()
                    print(json.dumps(stats, indent=2, default=str))
                
                else:
                    print("Unknown command. Available: courts, cases, opinions, judges, case-details, citations, stats, quit")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("Goodbye!")


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(description="CourtFinder CLI - CourtListener data processing")
    parser.add_argument('--data-dir', default='data', help='Data directory')
    parser.add_argument('--token', help='CourtListener API token')
    parser.add_argument('--download', nargs='+', help='Download bulk data types')
    parser.add_argument('--import-csv', help='Import CSV file')
    parser.add_argument('--data-type', help='Data type for CSV import')
    parser.add_argument('--limit', type=int, help='Limit number of records')
    parser.add_argument('--search', help='Search query')
    parser.add_argument('--search-type', default='courts', help='Search type')
    parser.add_argument('--interactive', action='store_true', help='Run interactive mode')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = CourtFinderCLI(args.data_dir, args.token)
    
    try:
        if args.download:
            cli.download_bulk_data(args.download)
        
        elif args.import_csv:
            if not args.data_type:
                print("Error: --data-type required for CSV import")
                sys.exit(1)
            
            result = cli.import_csv_data(Path(args.import_csv), args.data_type, args.limit)
            if not result['success']:
                print(f"Import failed: {result['error']}")
                sys.exit(1)
        
        elif args.search:
            if args.search_type == 'courts':
                results = cli.search_courts(args.search)
                for court in results:
                    print(f"{court.id}: {court.full_name} ({court.jurisdiction})")
            elif args.search_type == 'cases':
                results = cli.search_cases(args.search)
                for docket in results:
                    print(f"{docket.id}: {docket.case_name} - {docket.docket_number}")
            elif args.search_type == 'opinions':
                results = cli.search_opinions(args.search)
                for opinion in results:
                    print(f"{opinion.id}: {opinion.type.value} (cluster: {opinion.cluster_id})")
            elif args.search_type == 'judges':
                results = cli.search_judges(args.search)
                for person in results:
                    print(f"{person.id}: {person.get_full_name()}")
        
        elif args.stats:
            stats = cli.get_stats()
            print(json.dumps(stats, indent=2, default=str))
        
        elif args.interactive:
            cli.run_interactive_search()
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()