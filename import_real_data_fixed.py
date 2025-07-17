#!/usr/bin/env python3
"""
Fixed import script for real FreeLaw bulk data
Properly handles bz2 files and imports all data types efficiently
"""

import sys
import csv
import bz2
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.main import CourtFinderCLI
from courtfinder.models import Court, Docket, OpinionCluster, Opinion, Citation, Person
from courtfinder.csv_parser import BulkCSVParser, CourtCSVParser, DocketCSVParser, OpinionClusterCSVParser

def import_bz2_data(cli: CourtFinderCLI, file_path: Path, data_type: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Import data directly from bz2 file using the CSV parser
    
    Args:
        cli: CourtFinderCLI instance
        file_path: Path to .bz2 file
        data_type: Type of data (courts, dockets, opinion_clusters)
        limit: Maximum number of records to import
        
    Returns:
        Import statistics
    """
    print(f"📦 Processing {file_path.name} ({data_type})...")
    
    if not file_path.exists():
        return {'success': False, 'error': f'File not found: {file_path}'}
    
    # Create temporary uncompressed file for the parser
    import tempfile
    import shutil
    
    imported_count = 0
    error_count = 0
    
    try:
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            # Decompress bz2 to temporary CSV file
            with bz2.open(file_path, 'rt', encoding='utf-8') as bz2_file:
                shutil.copyfileobj(bz2_file, temp_file)
        
        # Use the BulkCSVParser to parse the temporary file
        parser = BulkCSVParser()
        
        # Parse objects using the proper parse_file method
        for obj in parser.parse_file(temp_path, data_type, limit):
            try:
                # Save to appropriate storage
                if data_type == 'courts':
                    cli.storage.save_court(obj)
                elif data_type == 'dockets':
                    cli.storage.save_docket(obj)
                elif data_type == 'opinion_clusters':
                    cli.storage.save_opinion_cluster(obj)
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    print(f"  📊 Imported {imported_count} {data_type}...")
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Only show first 5 errors
                    print(f"  ❌ Error saving {data_type}: {e}")
                continue
        
        # Clean up temporary file
        temp_path.unlink()
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'imported_count': imported_count,
            'error_count': error_count
        }
    
    print(f"✅ Successfully imported {imported_count} {data_type} ({error_count} errors)")
    return {
        'success': True,
        'imported_count': imported_count,
        'error_count': error_count
    }

def main():
    print("🏛️  FREELAW BULK DATA IMPORTER (FIXED)")
    print("=" * 60)
    print("Processing bz2 files directly with efficient import")
    print("=" * 60)
    
    # Setup directories
    downloads_dir = Path("downloads")
    data_dir = Path("real_data")
    
    if not downloads_dir.exists():
        print("❌ No downloads/ directory found")
        print("Please run download_bulk_data.py first")
        return
    
    # Initialize CLI with real data directory
    print(f"🔧 Initializing CourtFinder with real_data directory...")
    cli = CourtFinderCLI(str(data_dir))
    
    # Files to import with limits
    import_files = [
        ("courts-2024-12-31.csv.bz2", "courts", 1000),
        ("dockets-2024-12-31.csv.bz2", "dockets", 1000),
        ("opinion-clusters-2024-12-31.csv.bz2", "opinion_clusters", 500),
    ]
    
    print(f"\n🚀 Starting import process...")
    
    total_imported = 0
    total_errors = 0
    
    for filename, data_type, limit in import_files:
        file_path = downloads_dir / filename
        
        if not file_path.exists():
            print(f"⏭️  Skipping {filename} - file not found")
            continue
        
        print(f"\n📥 IMPORTING {data_type.upper()}")
        print("-" * 40)
        
        result = import_bz2_data(cli, file_path, data_type, limit)
        
        if result['success']:
            total_imported += result['imported_count']
            total_errors += result['error_count']
        else:
            print(f"❌ Failed to import {data_type}: {result['error']}")
    
    # Show final stats
    print(f"\n📊 FINAL STATISTICS")
    print("=" * 60)
    
    stats = cli.get_stats()
    for data_type, stat in stats['storage_stats'].items():
        if isinstance(stat, dict) and 'total_items' in stat:
            print(f"  {data_type}: {stat['total_items']} items")
    
    print(f"\n✅ Import complete!")
    print(f"📈 Total imported: {total_imported} records")
    print(f"⚠️  Total errors: {total_errors} records")
    print(f"📁 Data stored in: {data_dir}")
    
    # Test searches
    print(f"\n🔍 TESTING SEARCH WITH REAL DATA")
    print("-" * 40)
    
    # Test court search
    court_results = cli.search_courts("Supreme", limit=5)
    print(f"Court search 'Supreme': {len(court_results)} results")
    
    # Test case search
    case_results = cli.search_cases("United States", limit=5)
    print(f"Case search 'United States': {len(case_results)} results")
    
    # Test case search for specific case
    dickson_results = cli.search_cases("Dickson", limit=5)
    print(f"Case search 'Dickson': {len(dickson_results)} results")
    
    if len(case_results) > 0:
        print("🎉 SUCCESS! Found cases in real data!")
        for result in case_results[:3]:
            if hasattr(result, 'case_name'):
                print(f"  📋 {result.case_name}")
    
    print(f"\n🎯 READY TO USE!")
    print(f"Your CourtFinder now has comprehensive real data loaded!")

if __name__ == "__main__":
    main()