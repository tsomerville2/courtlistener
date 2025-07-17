#!/usr/bin/env python3
"""
Import real FreeLaw bulk data from downloads/ into the system
This replaces fake test_data with actual court data
"""

import sys
import csv
import bz2
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from courtfinder.main import CourtFinderCLI

def decompress_and_parse_csv(file_path, limit=None):
    """
    Decompress bz2 file and parse CSV, returning rows as dictionaries
    """
    print(f"📦 Decompressing {file_path.name}...")
    
    rows = []
    with bz2.open(file_path, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if limit and i >= limit:
                break
            
            # Clean up the row - remove backticks that CourtListener uses
            cleaned_row = {}
            for key, value in row.items():
                # Remove backticks from values
                if isinstance(value, str) and value.startswith('`') and value.endswith('`'):
                    cleaned_value = value[1:-1]  # Remove first and last backtick
                else:
                    cleaned_value = value
                
                cleaned_row[key] = cleaned_value
            
            rows.append(cleaned_row)
    
    print(f"✅ Extracted {len(rows)} records from {file_path.name}")
    return rows

def import_courts_data(cli, downloads_dir, limit=1000):
    """Import courts data from bulk file"""
    courts_file = downloads_dir / "courts-2024-12-31.csv.bz2"
    
    if not courts_file.exists():
        print(f"❌ Courts file not found: {courts_file}")
        return False
    
    print(f"🏛️  IMPORTING COURTS DATA (limit: {limit})")
    print("-" * 50)
    
    try:
        # Decompress and parse
        rows = decompress_and_parse_csv(courts_file, limit)
        
        # Import using CLI
        success_count = 0
        for i, row in enumerate(rows, 1):
            try:
                # Create a temporary CSV file for this batch
                temp_csv = downloads_dir / f"temp_courts_{i}.csv"
                
                # Write single row to CSV
                with open(temp_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=row.keys())
                    writer.writeheader()
                    writer.writerow(row)
                
                # Import the single row
                result = cli.import_csv_data(temp_csv, "courts", limit=1)
                
                if result.get('success', False):
                    success_count += 1
                    if success_count % 100 == 0:
                        print(f"  📊 Imported {success_count} courts so far...")
                
                # Clean up temp file
                temp_csv.unlink()
                
            except Exception as e:
                print(f"  ❌ Error importing row {i}: {e}")
                continue
        
        print(f"✅ Successfully imported {success_count} courts")
        return True
        
    except Exception as e:
        print(f"❌ Error importing courts: {e}")
        return False

def import_dockets_data(cli, downloads_dir, limit=1000):
    """Import dockets (cases) data from bulk file"""
    dockets_file = downloads_dir / "dockets-2024-12-31.csv.bz2"
    
    if not dockets_file.exists():
        print(f"❌ Dockets file not found: {dockets_file}")
        return False
    
    print(f"⚖️  IMPORTING DOCKETS DATA (limit: {limit})")
    print("-" * 50)
    
    try:
        # Decompress and parse
        rows = decompress_and_parse_csv(dockets_file, limit)
        
        # Import using CLI
        success_count = 0
        for i, row in enumerate(rows, 1):
            try:
                # Create a temporary CSV file for this batch
                temp_csv = downloads_dir / f"temp_dockets_{i}.csv"
                
                # Write single row to CSV
                with open(temp_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=row.keys())
                    writer.writeheader()
                    writer.writerow(row)
                
                # Import the single row
                result = cli.import_csv_data(temp_csv, "dockets", limit=1)
                
                if result.get('success', False):
                    success_count += 1
                    if success_count % 100 == 0:
                        print(f"  📊 Imported {success_count} dockets so far...")
                
                # Clean up temp file
                temp_csv.unlink()
                
            except Exception as e:
                print(f"  ❌ Error importing row {i}: {e}")
                continue
        
        print(f"✅ Successfully imported {success_count} dockets")
        return True
        
    except Exception as e:
        print(f"❌ Error importing dockets: {e}")
        return False

def import_opinion_clusters_data(cli, downloads_dir, limit=500):
    """Import opinion clusters data from bulk file"""
    clusters_file = downloads_dir / "opinion-clusters-2024-12-31.csv.bz2"
    
    if not clusters_file.exists():
        print(f"❌ Opinion clusters file not found: {clusters_file}")
        return False
    
    print(f"📝 IMPORTING OPINION CLUSTERS DATA (limit: {limit})")
    print("-" * 50)
    
    try:
        # Decompress and parse
        rows = decompress_and_parse_csv(clusters_file, limit)
        
        # Import using CLI
        success_count = 0
        for i, row in enumerate(rows, 1):
            try:
                # Create a temporary CSV file for this batch
                temp_csv = downloads_dir / f"temp_clusters_{i}.csv"
                
                # Write single row to CSV
                with open(temp_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=row.keys())
                    writer.writeheader()
                    writer.writerow(row)
                
                # Import the single row
                result = cli.import_csv_data(temp_csv, "opinion_clusters", limit=1)
                
                if result.get('success', False):
                    success_count += 1
                    if success_count % 50 == 0:
                        print(f"  📊 Imported {success_count} opinion clusters so far...")
                
                # Clean up temp file
                temp_csv.unlink()
                
            except Exception as e:
                print(f"  ❌ Error importing row {i}: {e}")
                continue
        
        print(f"✅ Successfully imported {success_count} opinion clusters")
        return True
        
    except Exception as e:
        print(f"❌ Error importing opinion clusters: {e}")
        return False

def main():
    print("🏛️  FREELAW BULK DATA IMPORTER")
    print("=" * 60)
    print("This will import REAL FreeLaw data from your downloads/")
    print("Replacing fake test_data with actual court records")
    print("=" * 60)
    
    # Setup directories
    downloads_dir = Path("downloads")
    data_dir = Path("real_data")  # Use new directory for real data
    
    if not downloads_dir.exists():
        print("❌ No downloads/ directory found")
        print("Please run download_bulk_data.py first")
        return
    
    # Show what bulk files we have
    print("📁 Available bulk data files:")
    for bz2_file in downloads_dir.glob("*.bz2"):
        size = bz2_file.stat().st_size
        print(f"  📄 {bz2_file.name} ({size:,} bytes)")
    
    # Initialize CLI with real data directory
    print(f"\n🔧 Initializing CourtFinder with real_data directory...")
    cli = CourtFinderCLI(str(data_dir))
    
    # Import data with reasonable limits
    print("\n🚀 Starting import process...")
    
    # Import courts (small file, import more)
    import_courts_data(cli, downloads_dir, limit=1000)
    
    # Import dockets/cases (large file, import fewer)
    import_dockets_data(cli, downloads_dir, limit=1000)
    
    # Import opinion clusters (huge file, import even fewer)
    import_opinion_clusters_data(cli, downloads_dir, limit=500)
    
    # Show final stats
    print("\n📊 FINAL STATISTICS")
    print("=" * 60)
    
    stats = cli.get_stats()
    for data_type, stat in stats['storage_stats'].items():
        if isinstance(stat, dict) and 'total_items' in stat:
            print(f"  {data_type}: {stat['total_items']} items")
    
    print(f"\n✅ Import complete! Real data is now in: {data_dir}")
    print(f"💡 To use this data, run: python menu.py")
    print(f"   And update your CLI to use 'real_data' directory")
    
    # Test a search
    print(f"\n🔍 TESTING SEARCH WITH REAL DATA")
    print("-" * 40)
    
    # Test court search
    court_results = cli.search_courts("Supreme", limit=5)
    print(f"Court search 'Supreme': {len(court_results)} results")
    
    # Test case search
    case_results = cli.search_cases("United States", limit=5)
    print(f"Case search 'United States': {len(case_results)} results")
    
    # Test case search for Dickson
    dickson_results = cli.search_cases("Dickson", limit=5)
    print(f"Case search 'Dickson': {len(dickson_results)} results")
    
    if len(dickson_results) > 0:
        print("🎉 SUCCESS! Found Dickson cases in real data!")
        for result in dickson_results:
            if hasattr(result, 'case_name'):
                print(f"  📋 {result.case_name}")
    
    print(f"\n🎯 READY TO USE!")
    print(f"Your CourtFinder now has REAL FreeLaw data loaded!")

if __name__ == "__main__":
    main()