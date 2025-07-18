#!/usr/bin/env python3
"""
Download CourtListener bulk data files manually
Run this script to download real bz2 files from CourtListener S3 bucket
"""

import subprocess
import os
import sys
import argparse
from pathlib import Path

def download_file(url, filename):
    """Download a file using curl"""
    print(f"Downloading {filename}...")
    print(f"URL: {url}")
    
    # Create downloads directory if it doesn't exist
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    output_path = downloads_dir / filename
    
    # Use curl to download
    cmd = [
        "curl", "-L", url, 
        "-o", str(output_path),
        "--progress-bar",
        "--continue-at", "-"  # Resume if interrupted
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"✅ Downloaded: {filename} ({size:,} bytes)")
            return True
        else:
            print(f"❌ Failed: {filename}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Download CourtListener bulk data files')
    parser.add_argument('--complete', action='store_true', 
                       help='Download complete dataset (~300GB) instead of essential files (~5.5GB)')
    args = parser.parse_args()
    
    print("🏛️  CourtListener Bulk Data Downloader")
    print("=" * 50)
    
    base_url = "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data"
    date = "2024-12-31"  # Latest available date
    
    if args.complete:
        print("📥 COMPLETE DATASET MODE: Downloading ALL FreeLaw bulk data (~300GB)")
        print("⚠️  This will download hundreds of files and may take many hours")
        print()
        
        # Complete dataset includes all available files
        files = [
            # Essential files (always included)
            (f"courts-{date}.csv.bz2", "Court metadata (~79KB)"),
            (f"people-{date}.csv.bz2", "Judge information (~1-5MB)"),
            (f"opinion-clusters-{date}.csv.bz2", "Opinion metadata (~100-500MB)"),
            (f"opinions-{date}.csv.bz2", "Full opinion text (~1-2GB)"),
            (f"citations-{date}.csv.bz2", "Citation data (~1-2GB)"),
            (f"dockets-{date}.csv.bz2", "Case dockets (~4GB)"),
            
            # Additional comprehensive data files
            (f"audio-{date}.csv.bz2", "Audio files metadata (~10-50MB)"),
            (f"judges-{date}.csv.bz2", "Judge detailed information (~50-100MB)"),
            (f"positions-{date}.csv.bz2", "Judge positions (~20-50MB)"),
            (f"schools-{date}.csv.bz2", "School information (~1-5MB)"),
            (f"political-affiliations-{date}.csv.bz2", "Political data (~1-10MB)"),
            (f"aba-ratings-{date}.csv.bz2", "ABA ratings (~1-5MB)"),
            (f"education-{date}.csv.bz2", "Education data (~1-10MB)"),
            (f"financial-disclosures-{date}.csv.bz2", "Financial disclosures (~50-200MB)"),
            (f"investments-{date}.csv.bz2", "Investment data (~20-100MB)"),
            (f"non-investment-income-{date}.csv.bz2", "Non-investment income (~10-50MB)"),
            (f"positions-{date}.csv.bz2", "Position data (~10-50MB)"),
            (f"gifts-{date}.csv.bz2", "Gift data (~5-20MB)"),
            (f"reimbursements-{date}.csv.bz2", "Reimbursement data (~5-20MB)"),
            (f"debts-{date}.csv.bz2", "Debt data (~5-20MB)"),
            (f"sources-{date}.csv.bz2", "Source data (~5-20MB)"),
            (f"recap-documents-{date}.csv.bz2", "RECAP documents (~50-200GB)"),
            (f"docket-entries-{date}.csv.bz2", "Docket entries (~20-50GB)"),
            (f"parties-{date}.csv.bz2", "Party data (~10-30GB)"),
            (f"attorneys-{date}.csv.bz2", "Attorney data (~5-20GB)"),
            (f"attorney-organizations-{date}.csv.bz2", "Attorney organizations (~1-5GB)"),
            (f"originating-court-information-{date}.csv.bz2", "Originating court info (~1-5GB)"),
            (f"bankruptcy-information-{date}.csv.bz2", "Bankruptcy info (~1-5GB)"),
            (f"criminal-complaints-{date}.csv.bz2", "Criminal complaints (~1-5GB)"),
            (f"criminal-counts-{date}.csv.bz2", "Criminal counts (~1-5GB)"),
            (f"tags-{date}.csv.bz2", "Tag data (~1-5GB)"),
        ]
        
    else:
        print("📥 ESSENTIAL FILES MODE: Downloading core dataset (~5.5GB)")
        print("💡 Use --complete flag for full 300GB dataset")
        print()
        
        # Essential files only
        files = [
            (f"courts-{date}.csv.bz2", "Court metadata (~79KB)"),
            (f"people-{date}.csv.bz2", "Judge information (~1-5MB)"),
            (f"opinion-clusters-{date}.csv.bz2", "Opinion metadata (~100-500MB)"),
            (f"opinions-{date}.csv.bz2", "Full opinion text (~1-2GB)"),
            (f"citations-{date}.csv.bz2", "Citation data (~1-2GB)"),
            (f"dockets-{date}.csv.bz2", "Case dockets (~4GB)"),
        ]
    
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    print("Checking existing files and downloading missing ones...")
    print()
    
    successful = 0
    failed = 0
    skipped = 0
    
    for filename, description in files:
        file_path = downloads_dir / filename
        
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"⏭️  SKIP: {filename} - already exists ({size:,} bytes)")
            skipped += 1
            continue
        
        print(f"📥 DOWNLOADING: {description}")
        url = f"{base_url}/{filename}"
        if download_file(url, filename):
            successful += 1
        else:
            failed += 1
        print()
    
    print(f"\nDownload Summary:")
    print(f"✅ Downloaded: {successful}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"❌ Failed: {failed}")
    
    # Show what we have
    print(f"\nAll files in downloads/ directory:")
    total_size = 0
    for file in sorted(downloads_dir.glob("*.bz2")):
        size = file.stat().st_size
        total_size += size
        print(f"  📄 {file.name} ({size:,} bytes)")
    
    print(f"\nTotal downloaded: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")

if __name__ == "__main__":
    main()